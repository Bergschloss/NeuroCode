import asyncio
import os
import time
import uuid
from pathlib import Path

import uvicorn
from fastapi import BackgroundTasks, FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from engine.encoder import mix_final, get_music_tracks
from engine.tts import TARGET_SR, generate_tts_multilang
from job_state import GenerationCancelled, JobStore, TtsCache

app = FastAPI(title="Neurocode Studio")

APP_DIR = Path(__file__).resolve().parent
OUTPUTS = APP_DIR / "outputs"
OUTPUTS.mkdir(exist_ok=True)
STATIC = APP_DIR / "static"

def generate_auto_filename(text: str, music_type: str) -> str:
    import re
    # Extract first 2 words, keeping alphanumeric characters (supporting Cyrillic/Ukrainian)
    words = re.findall(r'\w+', text, flags=re.UNICODE)
    text_part = "_".join(words[:2])
    if not text_part:
        text_part = "subliminal"
        
    music_part = ""
    if music_type and music_type != "none":
        clean_music = re.sub(r'[^\w\-]', '_', music_type)
        music_part = f"_{clean_music}"
        
    rand_part = uuid.uuid4().hex[:4]
    full_name = f"{text_part}{music_part}_{rand_part}"
    
    # Final cleanup of forbidden characters for safety
    full_name = re.sub(r'[\\/*?:"<>|]', "", full_name)
    if len(full_name) > 120:
        full_name = full_name[:120]
    return full_name

app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")




job_store = JobStore()
tts_cache = TtsCache()
generation_slots = asyncio.Semaphore(1)


def validate_generation_params(
    *,
    text_main: str,
    layers: int,
    speed_min: float,
    speed_max: float,
    silence_start: float,
    silence_end: float,
    binaural_type: str,
    binaural_volume: float,
    music_volume: float,
    voice_volume: float,
    lang_main: str,
    save_encoded: bool,
    save_raw: bool,
    save_flac: bool = False,
) -> None:
    errors = []
    if not text_main.strip():
        errors.append("Affirmation text cannot be empty")
    if layers < 4 or layers > 16 or layers % 2:
        errors.append("Layers must be an even number from 4 to 16")
    if not 2.0 <= speed_min <= 9.0:
        errors.append("Minimum speed must be between 2x and 9x")
    if not 3.0 <= speed_max <= 10.0:
        errors.append("Maximum speed must be between 3x and 10x")
    if speed_min > speed_max:
        errors.append("Minimum speed cannot exceed maximum speed")
    if not 0 <= silence_start <= 5 or not 0 <= silence_end <= 5:
        errors.append("Fade durations must be between 0 and 5 seconds")
    if binaural_type not in {
        "none", "delta", "theta", "alpha", "beta", "turbo_manipura"
    }:
        errors.append("Unknown binaural preset")
    if lang_main not in {"auto", "uk", "ru", "en"}:
        errors.append("Unknown synthesis language")
    if not -30 <= binaural_volume <= -6:
        errors.append("Binaural volume must be between -30 dB and -6 dB")
    if not -30 <= music_volume <= 0 or not -30 <= voice_volume <= 0:
        errors.append("Music and voice volumes must be between -30 dB and 0 dB")
    if not save_encoded and not save_raw and not save_flac:
        errors.append("At least one output format must be enabled")
    if errors:
        raise HTTPException(status_code=422, detail=errors)


