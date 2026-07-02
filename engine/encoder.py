import gc
import os
import numpy as np
import librosa
import soundfile as sf
import miniaudio
from typing import Callable
from scipy.signal import lfilter, butter, iirnotch

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
    """Memory-safe wrapper around librosa time_stretch (chunked)."""
    chunk = CHUNK_SEC * sr
    if len(audio) <= chunk:
        return librosa.effects.time_stretch(audio, rate=rate)
    pieces = []
    for start in range(0, len(audio), chunk):
        end = min(start + chunk, len(audio))
        pieces.append(
            librosa.effects.time_stretch(audio[start:end], rate=rate)
        )
    return np.concatenate(pieces)


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
    ultra_hd_mode: bool = False,
    log_cb: Callable[[str], None] = None,
) -> np.ndarray:
    """
    Full-spectrum AM modulation with Instant Entry guarantee and stereo symmetry / Ultra-HD mode.
    """
    # 1. Prepare source
    audio = _trim_silence(audio.astype(np.float32), threshold=0.01)
    target_samples = len(audio)
    
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
    if ultra_hd_mode:
        # 4 layers total: 2 for Left (channel 0), 2 for Right (channel 1)
        # Left channel layers:
        cf_l0 = 14000.0 + np.random.uniform(-300.0, 300.0)
        sf_l0 = np.random.uniform(speed_min, speed_max)
        cf_l1 = 18000.0 + np.random.uniform(-300.0, 300.0)
        sf_l1 = np.random.uniform(speed_min, speed_max)
        
        # Right channel layers:
        cf_r0 = 14000.0 + np.random.uniform(-300.0, 300.0)
        sf_r0 = np.random.uniform(speed_min, speed_max)
        cf_r1 = 18000.0 + np.random.uniform(-300.0, 300.0)
        sf_r1 = np.random.uniform(speed_min, speed_max)
        
        layers_config = [
            {'channel': 0, 'freq': cf_l0, 'speed': sf_l0, 'offset_zero': True},
            {'channel': 0, 'freq': cf_l1, 'speed': sf_l1, 'offset_zero': False},
            {'channel': 1, 'freq': cf_r0, 'speed': sf_r0, 'offset_zero': True},
            {'channel': 1, 'freq': cf_r1, 'speed': sf_r1, 'offset_zero': False},
        ]
        if log_cb:
            log_cb(f"Ultra-HD (4 layers): L1={cf_l0:.1f} Hz ({sf_l0:.2f}x), L2={cf_l1:.1f} Hz ({sf_l1:.2f}x)")
            log_cb(f"Ultra-HD (4 layers): R1={cf_r0:.1f} Hz ({sf_r0:.2f}x), R2={cf_r1:.1f} Hz ({sf_r1:.2f}x)")
    else:
        # Standard mode: symmetrical stereo grid
        n_left = n_layers // 2
        n_right = n_layers - n_left
        
        if n_left > 1:
            left_freqs = np.linspace(14000.0, 18000.0, n_left)
            left_speeds = np.linspace(speed_min, speed_max, n_left)
        else:
            left_freqs = np.array([14000.0])
            left_speeds = np.array([speed_min])
            
        if n_right > 1:
            right_freqs = np.linspace(14000.0, 18000.0, n_right)
            right_speeds = np.linspace(speed_min, speed_max, n_right)
        else:
            right_freqs = np.array([14000.0])
            right_speeds = np.array([speed_min])
            
        # Add Left channel layers (even panning)
        for j in range(n_left):
            layers_config.append({
                'channel': 0,
                'freq': left_freqs[j],
                'speed': left_speeds[j],
                'offset_zero': (j == 0)
            })
        # Add Right channel layers (odd panning)
        for j in range(n_right):
            layers_config.append({
                'channel': 1,
                'freq': right_freqs[j],
                'speed': right_speeds[j],
                'offset_zero': (j == 0)
            })
            
        if log_cb:
            log_cb(f"Standard mode: {n_left} layers Left, {n_right} layers Right (range 14000 - 18000 Hz, step {4000 / max(1, n_left - 1):.1f} Hz)")

    # 3. Process each layer
    total_layers = len(layers_config)
    for idx, cfg in enumerate(layers_config):
        cf = cfg['freq']
        sf_rate = cfg['speed']
        ch = cfg['channel']
        offset_zero = cfg['offset_zero']
        
        # A. Stretch
        stretched = _stretch_chunked(audio, rate=float(sf_rate), sr=sr)
        n_stretched = len(stretched)
        
        # B. Tiling with high reps
        reps = int(np.ceil(target_samples / n_stretched)) + 2
        tiled_full = np.tile(stretched, reps)
        
        # C. Start offsets (Instant Entry)
        if offset_zero:
            off = 0
        else:
            valid_starts = (active_indices / float(sf_rate)).astype(int)
            valid_starts = valid_starts[valid_starts < n_stretched]
            if len(valid_starts) == 0:
                valid_starts = np.array([0])
            off = np.random.choice(valid_starts)
        
        # D. Slice and apply AM
        chunk = tiled_full[off : off + target_samples].astype(np.float32)
        
        phase = np.random.uniform(0, 2 * np.pi)
        carrier = np.cos(2.0 * np.pi * cf * t + phase).astype(np.float32)
        
        layer_signal = chunk * carrier
        
        # Individual peak normalization
        pk = np.max(np.abs(layer_signal))
        if pk > 0:
            layer_signal /= pk
        
        # E. Add to corresponding channel
        output[:, ch] += layer_signal
        
        del stretched, tiled_full, chunk, carrier, layer_signal
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
        reps = int(np.ceil(length_samples / n_frames))
        tiled = np.tile(music_data, (reps, 1))
        music_signal = tiled[:length_samples].copy()
        
        # Apply 14000 Hz low-pass filter (high cut) to protect the voice spectrum
        cutoff = 14000.0
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
    
    freqs = get_binaural_freqs(beat_type)
    if freqs is None:
        return np.zeros((length_samples, 2), dtype=np.float32)
    f_left, f_right = freqs
        
    t = np.arange(length_samples, dtype=np.float64) / sr
    
    # Pure binaural sine waves (no harmonics)
    left_signal = np.sin(2.0 * np.pi * f_left * t)
    right_signal = np.sin(2.0 * np.pi * f_right * t)
    
    linear_vol = 10 ** (volume_db / 20.0)
    beat = np.column_stack((left_signal, right_signal)) * linear_vol
    return beat.astype(np.float32)


