import urllib.request
import urllib.parse
import json
import time
import sys
from pathlib import Path
import soundfile as sf

# Add project root to path just in case
sys.path.append(str(Path(__file__).resolve().parents[1]))

URL_BASE = "http://127.0.0.1:7860"

def run_test_and_inspect():
    print("=== Neurocode Generator Test Run ===")
    
    # 1. Prepare form parameters
    params = {
        'text_intro': 'Вступ. Починаємо сеанс афірмацій.',
        'text_main': 'Моє підсвідоме відкрите. Я відчуваю впевненість.\nКожен день приносить мені нові можливості.\nЯ здоровий і спокійний.',
        'text_outro': 'Завершення. Всі афірмації прийняті.',
        'voice_uk': 'uk-UA-PolinaNeural',
        'voice_ru': 'ru-RU-SvetlanaNeural',
        'voice_en': 'en-US-AriaNeural',
        'lang_intro': 'auto',
        'lang_main': 'auto',
        'lang_outro': 'auto',
        'layers': '24',
        'speed_min': '3.0',
        'speed_max': '7.0',
        'speed_single': '1.5',
        'silence_start': '1.0',
        'silence_end': '1.0',
        'noise_type': 'sea',
        'noise_volume': '-18.0'
    }
    
    data = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(f"{URL_BASE}/generate", data=data)
    
    try:
        print("Sending generation request to server...")
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            job_id = res_data.get("job_id")
            print(f"Request successful! Job ID: {job_id}")
    except Exception as e:
        print(f"Error connecting to server. Is it running? Details: {e}")
        return
        
    # 2. Poll job status
    print("Polling job status...")
    while True:
        try:
            with urllib.request.urlopen(f"{URL_BASE}/status/{job_id}") as response:
                status_data = json.loads(response.read().decode('utf-8'))
                status = status_data.get("status")
                progress = status_data.get("progress", 0)
                print(f"Job Status: {status} ({progress}%)")
                
                if status == "done":
                    print("Job finished successfully!")
                    break
                elif status == "error":
                    print(f"Job failed with error: {status_data.get('error')}")
                    return
        except Exception as e:
            print(f"Error polling status: {e}")
            return
        time.sleep(1.0)
        
    # 3. Verify output files
    print("\nVerifying output files...")
    outputs_dir = Path(__file__).resolve().parents[1] / "outputs"
    coded_file = outputs_dir / f"{job_id}.wav"
    raw_file = outputs_dir / f"{job_id}_raw.wav"
    
    if coded_file.exists():
        print(f"Coded WAV file exists at: {coded_file} (Size: {coded_file.stat().st_size} bytes)")
        inspect_file(coded_file, "Coded WAV")
    else:
        print(f"ERROR: Coded WAV file not found at: {coded_file}")
        
    if raw_file.exists():
        print(f"Raw WAV file exists at: {raw_file} (Size: {raw_file.stat().st_size} bytes)")
        inspect_file(raw_file, "Raw WAV")
    else:
        print(f"ERROR: Raw WAV file not found at: {raw_file}")

def inspect_file(filepath, label):
    print(f"\n--- Metadata & Analysis for {label} ({filepath.name}) ---")
    
    # Read file using soundfile
    data, sr = sf.read(str(filepath))
    shape = data.shape
    
    print(f"Sample Rate: {sr} Hz")
    print(f"Shape: {shape} (samples, channels)")
    print(f"Channels: {shape[1] if len(shape) > 1 else 1}")
    print(f"Duration: {len(data) / sr:.2f} seconds")
    
    # Check if there is any difference between L and R channels (to verify it's stereo and synchronized)
    if len(shape) > 1 and shape[1] == 2:
        l_channel = data[:, 0]
        r_channel = data[:, 1]
        
        # Check standard deviation of the difference
        diff = l_channel - r_channel
        std_diff = float(diff.std())
        max_diff = float(abs(diff).max())
        
        # Pearson correlation coefficient between L and R
        import numpy as np
        correlation = float(np.corrcoef(l_channel, r_channel)[0, 1])
        
        print(f"Left Channel Peak: {float(abs(l_channel).max()):.4f}")
        print(f"Right Channel Peak: {float(abs(r_channel).max()):.4f}")
        print(f"L/R Correlation: {correlation:.4f}")
        print(f"Standard Dev of L-R Difference: {std_diff:.6f}")
        print(f"Max Absolute L-R Difference: {max_diff:.6f}")
        
        if std_diff < 1e-7:
            print("Note: Channels are identical (mono).")
        else:
            print("Note: Channels contain distinct signals (stereo).")
    else:
        print("Note: File is mono.")

if __name__ == "__main__":
    run_test_and_inspect()
