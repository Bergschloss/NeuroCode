import numpy as np
import sys
import os
import soundfile as sf
import gc

# Add project root to path
sys.path.append(r"g:\Anti\Neurocode\SubliminalGenerator")

from engine.encoder import encode_multilayer

def analyze_output(filename):
    data, sr = sf.read(filename)
    print(f"File: {filename}, Shape: {data.shape}, SR: {sr}")
    
    # 1. Check for mono
    l = data[:, 0]
    r = data[:, 1]
    correlation = np.corrcoef(l, r)[0, 1]
    print(f"L/R Correlation: {correlation:.4f}")
    
    # 2. Check for gradual entry (energy in first 50ms vs first 500ms)
    def get_energy(signal, duration_ms):
        samples = int(duration_ms * sr / 1000)
        return np.mean(np.square(signal[:samples]))
    
    e_start_50 = get_energy(data, 50)
    e_start_500 = get_energy(data, 500)
    print(f"Energy 50ms: {e_start_50:.6f}")
    print(f"Energy 500ms: {e_start_500:.6f}")
    
    if e_start_50 < 0.0001:
        print("WARNING: Very low energy at start. Potential gradual entry or silence.")
    else:
        print("SUCCESS: Signal starts immediately.")

    # 3. Frequency check (FFT of first 200ms)
    # We want to see if all frequency bands are present
    samples_200 = int(0.2 * sr)
    fft_l = np.abs(np.fft.rfft(l[:samples_200]))
    freqs = np.fft.rfftfreq(samples_200, 1/sr)
    
    # Check bands: 1kHz, 5kHz, 10kHz, 15kHz
    bands = [1000, 5000, 10000, 15000]
    for b in bands:
        idx = np.argmin(np.abs(freqs - b))
        val = np.mean(fft_l[idx-10:idx+10])
        print(f"Band {b}Hz energy: {val:.4f}")

if __name__ == "__main__":
    sr = 44100
    # Create a 2-second "test" audio (white noise)
    audio = np.random.uniform(-0.5, 0.5, 2 * sr).astype(np.float32)
    
    print("Running encode_multilayer...")
    output = encode_multilayer(audio, sr, n_layers=24, speed_min=3.0, speed_max=7.0)
    
    test_file = "diag_test.wav"
    sf.write(test_file, output, sr)
    
    analyze_output(test_file)
    # os.remove(test_file)
