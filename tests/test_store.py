from prep.models import Extraction
from prep.store import add_note, get_extractions, init_db, list_notes, save_extraction


def test_add_and_list_notes_oldest_first():
    conn = init_db(":memory:")
    add_note(conn, "second", "text", created_at="2026-11-02T08:00")
    add_note(conn, "first", "voice", created_at="2026-11-01T08:00")

    notes = list_notes(conn)

    assert [n.text for n in notes] == ["first", "second"]
    assert [n.created_at for n in notes] == ["2026-11-01T08:00", "2026-11-02T08:00"]
    assert notes[0].source == "voice"
    assert all(isinstance(n.id, int) for n in notes)


def test_save_extraction_roundtrip():
    conn = init_db(":memory:")
    note = add_note(conn, "bad headache, slept 5h", "text", created_at="2026-11-01T08:00")
    ex = Extraction(
        note_id=note.id,
        symptoms=["headache", "blurry vision"],
        severity=7,
        triggers=["screen time"],
        medications=["ibuprofen"],
        sleep_hours=5.0,
    )

    save_extraction(conn, ex)

    assert get_extractions(conn) == {note.id: ex}


def test_save_extraction_upserts():
    conn = init_db(":memory:")
    note = add_note(conn, "headache", "text", created_at="2026-11-01T08:00")
    first = Extraction(note.id, ["headache"], 3, [], [], None)
    second = Extraction(note.id, ["headache", "nausea"], 6, ["noise"], [], 7.5)

    save_extraction(conn, first)
    save_extraction(conn, second)

    rows = conn.execute("SELECT COUNT(*) FROM extractions").fetchone()[0]
    assert rows == 1
    assert get_extractions(conn)[note.id] == second
