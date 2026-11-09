import json
from datetime import date

from prep.seed import load_demo
from prep.store import init_db, list_notes

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
