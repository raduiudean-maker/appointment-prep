"""SQLite storage for notes and their extracted fields."""
import json
import sqlite3
from datetime import datetime

from prep.models import Extraction, Note

_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    text TEXT NOT NULL,
    source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS extractions (
    note_id INTEGER PRIMARY KEY REFERENCES notes(id),
    symptoms TEXT NOT NULL,
    severity INTEGER,
    triggers TEXT NOT NULL,
    medications TEXT NOT NULL,
    sleep_hours REAL
);
"""


def init_db(path: str) -> sqlite3.Connection:
    # check_same_thread=False because Streamlit runs each rerun in a worker thread.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    return conn


def add_note(
    conn: sqlite3.Connection, text: str, source: str, created_at: str | None = None
) -> Note:
    created_at = created_at or datetime.now().isoformat(timespec="minutes")
    cur = conn.execute(
        "INSERT INTO notes (created_at, text, source) VALUES (?, ?, ?)",
        (created_at, text, source),
    )
    conn.commit()
    return Note(id=cur.lastrowid, created_at=created_at, text=text, source=source)


def list_notes(conn: sqlite3.Connection) -> list[Note]:
    rows = conn.execute(
        "SELECT id, created_at, text, source FROM notes ORDER BY created_at, id"
    ).fetchall()
    return [Note(id=r[0], created_at=r[1], text=r[2], source=r[3]) for r in rows]


def save_extraction(conn: sqlite3.Connection, ex: Extraction) -> None:
    conn.execute(
        """
        INSERT INTO extractions
            (note_id, symptoms, severity, triggers, medications, sleep_hours)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(note_id) DO UPDATE SET
            symptoms = excluded.symptoms,
            severity = excluded.severity,
            triggers = excluded.triggers,
            medications = excluded.medications,
            sleep_hours = excluded.sleep_hours
        """,
        (
            ex.note_id,
            json.dumps(ex.symptoms),
            ex.severity,
            json.dumps(ex.triggers),
            json.dumps(ex.medications),
            ex.sleep_hours,
        ),
    )
    conn.commit()


def get_extractions(conn: sqlite3.Connection) -> dict[int, Extraction]:
    rows = conn.execute(
        "SELECT note_id, symptoms, severity, triggers, medications, sleep_hours "
        "FROM extractions"
    ).fetchall()
    return {
        r[0]: Extraction(
            note_id=r[0],
            symptoms=json.loads(r[1]),
            severity=r[2],
            triggers=json.loads(r[3]),
            medications=json.loads(r[4]),
            sleep_hours=r[5],
        )
        for r in rows
    }
