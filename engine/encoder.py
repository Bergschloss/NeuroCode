import gc
import os
from pathlib import Path
import numpy as np
import soundfile as sf
import miniaudio
from typing import Callable
from scipy.signal import butter, iirnotch, lfilter, sosfilt, sosfiltfilt

# ─── Music library directory ──────────────────────────────────────────────────
MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")


def get_music_tracks() -> list[dict]:
    """
    Scan MUSIC_DIR for all .mp3 and .wav files and return a list of
    {"id": "stem_name", "label": "Human readable name", "filename": "file.mp3"}
    sorted alphabetically by label.
    """
    if not os.path.isdir(MUSIC_DIR):
        return []
    tracks = []
    for fname in sorted(os.listdir(MUSIC_DIR)):
        if fname.lower().endswith((".mp3", ".wav")):
            stem = os.path.splitext(fname)[0]
            # Convert underscores/dashes to spaces, title-case
            label = stem.replace("_", " ").replace("-", " ").title()
            tracks.append({"id": stem, "label": label, "filename": fname})
    return tracks

# ─── Memory-safe chunked time-stretch ────────────────────────────────────────

CHUNK_SEC = 300   # max seconds per STFT call (~210 MB RAM per chunk, avoids clicks for typical lengths)
CHUNK_OVERLAP_SEC = 0.25
VOICE_BAND_LIMIT_HZ = 3500.0
CARRIER_MIN_HZ = 3000.0
CARRIER_MAX_HZ = 17500.0
OUTPUT_CEILING = 10 ** (-1.0 / 20.0)