def mix_final(
    main_audio: np.ndarray,
    sr: int,
    n_layers: int,
    speed_min: float,
    speed_max: float,
    silence_start: float, # treat as fade in duration
    silence_end: float,   # treat as fade out duration
    output_path: str,
    output_raw_path: str | None = None,
    binaural_type: str = "none",
    binaural_volume: float = -12.0,
    music_type: str = "none",
    music_volume: float = -12.0,
    music_notch_enabled: bool = False,
    progress_cb: Callable[[int], None] = None,
    log_cb: Callable[[str], None] = None,
    ultra_hd_mode: bool = False,
) -> None:
    """
    Build the WAV with actual fade in / fade out and stereo.
    """
    if log_cb:
        log_cb("Preparing multi-threaded AM encoding...")

    if progress_cb:
        progress_cb(15)

    main_encoded = encode_multilayer(
        main_audio, sr, n_layers, speed_min, speed_max,
        progress_cb=progress_cb, p_start=25, p_end=90,
        ultra_hd_mode=ultra_hd_mode, log_cb=log_cb
    )
    
    if log_cb:
        log_cb("Multi-threaded AM encoding completed.")

    if progress_cb:
        progress_cb(95)

    final = main_encoded.copy()
    del main_encoded
    gc.collect()
    
    if binaural_type != "none":
        if log_cb:
            log_cb(f"Synthesizing binaural beat ({binaural_type})...")
        binaural = generate_binaural_beat(binaural_type, len(final), sr, binaural_volume)
        final += binaural
        
    if music_type != "none":
        if log_cb:
            log_cb(f"Loading and processing background music ({music_type})...")
        notch_freqs = None
        if music_notch_enabled and binaural_type != "none":
            freqs = get_binaural_freqs(binaural_type)
            if freqs is not None:
                f_left, f_right = freqs
                notch_freqs = [[f_left], [f_right]]
                if log_cb:
                    log_cb("Applying surgical Notch EQ to music...")
        music = _get_music_audio(music_type, len(final), sr, notch_freqs=notch_freqs)
        linear_vol = 10 ** (music_volume / 20.0)
        final += music * linear_vol

    # Apply fade in & fade out to mixed audio
    if silence_start > 0:
        fade_in_samples = int(silence_start * sr)
        if fade_in_samples > 0 and len(final) >= fade_in_samples:
            if log_cb:
                log_cb(f"Applying smooth Fade In ({silence_start}s)...")
            fade_in_curve = np.linspace(0.0, 1.0, fade_in_samples)[:, np.newaxis]
            final[:fade_in_samples] *= fade_in_curve

    if silence_end > 0:
        fade_out_samples = int(silence_end * sr)
        if fade_out_samples > 0 and len(final) >= fade_out_samples:
            if log_cb:
                log_cb(f"Applying smooth Fade Out ({silence_end}s)...")
            fade_out_curve = np.linspace(1.0, 0.0, fade_out_samples)[:, np.newaxis]
            final[-fade_out_samples:] *= fade_out_curve

    if log_cb:
        log_cb("Normalizing amplitude of mixed signal...")
    # Peak normalize to exactly 0 dB (amplitude 1.0)
    peak = np.max(np.abs(final))
    if peak > 0:
        final /= peak

    if log_cb:
        log_cb("Writing final WAV file...")
    sf.write(output_path, final, sr, subtype="FLOAT")

    if output_raw_path:
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
                
        sf.write(output_raw_path, raw_final, sr, subtype="FLOAT")

    if log_cb:
        log_cb("Generation finished successfully.")
    if progress_cb:
        progress_cb(100)
