import numpy as np
import soundfile as sf
import os
import sys

# Add root to path
sys.path.append(os.getcwd())
from engine.encoder import mix_final

def test_file_on_disk():
    sr = 44100
    test_out = "scratch/final_check.wav"
    
    # Create minimal dummy data
    main_audio = np.random.randn(sr).astype(np.float32) # 1 sec mono
    intro_audio = None
    outro_audio = None
    
    print(f"Generating test file: {test_out}")
    mix_final(
        intro_audio, main_audio, outro_audio,
        sr=sr, n_layers=24, speed_min=3.0, speed_max=7.0, speed_single=1.0,
        silence_start=0, silence_end=0,
        noise_type="none", noise_volume=-12,
        output_path=test_out
    )
    
    if not os.path.exists(test_out):
        print("FAIL: File was not created!")
        return

    # Read back metadata
    info = sf.info(test_out)
    print(f"File Info - Channels: {info.channels}, Samplerate: {info.samplerate}, Subtype: {info.subtype}")
    
    # Read back data
    data, fs = sf.read(test_out)
    print(f"Data Shape: {data.shape}")
    
    if info.channels == 2 and len(data.shape) == 2 and data.shape[1] == 2:
        print("SUCCESS: File on disk is TRUE STEREO")
    else:
        print("FAIL: File on disk is MONO")
        
    # Check if channels are different
    if np.array_equal(data[:, 0], data[:, 1]):
        print("CRITICAL FAIL: Channels are identical (Dual-Mono)")
    else:
        print("SUCCESS: Channels are unique")

if __name__ == "__main__":
    test_file_on_disk()