def _trim_silence(audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
    """Remove leading and trailing silence with a robust threshold."""
    mask = np.abs(audio) > threshold
    if not np.any(mask):
        return audio
    start = np.argmax(mask)
    end = len(audio) - np.argmax(mask[::-1])
    # Ensure we don't trim too much, keep a tiny buffer
    start = max(0, start - 100)
    end = min(len(audio), end + 100)
    return audio[start:end]


def _stretch_chunked(audio: np.ndarray, rate: float, sr: int) -> np.ndarray:
    """Memory-safe time stretch with overlap/crossfade at chunk boundaries."""
    import librosa
    chunk = CHUNK_SEC * sr
    if len(audio) <= chunk:
        return librosa.effects.time_stretch(audio, rate=rate)
    overlap = max(1, int(CHUNK_OVERLAP_SEC * sr))
    pieces = []
    for start in range(0, len(audio), chunk - overlap):
        end = min(start + chunk, len(audio))
        stretched = librosa.effects.time_stretch(audio[start:end], rate=rate)
        if not pieces:
            pieces.append(stretched)
        else:
            crossfade = min(
                max(1, int(overlap / rate)),
                len(pieces[-1]),
                len(stretched),
            )
            fade_out = np.linspace(1.0, 0.0, crossfade, dtype=np.float32)
            fade_in = 1.0 - fade_out
            pieces[-1][-crossfade:] = (
                pieces[-1][-crossfade:] * fade_out
                + stretched[:crossfade] * fade_in
            )
            pieces.append(stretched[crossfade:])
        if end == len(audio):
            break
    return np.concatenate(pieces)


def _bandlimit_voice(audio: np.ndarray, sr: int) -> np.ndarray:
    """Return raw voice signal without artificially chopping high vocal formants."""
    return audio.astype(np.float32, copy=False)


# ─── Single-stream (plain TTS, conscious hearing) ────────────────────────────

def encode_single_stream(audio: np.ndarray, speed: float = 1.0,
                         sr: int = 44100) -> np.ndarray:
    """
    Time-stretch and return stereo by duplicating the mono channel.
    """
    audio = audio.astype(np.float32)
    audio = _trim_silence(audio)
    
    if speed != 1.0:
        audio = _stretch_chunked(audio, rate=float(speed), sr=sr)
    
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio /= peak

    # Create identical Left/Right stereo channels
    return np.column_stack((audio, audio))


# ─── Multi-layer AM (subliminal encoding) ────────────────────────────────────

def encode_multilayer(
    audio: np.ndarray,
    sr: int,
    n_layers: int,
    speed_min: float,
    speed_max: float,
    progress_cb: Callable[[int], None] = None,
    p_start: int = 40,
    p_end: int = 90,
    log_cb: Callable[[str], None] = None,
    cancel_cb: Callable[[], None] | None = None,
) -> np.ndarray:
    """
    Band-limited AM modulation with deterministic variation and stereo symmetry.
    """
    # 1. Prepare source
    audio = _trim_silence(audio.astype(np.float32), threshold=0.01)
    audio = _bandlimit_voice(audio, sr)
    target_samples = len(audio)
    if target_samples == 0:
        raise ValueError("Cannot encode empty audio")
    rng = np.random.default_rng()
    
    # Pre-calculate active indices to ensure "Instant Entry"
    # We look for indices where the signal is non-negligible
    active_mask = np.abs(audio) > 0.02
    active_indices = np.where(active_mask)[0]
    if len(active_indices) == 0:
        active_indices = np.array([0])
        
    t = np.arange(target_samples, dtype=np.float64) / sr
    output = np.zeros((target_samples, 2), dtype=np.float32)

    # 2. Build layers configuration
    layers_config = []
    # Standard mode: symmetrical stereo grid
    n_left = n_layers // 2
    n_right = n_layers - n_left
    
    if n_left > 1:
        left_freqs = np.linspace(CARRIER_MIN_HZ, CARRIER_MAX_HZ, n_left)
        left_freqs += rng.uniform(-150.0, 150.0, n_left)
        left_speeds = np.linspace(speed_min, speed_max, n_left)
        left_speeds += rng.uniform(-0.05, 0.05, n_left)
    else:
        left_freqs = np.array([CARRIER_MIN_HZ])
        left_speeds = np.array([speed_min])
        
    if n_right > 1:
        right_freqs = np.linspace(CARRIER_MIN_HZ, CARRIER_MAX_HZ, n_right)
        right_freqs += rng.uniform(-150.0, 150.0, n_right)
        right_speeds = np.linspace(speed_min, speed_max, n_right)
        right_speeds += rng.uniform(-0.05, 0.05, n_right)
    else:
        right_freqs = np.array([CARRIER_MIN_HZ])
        right_speeds = np.array([speed_min])
        
    # Ensure speeds do not drop below 1.0
    left_speeds = np.clip(left_speeds, 1.0, 20.0)
    right_speeds = np.clip(right_speeds, 1.0, 20.0)
        
    # Add Left channel layers (even panning)
    for j in range(n_left):
        layers_config.append({
            'channel': 0,
            'freq': left_freqs[j],
            'speed': left_speeds[j],
            'offset_zero': (j == 0) # Instant entry on Left Layer 0
        })
    # Add Right channel layers (odd panning)
    for j in range(n_right):
        layers_config.append({
            'channel': 1,
            'freq': right_freqs[j],
            'speed': right_speeds[j],
            'offset_zero': False # All Right layers start randomly to prevent phantom mono center
        })
        
    if log_cb:
        log_cb(
            f"Processing: {n_left} layers Left, {n_right} layers Right "
            f"(range {CARRIER_MIN_HZ:.0f} - {CARRIER_MAX_HZ:.0f} Hz)"
        )

    # 3. Process each layer
    total_layers = len(layers_config)
    for idx, cfg in enumerate(layers_config):
        if cancel_cb:
            cancel_cb()
        cf = cfg['freq']
        sf_rate = cfg['speed']
        ch = cfg['channel']
        offset_zero = cfg['offset_zero']
        
        # A. Stretch
        stretched = _stretch_chunked(audio, rate=float(sf_rate), sr=sr)
        n_stretched = len(stretched)
        
        # B. Start offset (first left layer starts immediately).
        if offset_zero:
            off = 0
        else:
            valid_starts = (active_indices / float(sf_rate)).astype(int)
            valid_starts = valid_starts[valid_starts < n_stretched]
            if len(valid_starts) == 0:
                valid_starts = np.array([0])
            off = int(rng.choice(valid_starts))
        
        # C. Repeat only to the required length without a large over-allocated tile.
        source = (
            np.concatenate((stretched[off:], stretched[:off]))
            if off
            else stretched
        )
        chunk = np.resize(source, target_samples).astype(np.float32, copy=False)
        
        phase = rng.uniform(0, 2 * np.pi)
        carrier = np.cos(2.0 * np.pi * cf * t + phase).astype(np.float32)
        
        layer_signal = chunk * carrier
        
        # Individual peak normalization
        pk = np.max(np.abs(layer_signal))
        if pk > 0:
            layer_signal /= pk
        
        # E. Add to corresponding channel
        output[:, ch] += layer_signal
        
        del stretched, source, chunk, carrier, layer_signal
        gc.collect()

        if progress_cb:
            progress_cb(int(p_start + (p_end - p_start) * (idx + 1) / total_layers))

    # Final normalization
    peak = np.max(np.abs(output))
    if peak > 0:
        output /= peak
    return output



def _apply_notch_filters(signal: np.ndarray, freqs_per_channel: list, sr: int, Q: float = 30.0) -> np.ndarray:
    """
    Apply a surgical IIR notch filter at each frequency in freqs_per_channel[ch] for each channel.
    
    freqs_per_channel: list of two lists, e.g. [[136.1], [140.1]]
    Q: Quality factor — higher Q = narrower notch. 30 is very surgical (~4-5 Hz wide at 136 Hz).
    """
    result = signal.copy()
    nyq = 0.5 * sr
    for ch in range(min(2, signal.shape[1])):
        for freq in freqs_per_channel[ch]:
            if 0 < freq < nyq:
                w0 = freq / nyq
                b_n, a_n = iirnotch(w0, Q)
                result[:, ch] = lfilter(b_n, a_n, result[:, ch]).astype(np.float32)
    return result


def _get_music_audio(
    music_type: str,
    length_samples: int,
    sr: int,
    notch_freqs: list | None = None,
    notch_Q: float = 30.0,
) -> np.ndarray:
    """
    Load, loop, low-pass filter (high cut @ 3kHz), optionally notch-filter, and normalize the selected music track.
    
    notch_freqs: if provided, a list of two lists [[left_freqs], [right_freqs]] specifying
                 the exact carrier frequencies to surgically remove from each channel.
    notch_Q:     Quality factor for the notch — 30 gives a very narrow (~5 Hz) notch.
    """
    if music_type == "none":
        return np.zeros((length_samples, 2), dtype=np.float32)

    # Look up the filename from MUSIC_DIR by stem name (music_type == file stem)
    file_path = None
    for ext in (".mp3", ".wav"):
        candidate = os.path.join(MUSIC_DIR, music_type + ext)
        if os.path.exists(candidate):
            file_path = candidate
            break
    if file_path is None:
        print(f"[WARN] Music track not found: {music_type} in {MUSIC_DIR}")
        return np.zeros((length_samples, 2), dtype=np.float32)
    try:
        with open(file_path, "rb") as f:
            mp3_bytes = f.read()
        decoded = miniaudio.decode(
            mp3_bytes,
            output_format=miniaudio.SampleFormat.FLOAT32,
            nchannels=2,
            sample_rate=sr
        )
        music_data = np.frombuffer(decoded.samples, dtype=np.float32).reshape(-1, 2)
        
        # Loop music_data to match length_samples
        n_frames = len(music_data)
        if n_frames == 0:
            return np.zeros((length_samples, 2), dtype=np.float32)
        music_signal = np.resize(music_data, (length_samples, 2)).astype(
            np.float32,
            copy=False,
        )
        
        # Apply 3000 Hz low-pass filter (high cut) to protect the voice spectrum
        cutoff = 3000.0
        nyq = 0.5 * sr
        normal_cutoff = cutoff / nyq
        b_lp, a_lp = butter(4, normal_cutoff, btype='low', analog=False)
        music_signal = lfilter(b_lp, a_lp, music_signal, axis=0).astype(np.float32)
        
        # Optional surgical notch filter at binaural carrier frequencies
        if notch_freqs is not None:
            music_signal = _apply_notch_filters(music_signal, notch_freqs, sr, Q=notch_Q)
            print(f"[DSP] Notch filter applied: L={notch_freqs[0]} Hz, R={notch_freqs[1]} Hz, Q={notch_Q}")
        
        # Automatic RMS normalization to ensure all music tracks have identical perceived loudness
        rms = np.sqrt(np.mean(music_signal**2))
        if rms > 0:
            target_rms = 0.15
            music_signal = music_signal * (target_rms / rms)
        
        # Prevent clipping by peak-limiting to 1.0 if the scaled signal exceeds 1.0
        peak = np.max(np.abs(music_signal))
        if peak > 1.0:
            music_signal /= peak
            
        return music_signal
    except Exception as e:
        print(f"[ERROR] Failed to load or process music track {music_type}: {e}")
        return np.zeros((length_samples, 2), dtype=np.float32)


# Map binaural type → (f_left, f_right) carrier frequencies
BINAURAL_FREQS = {
    "delta": (136.1, 136.1 + 2.0),   # 2 Hz beat
    "theta": (136.1, 136.1 + 4.0),   # 4 Hz beat
    "alpha": (136.1, 136.1 + 10.0),  # 10 Hz beat
    "beta":  (136.1, 136.1 + 15.0),  # 15 Hz beat
}


def get_binaural_freqs(beat_type: str) -> tuple[float, float] | None:
    """Return (f_left, f_right) carrier Hz for a given binaural type, or None if 'none'."""
    return BINAURAL_FREQS.get(beat_type, None)


def generate_binaural_beat(beat_type: str, length_samples: int, sr: int, volume_db: float) -> np.ndarray:
    if beat_type == "none":
        return np.zeros((length_samples, 2), dtype=np.float32)
    
    linear_vol = 10 ** (volume_db / 20.0)
    t = np.arange(length_samples, dtype=np.float64) / sr

    if beat_type == "turbo_manipura":
        # Correct Frequency Modulation (FM) phase integration to prevent time-growing frequency drift distortion.
        # We use a single, shared LFO (0.05 Hz) to keep all three carrier layers in perfect harmonic sync.
        # Phase(t) = 2*pi * f0 * t - (modulation_depth / f_lfo) * cos(2*pi * f_lfo * t)
        phase_lfo = - (1.5 / 0.05) * np.cos(2.0 * np.pi * 0.05 * t)
        
        # 1. Low Layer (Sun): 126.22 Hz + 3 Hz Delta
        left1 = np.sin(2.0 * np.pi * 126.22 * t + phase_lfo)
        right1 = np.sin(2.0 * np.pi * 129.22 * t + phase_lfo)
        
        # 2. Mid Layer (Detox/Chakra): 330.0 Hz + 6 Hz Theta
        left2 = np.sin(2.0 * np.pi * 330.0 * t + phase_lfo)
        right2 = np.sin(2.0 * np.pi * 336.0 * t + phase_lfo)
        
        # 3. High Layer (Solfeggio): 528.0 Hz + 10 Hz Alpha
        left3 = np.sin(2.0 * np.pi * 528.0 * t + phase_lfo)
        right3 = np.sin(2.0 * np.pi * 538.0 * t + phase_lfo)
        
        # Combine the 3 layers (grounding bass, medium core, high Solfeggio)
        # Mix weights: Low layer 1.0, Mid layer 0.6, High layer 0.4
        left_combined = left1 + 0.6 * left2 + 0.4 * left3
        right_combined = right1 + 0.6 * right2 + 0.4 * right3
        
        # 4. Isochronic Amplitude Modulation (3 Hz raised cosine envelope)
        envelope = 0.5 * (1.0 + np.cos(2.0 * np.pi * 3.0 * t))
        left_modulated = left_combined * envelope
        right_modulated = right_combined * envelope
        
        beat = np.column_stack((left_modulated, right_modulated))
        # Peak normalize the combined beat signal to prevent digital clipping
        peak = np.max(np.abs(beat))
        if peak > 0:
            beat /= peak
            
        return (beat * linear_vol).astype(np.float32)

    freqs = get_binaural_freqs(beat_type)
    if freqs is None:
        return np.zeros((length_samples, 2), dtype=np.float32)
    f_left, f_right = freqs
    
    left_signal = np.sin(2.0 * np.pi * f_left * t)
    right_signal = np.sin(2.0 * np.pi * f_right * t)
    
    beat = np.column_stack((left_signal, right_signal)) * linear_vol
    return beat.astype(np.float32)


def _apply_tpdf_dither(audio: np.ndarray) -> np.ndarray:
    """
    Apply Triangular Probability Density Function (TPDF) dither to 32-bit float audio array.
    Eliminates quantization distortion down to -96 dB.
    """
    scale = 32768.0
    rng = np.random.default_rng()
    tpdf = (
        rng.uniform(-0.5, 0.5, size=audio.shape)
        + rng.uniform(-0.5, 0.5, size=audio.shape)
    ) / scale
    return np.clip(audio + tpdf, -1.0, 1.0)


def _write_audio_file(output_path: str, audio: np.ndarray, sr: int = 44100) -> None:
    """
    Write audio file supporting MP3 (320k Full Stereo, 20k cutoff, TPDF dithered),
    FLAC (Lossless), and WAV.
    """
    import subprocess
    import tempfile
    import uuid

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dithered = _apply_tpdf_dither(audio)
    ext = path.suffix.lower()

    if ext == ".flac":
        sf.write(str(path), dithered, sr, format="FLAC")
    elif ext == ".mp3":
        temp_wav = Path(tempfile.gettempdir()) / f"ncs_temp_{uuid.uuid4().hex[:6]}.wav"
        try:
            sf.write(str(temp_wav), dithered, sr, subtype="PCM_16")
            cmd = [
                "ffmpeg", "-y", "-i", str(temp_wav),
                "-c:a", "libmp3lame",
                "-b:a", "320k",
                "-joint_stereo", "0",
                "-cutoff", "20000",
                str(path)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                sf.write(str(path), dithered, sr, format="MP3")
        except Exception:
            sf.write(str(path), dithered, sr, format="MP3")
        finally:
            if temp_wav.exists():
                temp_wav.unlink(missing_ok=True)
    else:
        sf.write(str(path), dithered, sr, subtype="PCM_16")


def mix_final(
    main_audio: np.ndarray,
    sr: int,
    n_layers: int,
    speed_min: float,
    speed_max: float,
    silence_start: float, # treat as fade in duration
    silence_end: float,   # treat as fade out duration
    output_path: str | None,
    output_raw_path: str | None = None,
    output_flac_path: str | None = None,
    binaural_type: str = "none",
    binaural_volume: float = -12.0,
    music_type: str = "none",
    music_volume: float = -12.0,
    music_notch_enabled: bool = False,
    progress_cb: Callable[[int], None] = None,
    log_cb: Callable[[str], None] = None,
    voice_volume: float = 0.0,
    cancel_cb: Callable[[], None] | None = None,
) -> None:
    """
    Build final audio with TPDF dithered MP3 320k, Lossless FLAC, or WAV output.
    """
    if output_path or output_flac_path:
        if log_cb:
            log_cb("Preparing multi-layer AM encoding...")

        if progress_cb:
            progress_cb(20)

        main_encoded = encode_multilayer(
            main_audio, sr, n_layers, speed_min, speed_max,
            progress_cb=progress_cb, p_start=25, p_end=90,
            log_cb=log_cb,
            cancel_cb=cancel_cb,
        )
        main_encoded *= 10 ** (voice_volume / 20.0)
        final = main_encoded.copy()
        del main_encoded
        gc.collect()

        if binaural_type != "none":
            if cancel_cb:
                cancel_cb()
            if log_cb:
                log_cb(f"Synthesizing binaural beat ({binaural_type})...")
            final += generate_binaural_beat(
                binaural_type, len(final), sr, binaural_volume
            )

        if music_type != "none":
            if cancel_cb:
                cancel_cb()
            if log_cb:
                log_cb(f"Loading and processing background music ({music_type})...")
            notch_freqs = None
            if music_notch_enabled and binaural_type != "none":
                if binaural_type == "turbo_manipura":
                    notch_freqs = [
                        [126.22, 330.0, 528.0],
                        [129.22, 336.0, 538.0],
                    ]
                else:
                    freqs = get_binaural_freqs(binaural_type)
                    if freqs is not None:
                        notch_freqs = [[freqs[0]], [freqs[1]]]
                if notch_freqs is not None and log_cb:
                    log_cb("Applying surgical Notch EQ to music...")
            music = _get_music_audio(
                music_type, len(final), sr, notch_freqs=notch_freqs
            )
            final += music * (10 ** (music_volume / 20.0))

        if silence_start > 0:
            fade_in_samples = min(int(silence_start * sr), len(final))
            if fade_in_samples:
                final[:fade_in_samples] *= np.linspace(
                    0.0, 1.0, fade_in_samples
                )[:, np.newaxis]

        if silence_end > 0:
            fade_out_samples = min(int(silence_end * sr), len(final))
            if fade_out_samples:
                final[-fade_out_samples:] *= np.linspace(
                    1.0, 0.0, fade_out_samples
                )[:, np.newaxis]

        peak = np.max(np.abs(final))
        if peak > 0:
            final *= OUTPUT_CEILING / peak

        if output_path:
            ext = str(Path(output_path).suffix.lower())
            if log_cb:
                if ext == ".mp3":
                    log_cb("Writing 320 kbps TPDF-dithered MP3 audio file...")
                elif ext == ".flac":
                    log_cb("Writing 44.1 kHz Lossless FLAC audio file...")
                else:
                    log_cb("Writing 44.1 kHz 16-bit WAV file...")
            _write_audio_file(output_path, final, sr)

        if output_flac_path:
            if log_cb:
                log_cb("Writing 44.1 kHz Lossless FLAC audio file...")
            _write_audio_file(output_flac_path, final, sr)

    if output_raw_path:
        if cancel_cb:
            cancel_cb()
        if log_cb:
            log_cb("Generating raw voice file...")
        raw_final = encode_single_stream(main_audio, speed=1.0, sr=sr)
        
        # Apply fade in & fade out to raw audio too
        if silence_start > 0:
            fade_in_samples = int(silence_start * sr)
            if fade_in_samples > 0 and len(raw_final) >= fade_in_samples:
                fade_in_curve = np.linspace(0.0, 1.0, fade_in_samples)[:, np.newaxis]
                raw_final[:fade_in_samples] *= fade_in_curve

        if silence_end > 0:
            fade_out_samples = int(silence_end * sr)
            if fade_out_samples > 0 and len(raw_final) >= fade_out_samples:
                fade_out_curve = np.linspace(1.0, 0.0, fade_out_samples)[:, np.newaxis]
                raw_final[-fade_out_samples:] *= fade_out_curve

        raw_peak = np.max(np.abs(raw_final))
        if raw_peak > 0:
            raw_final *= OUTPUT_CEILING / raw_peak
        _write_audio_file(output_raw_path, raw_final, sr)

    if log_cb:
        log_cb("Generation finished successfully.")
    if progress_cb:
        progress_cb(100)
