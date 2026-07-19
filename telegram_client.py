import json
from pathlib import Path

import requests


CONFIG_FILE = Path(__file__).resolve().parent / "telegram_config.json"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return {
                "enabled": bool(data.get("enabled", False)),
                "token": str(data.get("token", "")),
                "chat_id": str(data.get("chat_id", "")),
            }
        except Exception as exc:
            print(f"[TG CONFIG ERROR] Read failed: {exc}")
    return {"enabled": False, "token": "", "chat_id": ""}


def save_config(enabled: bool, token: str, chat_id: str) -> None:
    current = load_config()
    config = {
        "enabled": enabled,
        "token": token.strip() or current["token"],
        "chat_id": chat_id.strip(),
    }
    CONFIG_FILE.write_text(
        json.dumps(config, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


def test_connection(token: str, chat_id: str) -> dict:
    response = requests.post(
        f"https://api.telegram.org/bot{token.strip()}/sendMessage",
        data={
            "chat_id": chat_id.strip(),
            "text": (
                "⚡️ *Neurocode Studio*\n\n"
                "Telegram Bot connection test successful!\n"
                "Your bot is ready to receive generated audio files."
            ),
            "parse_mode": "Markdown",
        },
        timeout=10,
    )
    return response.json()


def send_document(token: str, chat_id: str, file_path: str, caption: str = "") -> dict:
    path = Path(file_path)
    if not path.exists():
        return {"ok": False, "error": f"File not found: {file_path}"}
    
    upload_path = path
    temp_compressed_path = None
    
    # Telegram Bot API limit is 50 MB (50 * 1024 * 1024 bytes)
    if path.stat().st_size > 50 * 1024 * 1024:
        import shutil
        import subprocess
        ffmpeg_bin = shutil.which("ffmpeg")
        if ffmpeg_bin:
            try:
                file_size_bytes = path.stat().st_size
                # Estimate duration in seconds (44100 Hz, 16-bit PCM, 2 channels = 176400 bytes/sec)
                duration_sec = max(1.0, file_size_bytes / 176400.0)
                
                # Target max size ~44 MB = 44 * 1024 * 1024 * 8 bits = 369,098,752 bits
                target_bitrate_kbps = int((44 * 1024 * 1024 * 8) / duration_sec / 1000)
                bitrate_kbps = max(96, min(320, target_bitrate_kbps))
                
                clean_name = path.stem
                temp_compressed_path = path.parent / f"{clean_name}_tg_compressed.mp3"
                
                cmd = [
                    ffmpeg_bin, "-y", "-i", str(path),
                    "-b:a", f"{bitrate_kbps}k",
                    "-ac", "2",
                    "-ar", "44100",
                    str(temp_compressed_path)
                ]
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                
                if temp_compressed_path.exists() and temp_compressed_path.stat().st_size <= 50 * 1024 * 1024:
                    upload_path = temp_compressed_path
                    caption += f"\n\n⚡️ _(Converted to High-Quality {bitrate_kbps}k MP3 for Telegram 50MB limit compliance)_"
                elif temp_compressed_path.exists():
                    fallback_path = path.parent / f"{clean_name}_tg_fallback.mp3"
                    cmd_fallback = [
                        ffmpeg_bin, "-y", "-i", str(path),
                        "-b:a", "128k", "-ac", "2", "-ar", "44100",
                        str(fallback_path)
                    ]
                    subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    if fallback_path.exists() and fallback_path.stat().st_size <= 50 * 1024 * 1024:
                        if temp_compressed_path.exists():
                            try:
                                temp_compressed_path.unlink()
                            except Exception:
                                pass
                        upload_path = fallback_path
                        temp_compressed_path = fallback_path
                        caption += "\n\n⚡️ _(Compressed to 128k MP3 to fit Telegram 50MB limit)_"
            except Exception as conv_err:
                print(f"[TG CONVERT ERROR] {conv_err}")

    if upload_path.stat().st_size > 50 * 1024 * 1024:
        size_mb = upload_path.stat().st_size / 1024 / 1024
        return {
            "ok": False,
            "error": f"File size ({size_mb:.1f} MB) exceeds Telegram's 50 MB bot limit.",
        }

    try:
        filename_override = upload_path.name
        if "_tg_compressed" in filename_override or "_tg_fallback" in filename_override:
            clean_stem = path.stem
            filename_override = f"{clean_stem}.mp3"

        with upload_path.open("rb") as handle:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendDocument",
                files={"document": (filename_override, handle)},
                data={
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "Markdown",
                },
                timeout=180,
            )
        return response.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    finally:
        if temp_compressed_path and temp_compressed_path.exists():
            try:
                temp_compressed_path.unlink()
            except Exception:
                pass
