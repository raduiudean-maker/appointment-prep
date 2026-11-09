"""Load the synthetic demo patient ("Ana") into the database."""
import json
import sqlite3
from prep import config
from prep.models import Extraction
from prep.store import add_note, save_extraction

def load_demo(conn: sqlite3.Connection, path: str = config.DEMO_PATIENT_PATH) -> int:
    """Insert the demo notes. Returns how many were inserted (0 if already loaded)."""
    already = conn.execute("SELECT COUNT(*) FROM notes WHERE source = 'seed'").fetchone()[0]
    if already:
        return 0
    with open(config.repo_path(path), encoding="utf-8") as f:
        entries = json.load(f)
    for entry in entries:
        add_note(conn, entry["text"], "seed", created_at=entry["created_at"])
    return len(entries)


def load_extractions(conn: sqlite3.Connection, path: str = config.DEMO_EXTRACTIONS_PATH) -> int:
    """Attach precomputed extractions to the seeded notes with the same created_at.

    Returns how many were attached. Safe to call again: it overwrites with the same values.
    """
    p = config.repo_path(path)
    if not p.exists():
        return 0
    entries = json.loads(p.read_text(encoding="utf-8"))
    note_ids = dict(
        conn.execute("SELECT created_at, id FROM notes WHERE source = 'seed'").fetchall()
    )
    attached = 0
    for entry in entries:
        note_id = note_ids.get(entry["created_at"])
        if note_id is None:
            continue
        save_extraction(
            conn,
            Extraction(
                note_id=note_id,
                symptoms=list(entry.get("symptoms", [])),
                severity=entry.get("severity"),
                triggers=list(entry.get("triggers", [])),
                medications=list(entry.get("medications", [])),
                sleep_hours=entry.get("sleep_hours"),
            ),
        )
        attached += 1
    return attached
