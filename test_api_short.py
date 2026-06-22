"""Short smoke test for the Neurocode Studio API."""
import requests
import time
import soundfile as sf

BASE = "http://127.0.0.1:7860"


def test_generate_and_download():
    # 1. Submit a tiny job
    r = requests.post(
        f"{BASE}/generate",
        data={
            "text_main": "Тестове повідомлення.",
            "lang_main": "auto",
            "layers": 4,
            "speed_min": 3.0,
            "speed_max": 5.0,
            "silence_start": 0.5,
            "silence_end": 0.5,
            "binaural_type": "none",
            "music_type": "none",
        },
        timeout=30,
    )
    r.raise_for_status()
    job_id = r.json()["job_id"]
    print(f"Job created: {job_id}")

    # 2. Poll until done (or error)
    for _ in range(120):
        status = requests.get(f"{BASE}/status/{job_id}", timeout=10).json()
        if status.get("status") == "done":
            break
        if status.get("status") == "error":
            raise RuntimeError(f"Job failed: {status.get('error')}")
        time.sleep(1)
    else:
        raise TimeoutError("Generation did not finish in time")

    # 3. Download and validate WAV
    wav = requests.get(f"{BASE}/download/{job_id}", timeout=30)
    wav.raise_for_status()
    import os
    path = f"outputs/neurocode_test_{job_id}.wav"
    with open(path, "wb") as f:
        f.write(wav.content)

    data, sr = sf.read(path)
    # Cleanup file
    if os.path.exists(path):
        os.remove(path)
        
    assert sr in (44100, 48000), f"Expected 44100 or 48000 Hz, got {sr}"
    assert len(data.shape) == 2 and data.shape[1] == 2, "Expected stereo output"
    assert len(data) > 0, "Empty audio file"
    print(f"OK: verified online synthesis and download successfully, duration={len(data)/sr:.2f}s, shape={data.shape}")


if __name__ == "__main__":
    test_generate_and_download()
