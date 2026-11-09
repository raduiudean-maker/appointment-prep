import json
from datetime import date

from prep.seed import load_demo, load_extractions
from prep.store import add_note, get_extractions, init_db, list_notes

DEMO_PATH = "data/demo_patient.json"


def test_load_demo_inserts_21():
    conn = init_db(":memory:")

    inserted = load_demo(conn)

    assert inserted == 21
    notes = list_notes(conn)
    assert len(notes) == 21
    assert {n.source for n in notes} == {"seed"}


def test_load_demo_is_idempotent():
    conn = init_db(":memory:")

    load_demo(conn)
    second = load_demo(conn)

    assert second == 0
    assert len(list_notes(conn)) == 21


def test_demo_notes_cover_21_consecutive_days():
    with open(DEMO_PATH, encoding="utf-8") as f:
        notes = json.load(f)

    days = [date.fromisoformat(n["created_at"][:10]) for n in notes]

    assert days == sorted(days)
    assert (days[-1] - days[0]).days == 20
    assert len(set(days)) == 21


def test_demo_notes_mention_ibuprofen_in_exactly_9_notes():
    with open(DEMO_PATH, encoding="utf-8") as f:
        notes = json.load(f)

    assert sum("ibuprofen" in n["text"].lower() for n in notes) == 9


def _write_extractions(tmp_path, entries):
    path = tmp_path / "extractions.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    return str(path)


def _seed_two_notes(conn):
    add_note(conn, "first", "seed", created_at="2026-10-19T21:05")
    add_note(conn, "second", "seed", created_at="2026-10-20T21:40")


def test_load_extractions_attaches_by_created_at(tmp_path):
    conn = init_db(":memory:")
    _seed_two_notes(conn)
    path = _write_extractions(tmp_path, [
        {"created_at": "2026-10-20T21:40", "symptoms": ["headache"], "severity": 7,
         "triggers": ["calls"], "medications": ["ibuprofen"], "sleep_hours": 5.0},
        {"created_at": "2026-10-19T21:05", "symptoms": ["headache"], "severity": 6,
         "triggers": [], "medications": [], "sleep_hours": 6.5},
    ])

    attached = load_extractions(conn, path)

    by_text = {n.text: n.id for n in list_notes(conn)}
    extractions = get_extractions(conn)
    assert attached == 2
    assert extractions[by_text["second"]].severity == 7
    assert extractions[by_text["first"]].sleep_hours == 6.5


def test_load_extractions_is_idempotent(tmp_path):
    conn = init_db(":memory:")
    _seed_two_notes(conn)
    path = _write_extractions(tmp_path, [
        {"created_at": "2026-10-19T21:05", "symptoms": [], "severity": 6,
         "triggers": [], "medications": [], "sleep_hours": None},
    ])

    load_extractions(conn, path)
    load_extractions(conn, path)

    assert len(get_extractions(conn)) == 1


def test_load_extractions_skips_unknown_created_at(tmp_path):
    conn = init_db(":memory:")
    _seed_two_notes(conn)
    path = _write_extractions(tmp_path, [
        {"created_at": "1999-01-01T00:00", "symptoms": [], "severity": 1,
         "triggers": [], "medications": [], "sleep_hours": None},
    ])

    assert load_extractions(conn, path) == 0
