import sys
import os
sys.path.append(os.getcwd())

import numpy as np
import librosa
import soundfile as sf
from engine.encoder import encode_multilayer, encode_single_stream

def verify_stereo():
    sr = 44100
    # Create 1 second of dummy audio (sine wave)
    t = np.arange(sr) / sr
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    
    print("--- Testing encode_multilayer (Hard Stereo) ---")
    n_layers = 24
    output = encode_multilayer(audio, sr, n_layers, 3.0, 7.0)
    
    print(f"Output shape: {output.shape}")
    if output.shape[1] != 2:
        print("FAIL: Output is not stereo (columns != 2)")
    else:
        print("SUCCESS: Output is stereo")
    
    # Calculate correlation
    corr = np.corrcoef(output[:, 0], output[:, 1])[0, 1]
    print(f"Channel Correlation: {corr:.4f}")
    if abs(corr) < 0.1:
        print("SUCCESS: Channels are highly decorrelated (True Stereo)")
    else:
        print(f"WARNING: High correlation detected ({corr:.4f})")
        
    # Check if both channels have energy
    rms_l = np.sqrt(np.mean(output[:, 0]**2))
    rms_r = np.sqrt(np.mean(output[:, 1]**2))
    print(f"RMS Left: {rms_l:.4f}, RMS Right: {rms_r:.4f}")
    if rms_l > 0 and rms_r > 0:
        print("SUCCESS: Both channels have signal energy")
    else:
        print("FAIL: One or both channels are silent")

    print("\n--- Testing encode_single_stream (Pseudo Stereo) ---")
    output_single = encode_single_stream(audio, speed=1.0, sr=sr)
    corr_single = np.corrcoef(output_single[:, 0], output_single[:, 1])[0, 1]
    print(f"Single-stream Correlation: {corr_single:.4f}")
    if abs(corr_single) < 0.99:
        print("SUCCESS: Single-stream is not hard-mono")
    else:
        print("FAIL: Single-stream is hard-mono (1.0 correlation)")

if __name__ == "__main__":
    # Ensure we can import from the root
    import sys
    sys.path.append(os.getcwd())
    verify_stereo()
