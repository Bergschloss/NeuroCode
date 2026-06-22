import asyncio
import time
import uuid
from pathlib import Path

import uvicorn
from fastapi import BackgroundTasks, FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from engine.encoder import mix_final, get_music_tracks
from engine.tts import TARGET_SR, generate_tts_multilang, generate_tts_single

app = FastAPI(title="Neurocode Studio")

OUTPUTS = Path("outputs")
OUTPUTS.mkdir(exist_ok=True)
STATIC = Path("static")

app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

jobs: dict[str, dict] = {}
tts_cache: dict = {}


def cleanup_old_outputs(max_age_seconds: float = 3600):
    """Delete wav files in outputs/ folder that are older than max_age_seconds."""
    try:
        now = time.time()
        for path in OUTPUTS.glob("*.wav"):
            if path.is_file():
                file_age = now - path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        path.unlink()
                        print(f"[CLEANUP] Deleted old output file: {path.name}")
                    except Exception as e:
                        print(f"[CLEANUP ERROR] Could not delete {path.name}: {e}")
    except Exception as e:
        print(f"[CLEANUP ERROR] General cleanup error: {e}")


@app.get("/music_tracks")
async def music_tracks():
    """Return available background music tracks from engine/music/ directory."""
    return get_music_tracks()


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.post("/generate")
async def generate(
    background_tasks: BackgroundTasks,
    text_main: str = Form(...),
    voice_uk: str = Form("uk-UA-PolinaNeural"),
    voice_ru: str = Form("ru-RU-SvetlanaNeural"),
    voice_en: str = Form("en-US-AriaNeural"),
    lang_main: str = Form("auto"),
    layers: int = Form(24),
    speed_min: float = Form(2.0),
    speed_max: float = Form(4.0),
    silence_start: float = Form(1.5),
    silence_end: float = Form(1.5),
    binaural_type: str = Form("none"),
    binaural_volume: float = Form(-12.0),
    music_type: str = Form("none"),
    music_volume: float = Form(-8.0),
    music_notch_enabled: str = Form("false"),
    client_session_id: str = Form(None),
    export_filename: str = Form(None),
    export_dir: str = Form(None),
    save_encoded: str = Form("true"),
    save_raw: str = Form("false"),
    ultra_hd_mode: str = Form("false"),
):
    background_tasks.add_task(cleanup_old_outputs, 3600)
    job_id = uuid.uuid4().hex[:8]

    save_enc_flag = save_encoded.lower() in ("true", "1", "yes", "on")
    save_raw_flag = save_raw.lower() in ("true", "1", "yes", "on")

    # Determine target directories
    target_dir_encoded = OUTPUTS
    target_dir_raw = OUTPUTS
    if export_dir:
        try:
            custom_path = Path(export_dir).resolve()
            custom_path.mkdir(parents=True, exist_ok=True)
            if save_enc_flag:
                target_dir_encoded = custom_path
            if save_raw_flag:
                target_dir_raw = custom_path
        except Exception as e:
            print(f"[EXPORT ERROR] Could not create custom directory {export_dir}, falling back to outputs/: {e}")

    # Determine custom filename
    fname = job_id
    if export_filename:
        base_name = export_filename
        if base_name.lower().endswith(".wav"):
            base_name = base_name[:-4]
        import re
        base_name = re.sub(r'[\\/*?:"<>|]', "", base_name)
        base_name = base_name.strip()
        if base_name:
            fname = base_name

    # Encoded file path resolution
    if export_filename and fname != job_id:
        candidate = target_dir_encoded / f"{fname}.wav"
        if candidate.exists():
            counter = 1
            while True:
                candidate = target_dir_encoded / f"{fname} ({counter}).wav"
                if not candidate.exists():
                    break
                counter += 1
            output_path = str(candidate)
        else:
            output_path = str(candidate)
    else:
        output_path = str(target_dir_encoded / f"{fname}.wav")

    # Raw file path resolution
    if export_filename and fname != job_id:
        candidate_raw = target_dir_raw / f"{fname}_raw.wav"
        if candidate_raw.exists():
            counter = 1
            while True:
                candidate_raw = target_dir_raw / f"{fname} ({counter})_raw.wav"
                if not candidate_raw.exists():
                    break
                counter += 1
            output_raw_path = str(candidate_raw)
        else:
            output_raw_path = str(candidate_raw)
    else:
        output_raw_path = str(target_dir_raw / f"{fname}_raw.wav")

    jobs[job_id] = {
        "status": "processing",
        "progress": 5,
        "output_path": output_path,
        "output_raw_path": output_raw_path
    }
    voices = {"uk": voice_uk, "ru": voice_ru, "en": voice_en}
    notch_flag = music_notch_enabled.lower() in ("true", "on", "1", "yes")
    ultra_hd_flag = ultra_hd_mode.lower() in ("true", "on", "1", "yes")
    background_tasks.add_task(
        _run,
        job_id,
        text_main.strip(),
        voices,
        lang_main,
        layers, speed_min, speed_max,
        silence_start, silence_end,
        binaural_type, binaural_volume,
        music_type, music_volume,
        notch_flag,
        output_path, output_raw_path,
        client_session_id,
        ultra_hd_flag,
    )
    return {"job_id": job_id}