def cleanup_old_outputs(max_age_seconds: float = 3600):
    """Delete output files in outputs/ folder that are older than max_age_seconds."""
    try:
        now = time.time()
        for ext in ("*.mp3", "*.flac", "*.wav"):
            for path in OUTPUTS.glob(ext):
                if path.is_file():
                    file_age = now - path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            path.unlink()
                        except Exception as e:
                            print(f"[CLEANUP ERROR] Could not delete {path.name}: {e}")
    except Exception as e:
        print(f"[CLEANUP ERROR] Directory cleanup failed: {e}")


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
    layers: int = Form(8),
    speed_min: float = Form(3.0),
    speed_max: float = Form(4.0),
    silence_start: float = Form(1.5),
    silence_end: float = Form(1.5),
    binaural_type: str = Form("none"),
    binaural_volume: float = Form(-12.0),
    music_type: str = Form("none"),
    music_volume: float = Form(-4.0),
    music_notch_enabled: str = Form("false"),
    mono_voice: str = Form("false"),
    client_session_id: str = Form(None),
    export_filename: str = Form(None),
    export_dir: str = Form(None),
    save_encoded: str = Form("true"),
    save_flac: str = Form("false"),
    save_raw: str = Form("false"),
    voice_volume: float = Form(-2.0),
):
    if not export_dir or not export_dir.strip():
        raise HTTPException(status_code=400, detail="Output directory is required")

    background_tasks.add_task(cleanup_old_outputs, 3600)
    job_id = uuid.uuid4().hex[:8]

    save_enc_flag = save_encoded.lower() in ("true", "1", "yes", "on")
    save_flac_flag = save_flac.lower() in ("true", "1", "yes", "on")
    save_raw_flag = save_raw.lower() in ("true", "1", "yes", "on")
    mono_flag = mono_voice.lower() in ("true", "1", "yes", "on")

    validate_generation_params(
        text_main=text_main,
        layers=layers,
        speed_min=speed_min,
        speed_max=speed_max,
        silence_start=silence_start,
        silence_end=silence_end,
        binaural_type=binaural_type,
        binaural_volume=binaural_volume,
        music_volume=music_volume,
        voice_volume=voice_volume,
        lang_main=lang_main,
        save_encoded=save_enc_flag,
        save_raw=save_raw_flag,
        save_flac=save_flac_flag,
    )
    job_store.cleanup()

    # Determine target directories
    target_dir_encoded = OUTPUTS
    target_dir_raw = OUTPUTS
    if export_dir:
        try:
            custom_path = Path(export_dir).resolve()
            custom_path.mkdir(parents=True, exist_ok=True)
            if save_enc_flag or save_flac_flag:
                target_dir_encoded = custom_path
            if save_raw_flag:
                target_dir_raw = custom_path
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Output directory is not writable: {e}",
            ) from e

    # Determine custom filename
    if export_filename and export_filename.strip():
        base_name = export_filename.strip()
        for ext in (".wav", ".mp3", ".flac"):
            if base_name.lower().endswith(ext):
                base_name = base_name[:-len(ext)]
        import re
        base_name = re.sub(r'[\\/*?:"<>|]', "", base_name).strip()
        fname = base_name if base_name else generate_auto_filename(text_main, music_type)
    else:
        fname = generate_auto_filename(text_main, music_type)

    output_path = None
    output_flac_path = None
    output_raw_path = None

    # Encoded MP3 320k file path resolution
    if save_enc_flag:
        fname_enc = f"{fname}_mono.mp3" if mono_flag else f"{fname}.mp3"
        output_path = str(target_dir_encoded / fname_enc)

    # Lossless FLAC file path resolution
    if save_flac_flag:
        fname_flac = f"{fname}_mono.flac" if mono_flag else f"{fname}.flac"
        output_flac_path = str(target_dir_encoded / fname_flac)

    # Raw file path resolution
    if save_raw_flag:
        output_raw_path = str(target_dir_raw / f"{fname}_raw.mp3")

    job_store.create(
        job_id,
        output_path=output_path,
        output_flac_path=output_flac_path,
        output_raw_path=output_raw_path,
    )
    voices = {"uk": voice_uk, "ru": voice_ru, "en": voice_en}
    notch_flag = music_notch_enabled.lower() in ("true", "on", "1", "yes")
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
        output_path, output_raw_path, output_flac_path,
        client_session_id,
        voice_volume,
        save_enc_flag,
        save_raw_flag,
        mono_flag,
    )
    return {"job_id": job_id}


