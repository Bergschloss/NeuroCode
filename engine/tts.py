import re
import numpy as np
import edge_tts
import miniaudio

TARGET_SR = 44100

VOICES = {
    "uk": ["uk-UA-PolinaNeural", "uk-UA-OstapNeural"],
    "ru": ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"],
    "en": ["en-US-AriaNeural", "en-US-GuyNeural"],
}


def detect_lang(text: str) -> str:
    """Reliable heuristic: UA/RU/EN by character sets."""
    lo = text.lower()
    latin    = sum(1 for c in lo if c.isalpha() and c.isascii())
    cyrillic = sum(1 for c in lo if '\u0400' <= c <= '\u04FF')

    if latin > cyrillic and latin > 0:
        return 'en'

    uk_markers = sum(1 for c in lo if c in 'їієґ')
    ru_markers = sum(1 for c in lo if c in 'ыъэё')

    if uk_markers > ru_markers:
        return 'uk'
    if ru_markers > uk_markers:
        return 'ru'

    # If ambiguous (both 0 or equal), check for 'и' (RU 'i') vs 'і' (UK 'i')
    # If text has 'и' but no 'і', it's highly likely Russian in this context.
    if 'и' in lo and 'і' not in lo:
        return 'ru'
    if 'і' in lo and 'и' not in lo:
        return 'uk'

    # Default to 'ru' if still zero/ambiguous
    return 'ru'


def split_segments(text: str) -> list[tuple[str, str]]:
    """Return list of (lang, text) merged by consecutive same-language runs."""
    parts = re.split(r'(?<=[.!?\n])\s+|\n+', text.strip())
    parts = [p.strip() for p in parts if p.strip()]

    raw = [(detect_lang(p), p) for p in parts]

    # merge consecutive same-lang
    merged: list[list] = []
    for lang, txt in raw:
        if merged and merged[-1][0] == lang:
            merged[-1][1] += ' ' + txt
        else:
            merged.append([lang, txt])

    return [(lang, txt) for lang, txt in merged]


async def _tts_to_array(text: str, voice: str) -> np.ndarray:
    print(f"[TTS DEBUG] Starting _tts_to_array for voice={voice}, text length={len(text)}...")
    try:
        communicate = edge_tts.Communicate(text, voice)
        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        print(f"[TTS DEBUG] Finished edge_tts stream, chunks received: {len(chunks)}")
        mp3_bytes = b"".join(chunks)
        decoded = miniaudio.decode(
            mp3_bytes,
            output_format=miniaudio.SampleFormat.FLOAT32,
            nchannels=1,
            sample_rate=TARGET_SR,
        )
        print(f"[TTS DEBUG] Miniaudio decoded.")
        return np.frombuffer(decoded.samples, dtype=np.float32).copy()
    except Exception as e:
        print(f"[TTS ERROR] Exception in _tts_to_array: {e}")
        raise e


async def generate_tts_single(
    text: str,
    voices: dict,
    lang_override: str = "auto",
) -> tuple[np.ndarray, int]:
    """
    Single-voice TTS for the whole text.
    lang_override: 'auto' | 'uk' | 'ru' | 'en'
    'auto' — detect from text content.
    """
    if lang_override == "auto":
        lang = detect_lang(text)
    else:
        lang = lang_override
    voice = voices.get(lang, voices["ru"])
    audio = await _tts_to_array(text, voice)
    return audio, TARGET_SR


async def generate_tts_multilang(
    text: str,
    voices: dict,
    lang_override: str = "auto",
) -> tuple[np.ndarray, int]:
    """
    Multi-language TTS for block 2.
    lang_override: 'auto' | 'uk' | 'ru' | 'en'
    'auto' — per-sentence detection.
    Fixed lang — use that voice for the whole text.
    """
    if lang_override != "auto":
        # Force a single language/voice for the entire text
        voice = voices.get(lang_override, voices["ru"])
        audio = await _tts_to_array(text, voice)
        return audio, TARGET_SR

    # auto — per-segment detection
    segments = split_segments(text)
    arrays = []
    for lang, seg_text in segments:
        voice = voices.get(lang, voices.get('en', 'en-US-AriaNeural'))
        audio = await _tts_to_array(seg_text, voice)
        arrays.append(audio)

    combined = np.concatenate(arrays) if arrays else np.zeros(TARGET_SR, dtype=np.float32)
    return combined, TARGET_SR
