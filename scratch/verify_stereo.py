import numpy as np
import sys
import os

# Add the project directory to sys.path
sys.path.append(r"g:\Anti\Neurocode\SubliminalGenerator")

from engine.encoder import encode_multilayer

def test_stereo():
    sr = 44100
    # 1 second of white noise as "audio"
    audio = np.random.uniform(-0.1, 0.1, sr).astype(np.float32)
    
    print("Testing encode_multilayer with 24 layers...")
    output = encode_multilayer(audio, sr, n_layers=24, speed_min=3.0, speed_max=7.0)
    
    # Check shape
    print(f"Output shape: {output.shape}")
    
    # Check if L and R are different
    diff = output[:, 0] - output[:, 1]
    std_diff = np.std(diff)
    print(f"Standard deviation of L-R difference: {std_diff}")
    
    if std_diff > 1e-5:
        print("SUCCESS: Audio is clearly stereo (channels are different).")
    else:
        print("FAILURE: Audio is mono or nearly mono.")

if __name__ == "__main__":
    test_stereo()
