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
    if path.stat().st_size > 50 * 1024 * 1024:
        size_mb = path.stat().st_size / 1024 / 1024
        return {
            "ok": False,
            "error": f"File size ({size_mb:.1f} MB) exceeds Telegram's 50 MB bot limit.",
        }
    try:
        with path.open("rb") as handle:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendDocument",
                files={"document": (path.name, handle)},
                data={
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "Markdown",
                },
                timeout=120,
            )
        return response.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
