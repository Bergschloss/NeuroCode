import numpy as np
import sys
import soundfile as sf

sys.path.append(r"g:\Anti\Neurocode\SubliminalGenerator")
from engine.encoder import encode_single_stream

sr = 44100
audio = np.random.uniform(-0.5, 0.5, sr).astype(np.float32)
output = encode_single_stream(audio, speed=1.0, sr=sr)

l = output[:, 0]
r = output[:, 1]
corr = np.corrcoef(l, r)[0, 1]
print(f"Single stream correlation: {corr:.4f}")
if corr < 0.99:
    print("SUCCESS: Pseudo-stereo detected.")
else:
    print("FAILURE: Still hard-mono.")
