"""
Device token storage for push notifications. Same hybrid pattern as
storage.py and feedback.py: Postgres when DATABASE_URL is set, local JSON
otherwise (fine for local dev, not for Render - same reasoning as reports).
"""
import json
from pathlib import Path

from backend.db import is_postgres_configured
from backend.paths import get_data_dir

DEFAULT_DEVICES_FILE = Path(get_data_dir()) / "device_tokens.json"


def save_device_token(token: str, platform: str = "android", path: Path = DEFAULT_DEVICES_FILE) -> None:
    if is_postgres_configured():
        from backend.postgres_storage import save_device_token_db
        save_device_token_db(token, platform)
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    tokens = {}
    if path.exists():
        tokens = json.loads(path.read_text(encoding="utf-8"))
    tokens[token] = platform
    path.write_text(json.dumps(tokens, indent=2), encoding="utf-8")


def list_device_tokens(path: Path = DEFAULT_DEVICES_FILE) -> list[str]:
    if is_postgres_configured():
        from backend.postgres_storage import list_device_tokens_db
        return list_device_tokens_db()

    if not path.exists():
        return []
    tokens = json.loads(path.read_text(encoding="utf-8"))
    return list(tokens.keys())