def add_job_log(job_id, msg):
    job_store.log(job_id, msg)
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
    out, out_raw, out_flac=None,
    client_session_id=None,
    voice_volume=-2.0,
    save_enc_flag=True,
    save_raw_flag=False,
    mono_voice=False,
):
    try:
        add_job_log(job_id, "Queued for generation...")
        async with generation_slots:
            job_store.raise_if_cancelled(job_id)
            job_store.update(job_id, status="processing", progress=5)
            await _process_job(
                job_id, text_main, voices, lang_main,
                layers, speed_min, speed_max,
                silence_start, silence_end,
                binaural_type, binaural_volume,
                music_type, music_volume, music_notch_enabled,
                out, out_raw, out_flac, client_session_id, voice_volume,
                save_enc_flag, save_raw_flag,
                mono_voice,
            )
    except GenerationCancelled:
        add_job_log(job_id, "Generation cancelled.")
        job_store.update(job_id, status="cancelled", progress=0)
        for path in (out, out_raw, out_flac):
            if path:
                Path(path).unlink(missing_ok=True)
    except Exception as exc:
        add_job_log(job_id, f"Error: {exc}")
        job_store.update(job_id, status="error", error=str(exc), progress=0)
    finally:
        job = job_store.get(job_id)
        if job and job.get("status") in ("cancelling", "queued"):
            job_store.update(job_id, status="cancelled", progress=0)


async def _process_job(
    job_id,
    text_main,
    voices,
    lang_main,
    layers, speed_min, speed_max,
    silence_start, silence_end,
    binaural_type, binaural_volume,
    music_type, music_volume,
    music_notch_enabled,
    out, out_raw, out_flac,
    client_session_id,
    voice_volume,
    save_enc_flag,
    save_raw_flag,
    mono_voice=False,
):
        add_job_log(job_id, "Initializing generation session...")
        sr = TARGET_SR
        job_store.update(job_id, progress=8)

        # ── Main text TTS (will be multi-layer encoded) ────────────
        if not text_main:
            raise ValueError("Affirmation text cannot be empty")

        cache_key = (
            client_session_id,
            text_main,
            tuple(sorted(voices.items())),
            lang_main,
        )
        cached = tts_cache.get(cache_key)
        if cached:
            add_job_log(job_id, "Using cached TTS voice from previous generation...")
            main_audio, sr = cached
        else:
            add_job_log(job_id, "Synthesizing speech via Neural TTS...")
            main_audio, sr = await generate_tts_multilang(text_main, voices, lang_main)
            add_job_log(job_id, "Neural TTS synthesis completed successfully.")
            if client_session_id:
                main_audio.setflags(write=False)
                tts_cache.put(cache_key, (main_audio, sr))
        job_store.raise_if_cancelled(job_id)
        job_store.update(job_id, progress=25)

        def cb(p):
            job_store.update(job_id, progress=p)

        def log_cb(msg):
            add_job_log(job_id, msg)

        loop = asyncio.get_running_loop()
        add_job_log(job_id, "Starting mixdown and encoding...")
        await loop.run_in_executor(
            None,
            mix_final,
            main_audio,
            sr, layers, speed_min, speed_max,
            silence_start, silence_end,
            out, out_raw, out_flac,
            binaural_type, binaural_volume,
            music_type, music_volume,
            music_notch_enabled,
            cb,
            log_cb,
            voice_volume,
            lambda: job_store.raise_if_cancelled(job_id),
            mono_voice,
        )

        job_store.update(job_id, status="done", progress=100)
        add_job_log(job_id, "Generation session completed successfully.")

@app.get("/status/{job_id}")
async def status(job_id: str):
    return job_store.get(job_id) or {"status": "not_found"}


@app.get("/jobs")
async def get_all_jobs():
    return job_store.all()


@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    if job_store.cancel(job_id):
        return {"status": "cancelling"}
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    raise HTTPException(status_code=409, detail=f"Job is already {job['status']}")


