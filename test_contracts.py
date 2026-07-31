import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app import validate_generation_params
from engine.encoder import OUTPUT_CEILING, encode_multilayer, mix_final
from engine.tts import TARGET_SR
from job_state import GenerationCancelled, JobStore, TtsCache


def test_output_contract_is_44khz_pcm16(tmp_path):
    encoded = tmp_path / "encoded.mp3"
    flac_file = tmp_path / "encoded.flac"
    audio = np.sin(
        2 * np.pi * 220 * np.arange(TARGET_SR // 20, dtype=np.float32) / TARGET_SR
    )

    mix_final(
        audio,
        TARGET_SR,
        4,
        2.0,
        3.0,
        0,
        0,
        str(encoded),
        output_flac_path=str(flac_file),
    )

    assert encoded.exists()
    assert flac_file.exists()

    info_flac = sf.info(flac_file)
    assert info_flac.samplerate == 44100
    assert info_flac.channels == 2


def test_disabled_outputs_are_not_written(tmp_path):
    raw = tmp_path / "raw.wav"
    audio = np.ones(256, dtype=np.float32) * 0.1

    mix_final(
        audio,
        TARGET_SR,
        4,
        2.0,
        3.0,
        0,
        0,
        None,
        str(raw),
    )

    assert raw.exists()
    assert list(tmp_path.glob("*")) == [raw]
    data, _ = sf.read(raw)
    assert np.max(np.abs(data)) <= OUTPUT_CEILING + 1e-4


def test_generation_validation_rejects_invalid_contract():
    try:
        validate_generation_params(
            text_main="test",
            layers=3,
            speed_min=4,
            speed_max=3,
            silence_start=0,
            silence_end=0,
            binaural_type="none",
            binaural_volume=-12,
            music_volume=-8,
            voice_volume=0,
            lang_main="auto",
            save_encoded=True,
            save_raw=False,
        )
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
    else:
        raise AssertionError("Invalid DSP parameters were accepted")


def test_am_output_has_negligible_energy_near_nyquist():
    t = np.arange(TARGET_SR // 2, dtype=np.float32) / TARGET_SR
    audio = (
        np.sin(2 * np.pi * 900 * t)
        + 0.4 * np.sin(2 * np.pi * 7000 * t)
    ).astype(np.float32)
    fixed_rng = np.random.default_rng(7)
    with patch("engine.encoder.np.random.default_rng", return_value=fixed_rng):
        encoded = encode_multilayer(audio, TARGET_SR, 4, 2.0, 3.0)

    spectrum = np.abs(np.fft.rfft(encoded[:, 0]))
    frequencies = np.fft.rfftfreq(len(encoded), 1 / TARGET_SR)
    near_nyquist = spectrum[frequencies >= 21500].sum()

    assert near_nyquist / max(spectrum.sum(), 1.0) < 0.005


def test_mix_ceiling_is_minus_one_dbfs(tmp_path):
    encoded = tmp_path / "ceiling.wav"
    audio = np.ones(TARGET_SR // 20, dtype=np.float32)

    mix_final(audio, TARGET_SR, 4, 2.0, 3.0, 0, 0, str(encoded))

    data, _ = sf.read(encoded)
    assert np.max(np.abs(data)) <= OUTPUT_CEILING + 1e-4


def test_job_store_cancels_and_bounds_logs():
    store = JobStore(max_jobs=2, max_logs=2)
    store.create("one")
    store.log("one", "a")
    store.log("one", "b")
    store.log("one", "c")
    assert store.get("one")["logs"] == ["b", "c"]
    assert store.cancel("one")
    try:
        store.raise_if_cancelled("one")
    except GenerationCancelled:
        pass
    else:
        raise AssertionError("Cancellation signal was not raised")


def test_tts_cache_is_lru_and_bounded():
    cache = TtsCache(max_entries=2, max_bytes=64)
    cache.put(("a",), (np.zeros(4, dtype=np.float32), TARGET_SR))
    cache.put(("b",), (np.zeros(4, dtype=np.float32), TARGET_SR))
    assert cache.get(("a",)) is not None
    cache.put(("c",), (np.zeros(4, dtype=np.float32), TARGET_SR))
    assert cache.get(("b",)) is None
    assert cache.get(("a",)) is not None


def test_mono_voice_writes_identical_channels():
    t = np.arange(TARGET_SR // 2, dtype=np.float32) / TARGET_SR
    audio = np.sin(2 * np.pi * 900 * t).astype(np.float32)

    encoded = encode_multilayer(audio, TARGET_SR, 8, 2.0, 3.0, mono=True)

    assert encoded.shape[1] == 2
    assert np.array_equal(encoded[:, 0], encoded[:, 1])


def test_stereo_voice_keeps_channels_independent():
    t = np.arange(TARGET_SR // 2, dtype=np.float32) / TARGET_SR
    audio = np.sin(2 * np.pi * 900 * t).astype(np.float32)

    encoded = encode_multilayer(audio, TARGET_SR, 8, 2.0, 3.0, mono=False)

    assert not np.array_equal(encoded[:, 0], encoded[:, 1])


def test_mono_voice_halves_the_layer_count():
    t = np.arange(TARGET_SR // 4, dtype=np.float32) / TARGET_SR
    audio = np.sin(2 * np.pi * 900 * t).astype(np.float32)
    logs = []

    encode_multilayer(
        audio, TARGET_SR, 8, 2.0, 3.0, log_cb=logs.append, mono=True
    )

    assert any("4 mono voice layers" in msg for msg in logs)


def test_mono_voice_leaves_binaural_in_stereo(tmp_path):
    silent = tmp_path / "mono_no_beat.wav"
    beating = tmp_path / "mono_with_beat.wav"
    audio = np.sin(
        2 * np.pi * 220 * np.arange(TARGET_SR // 4, dtype=np.float32) / TARGET_SR
    )

    mix_final(
        audio, TARGET_SR, 8, 2.0, 3.0, 0, 0, str(silent),
        binaural_type="none", mono_voice=True,
    )
    mix_final(
        audio, TARGET_SR, 8, 2.0, 3.0, 0, 0, str(beating),
        binaural_type="theta", binaural_volume=-12.0, mono_voice=True,
    )

    quiet, _ = sf.read(silent)
    loud, _ = sf.read(beating)

    # Mono voice alone: channels differ only by TPDF dither (~ -90 dBFS).
    assert np.max(np.abs(quiet[:, 0] - quiet[:, 1])) < 1e-3
    # Binaural must still produce a genuine inter-channel difference.
    assert np.max(np.abs(loud[:, 0] - loud[:, 1])) > 0.01
