"""Load the synthetic demo patient ("Ana") into the database."""
import json
import sqlite3
from pathlib import Path

from prep import config
from prep.store import add_note

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else _REPO_ROOT / p


def load_demo(conn: sqlite3.Connection, path: str = config.DEMO_PATIENT_PATH) -> int:
    """Insert the demo notes. Returns how many were inserted (0 if already loaded)."""
    already = conn.execute("SELECT COUNT(*) FROM notes WHERE source = 'seed'").fetchone()[0]
    if already:
        return 0
    with open(_resolve(path), encoding="utf-8") as f:
        entries = json.load(f)
    for entry in entries:
        add_note(conn, entry["text"], "seed", created_at=entry["created_at"])
    return len(entries)
