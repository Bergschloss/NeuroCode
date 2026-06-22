import numpy as np
import sys
import os
import soundfile as sf

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
    l = output[:, 0]
    r = output[:, 1]
    
    diff = l - r
    std_diff = np.std(diff)
    correlation = np.corrcoef(l, r)[0, 1]
    
    # Check for leading silence
    first_100ms = output[:int(0.1 * sr)]
    has_signal = np.any(np.abs(first_100ms) > 0.01)
    print(f"Signal present in first 100ms: {has_signal}")
    
    # Write to file and check if it's 2 channels
    test_path = "stereo_test.wav"
    sf.write(test_path, output, sr)
    info = sf.info(test_path)
    print(f"WAV Info: channels={info.channels}, frames={info.frames}")
    
    if correlation < 0.1:
        print("PERFECT: Content-level stereo width achieved.")
    elif correlation < 0.9:
        print("GOOD: Phase-level stereo width achieved.")
    
    if not has_signal:
        print("WARNING: Leading silence detected!")
    else:
        print("SUCCESS: Immediate signal entry confirmed.")

    os.remove(test_path)

if __name__ == "__main__":
    try:
        test_stereo()
    except Exception as e:
        print(f"ERROR: {e}")
