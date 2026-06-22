import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

def verify_24_layers():
    n_layers = 24
    speed_min = 3.0
    speed_max = 7.0
    
    # These match the exact math inside engine/encoder.py
    carrier_freqs = np.linspace(500, 18000, n_layers)
    speed_factors = np.linspace(speed_min, speed_max, n_layers)
    
    print("=== Verification of 24 Layers ===")
    print(f"Total layers configured: {n_layers}")
    print(f"Coded voice speed ranges from {speed_min}x to {speed_max}x")
    print(f"Frequency spectrum ranges from 500 Hz to 18,000 Hz\n")
    
    print(f"{'Layer':<6} | {'Carrier Freq':<15} | {'Speed Factor':<12} | {'Panning (Ear)':<15}")
    print("-" * 60)
    
    for i in range(n_layers):
        cf = carrier_freqs[i]
        sf_rate = speed_factors[i]
        pan = "Left Ear (Even)" if i % 2 == 0 else "Right Ear (Odd)"
        print(f"{i+1:<6} | {cf:>11.2f} Hz | {sf_rate:>10.2f}x | {pan:<15}")
        
    print("\nResult:")
    print(f"- Left Channel: {sum(1 for i in range(n_layers) if i % 2 == 0)} independent speed layers mixed together.")
    print(f"- Right Channel: {sum(1 for i in range(n_layers) if i % 2 == 1)} independent speed layers mixed together.")
    print("- Both channels play their respective 12 layers concurrently in a single stereo audio track.")

if __name__ == "__main__":
    verify_24_layers()