@app.get("/download/{job_id}")
async def download(job_id: str):
    job = job_store.get(job_id)
    if job and job.get("output_path"):
        path = Path(job["output_path"])
        if path.exists():
            media = "audio/mpeg" if path.suffix.lower() == ".mp3" else ("audio/flac" if path.suffix.lower() == ".flac" else "audio/wav")
            return FileResponse(
                str(path), media_type=media, filename=path.name
            )
    for ext in (".mp3", ".flac", ".wav"):
        path = OUTPUTS / f"{job_id}{ext}"
        if path.exists():
            media = "audio/mpeg" if ext == ".mp3" else ("audio/flac" if ext == ".flac" else "audio/wav")
            return FileResponse(
                str(path), media_type=media, filename=f"neurocode_{job_id}{ext}"
            )
    return {"error": "not found"}


@app.get("/download_flac/{job_id}")
async def download_flac(job_id: str):
    job = job_store.get(job_id)
    if job and job.get("output_flac_path"):
        path = Path(job["output_flac_path"])
        if path.exists():
            return FileResponse(
                str(path), media_type="audio/flac", filename=path.name
            )
    path = OUTPUTS / f"{job_id}.flac"
    if path.exists():
        return FileResponse(
            str(path), media_type="audio/flac", filename=f"neurocode_{job_id}.flac"
        )
    return {"error": "not found"}


@app.get("/download_raw/{job_id}")
async def download_raw(job_id: str):
    job = job_store.get(job_id)
    if job and job.get("output_raw_path"):
        path = Path(job["output_raw_path"])
        if path.exists():
            media = "audio/mpeg" if path.suffix.lower() == ".mp3" else ("audio/flac" if path.suffix.lower() == ".flac" else "audio/wav")
            return FileResponse(
                str(path), media_type=media, filename=path.name
            )
    for ext in (".mp3", ".flac", ".wav"):
        path = OUTPUTS / f"{job_id}_raw{ext}"
        if path.exists():
            media = "audio/mpeg" if ext == ".mp3" else ("audio/flac" if ext == ".flac" else "audio/wav")
            return FileResponse(
                str(path), media_type=media, filename=f"neurocode_{job_id}_raw{ext}"
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

    def open_external(self, url: str) -> bool:
        allowed = {
            "https://t.me/BotFather",
            "https://t.me/userinfobot",
        }
        if url not in allowed:
            return False
        try:
            import webbrowser
            return bool(webbrowser.open(url))
        except Exception as e:
            print(f"[GUI API ERROR] open_external error: {e}")
            return False


def find_free_port(start_port: int = 7860) -> int:
    import socket
    for p in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start_port


if __name__ == "__main__":
    import sys
    port = find_free_port(7860)

    if "--browser" in sys.argv:
        import threading
        import webbrowser

        def start_server():
            uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

        t = threading.Thread(target=start_server, daemon=True)
        t.start()
        time.sleep(0.4)
        webbrowser.open(f"http://127.0.0.1:{port}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
    else:
        try:
            import threading
            import urllib.request
            import webview

            def start_server():
                try:
                    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
                except Exception as err:
                    print(f"[SERVER ERROR] Could not start server on port {port}: {err}")

            t = threading.Thread(target=start_server, daemon=True)
            t.start()

            # Fast HTTP readiness check (up to 2 seconds max)
            for _ in range(40):
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=0.2) as resp:
                        if resp.status == 200:
                            break
                except Exception:
                    pass
                time.sleep(0.05)

            window = webview.create_window(
                "Neurocode Studio",
                f"http://127.0.0.1:{port}",
                width=1280,
                height=850,
                min_size=(1000, 700),
            )
            window.js_api = GUI_API(window)

            def on_loaded():
                try:
                    window.evaluate_js(
                        "if(!document.body || document.body.children.length === 0) { location.reload(); }"
                    )
                except Exception:
                    pass

            window.events.loaded += on_loaded
            webview.start()

        except Exception as exc:
            print(f"[GUI LAUNCH NOTICE] Launching in default browser: {exc}")
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{port}")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                sys.exit(0)