def add_job_log(job_id, msg):
    if job_id in jobs:
        if "logs" not in jobs[job_id]:
            jobs[job_id]["logs"] = []
        jobs[job_id]["logs"].append(msg)
        try:
            print(f"[{job_id}] {msg}")
        except UnicodeEncodeError:
            safe_msg = msg.encode('ascii', errors='backslashreplace').decode('ascii')
            print(f"[{job_id}] {safe_msg}")


async def _run(
    job_id,
    text_main,
    voices,
    lang_main,
    layers, speed_min, speed_max,
    silence_start, silence_end,
    binaural_type, binaural_volume,
    music_type, music_volume,
    music_notch_enabled,
    out, out_raw,
    client_session_id=None,
    ultra_hd_mode=False,
):
    try:
        add_job_log(job_id, "Ініціалізація сесії генерації...")
        sr = TARGET_SR
        jobs[job_id]["progress"] = 8

        # ── Main text TTS (will be multi-layer encoded) ────────────
        if not text_main:
            raise ValueError("Основний текст не може бути порожнім")

        # Check cache
        cache_hit = False
        global tts_cache
        if (
            tts_cache.get("client_session_id") == client_session_id
            and tts_cache.get("text_main") == text_main
            and tts_cache.get("voices") == voices
            and tts_cache.get("lang_main") == lang_main
            and tts_cache.get("audio") is not None
        ):
            cache_hit = True

        if cache_hit:
            add_job_log(job_id, "Використання збереженого з попередньої генерації голосу (TTS кеш)...")
            main_audio = tts_cache["audio"].copy()
            sr = tts_cache["sr"]
        else:
            add_job_log(job_id, "Синтез мовлення за допомогою Neural TTS...")
            main_audio, sr = await generate_tts_multilang(text_main, voices, lang_main)
            add_job_log(job_id, "Синтез Neural TTS завершено успішно.")
            if client_session_id:
                tts_cache = {
                    "client_session_id": client_session_id,
                    "text_main": text_main,
                    "voices": voices.copy(),
                    "lang_main": lang_main,
                    "audio": main_audio.copy(),
                    "sr": sr
                }
        jobs[job_id]["progress"] = 25

        def cb(p):
            jobs[job_id]["progress"] = p

        def log_cb(msg):
            add_job_log(job_id, msg)

        loop = asyncio.get_event_loop()
        add_job_log(job_id, "Початок зведення та кодування...")
        await loop.run_in_executor(
            None,
            mix_final,
            main_audio,
            sr, layers, speed_min, speed_max,
            silence_start, silence_end,
            out, out_raw,
            binaural_type, binaural_volume,
            music_type, music_volume,
            music_notch_enabled,
            cb,
            log_cb,
            ultra_hd_mode,
        )

        jobs[job_id].update({"status": "done", "progress": 100})
        add_job_log(job_id, "Сесія генерації успішно завершена.")
    except Exception as exc:
        add_job_log(job_id, f"Помилка: {exc}")
        jobs[job_id].update({"status": "error", "error": str(exc), "progress": 0})


@app.get("/status/{job_id}")
async def status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})


@app.get("/jobs")
async def get_all_jobs():
    return jobs


@app.get("/download/{job_id}")
async def download(job_id: str):
    job = jobs.get(job_id)
    if job and "output_path" in job:
        path = Path(job["output_path"])
        if path.exists():
            return FileResponse(
                str(path), media_type="audio/wav", filename=path.name
            )
    path = OUTPUTS / f"{job_id}.wav"
    if path.exists():
        return FileResponse(
            str(path), media_type="audio/wav", filename=f"neurocode_{job_id}.wav"
        )
    return {"error": "not found"}


@app.get("/download_raw/{job_id}")
async def download_raw(job_id: str):
    job = jobs.get(job_id)
    if job and "output_raw_path" in job:
        path = Path(job["output_raw_path"])
        if path.exists():
            return FileResponse(
                str(path), media_type="audio/wav", filename=path.name
            )
    path = OUTPUTS / f"{job_id}_raw.wav"
    if path.exists():
        return FileResponse(
            str(path), media_type="audio/wav", filename=f"neurocode_{job_id}_raw.wav"
        )
    return {"error": "not found"}


class GUI_API:
    def __init__(self, window):
        self.window = window

    def choose_folder(self):
        try:
            import webview
            result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
            if result:
                return result[0]
        except Exception as e:
            print(f"[GUI API ERROR] choose_folder error: {e}")
        return None


if __name__ == "__main__":
    import sys
    if "--browser" in sys.argv:
        uvicorn.run("app:app", host="127.0.0.1", port=7860, reload=True)
    else:
        try:
            import webview
            import threading
            
            def start_server():
                uvicorn.run("app:app", host="127.0.0.1", port=7860, log_level="warning")
                
            t = threading.Thread(target=start_server, daemon=True)
            t.start()
            
            time.sleep(0.8)
            
            window = webview.create_window(
                "Neurocode Studio",
                "http://127.0.0.1:7860",
                width=1280,
                height=850,
                min_size=(1000, 700)
            )
            window.js_api = GUI_API(window)
            webview.start()
            
        except ImportError:
            print("pywebview is not installed. Falling back to browser mode...")
            uvicorn.run("app:app", host="127.0.0.1", port=7860, reload=True)
