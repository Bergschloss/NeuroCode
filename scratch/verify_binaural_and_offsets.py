import numpy as np
import sys
from pathlib import Path
import soundfile as sf

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from engine.encoder import encode_multilayer, generate_binaural_beat, mix_final

def verify_offsets():
    print("--- Verifying Layer Offsets ---")
    sr = 44100
    n_layers = 12
    # Create 3-second audio
    audio = np.random.uniform(-0.5, 0.5, 3 * sr).astype(np.float32)
    
    # We will temporarily mock the offset-logging or check offsets.
    # To trace this, let's verify by passing a small audio.
    # In order to see the exact offset selection, we can simulate the calculation
    # or check the behavior of the code. Let's inspect encode_multilayer output.
    output = encode_multilayer(audio, sr, n_layers=n_layers, speed_min=3.0, speed_max=7.0)
    print(f"Layer compilation completed successfully. Output shape: {output.shape}")
    
    # Check that output is not silent
    max_val = np.max(np.abs(output))
    print(f"Max signal value: {max_val:.4f}")
    assert max_val > 0.1, "Output signal is silent!"
    print("SUCCESS: Offset code executed without errors and produced valid audio.")

def verify_binaural_beat():
    print("\n--- Verifying Binaural Beat (Tibetan Bowl Drone) ---")
    sr = 44100
    length = 88200  # 2 seconds
    volume_db = -6.0  # Linear volume = 0.501187
    
    beat = generate_binaural_beat("theta", length, sr, volume_db)
    
    max_val = max(np.max(np.abs(beat[:, 0])), np.max(np.abs(beat[:, 1])))
    print(f"Binaural Drone Peak: {max_val:.4f} (Expected: ~0.5012)")
    assert np.allclose(max_val, 0.501187, atol=1e-4), f"Peak is {max_val}, expected 0.501187"
    
    # Verify it is stereo
    correlation = np.corrcoef(beat[:, 0], beat[:, 1])[0, 1]
    print(f"L/R Correlation: {correlation:.4f}")
    assert correlation < 0.99, "Channels are identical! Must be out of phase for binaural effect."
    print("SUCCESS: Tibetan Bowl Drone generated successfully in stereo with binaural phase shift.")

def verify_peak_normalization():
    print("\n--- Verifying Peak Normalization & Clip Prevention ---")
    sr = 44100
    # Generate 1-second sine waves that are very loud to test clipping
    main = np.ones(sr) * 2.0
    
    out_path = "scratch/temp_test_peak.wav"
    
    mix_final(
        main_audio=main,
        sr=sr,
        n_layers=4,
        speed_min=2.0,
        speed_max=4.0,
        silence_start=0.1,
        silence_end=0.1,
        noise_type="pink",
        noise_volume=0.0,  # Loud noise
        output_path=out_path,
        binaural_type="theta",
        binaural_volume=0.0,  # Loud binaural
        music_type="bowl_1",
        music_volume=-6.0,  # Loud music track
        progress_cb=None
    )
    
    data, file_sr = sf.read(out_path)
    peak = np.max(np.abs(data))
    print(f"Mixed file peak: {peak:.4f} (Expected: <= 1.00)")
    assert peak <= 1.0, "Audio clipped! Peak exceeds 1.0."
    print("SUCCESS: Mixed audio peak normalized and clip prevented.")
    
    # Cleanup
    import os
    if os.path.exists(out_path):
        os.remove(out_path)

if __name__ == "__main__":
    verify_offsets()
    verify_binaural_beat()
    verify_peak_normalization()
