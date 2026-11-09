import json

import pytest

from prep import store
from prep.ingest import ingest_note
from prep.llm import LLMError, QuotaError

GOOD = json.dumps(
    {"symptoms": ["headache"], "severity": 6, "triggers": [], "medications": [], "sleep_hours": 5}
)


@pytest.fixture
def conn():
    return store.init_db(":memory:")


def test_text_note_is_saved_and_extracted(conn, fake_llm):
    r = ingest_note(conn, fake_llm([GOOD]), text="Headache after screens")
    assert r.note and r.warning is None
    assert store.get_extractions(conn)[r.note.id].severity == 6


def test_red_flag_detected_even_when_ai_is_down(conn, fake_llm):
    r = ingest_note(conn, fake_llm([QuotaError("x")]), text="the worst headache of my life")
    assert r.red_flags and r.note and "extract" in r.warning
    assert len(store.list_notes(conn)) == 1


def test_extraction_failure_keeps_note(conn, fake_llm):
    r = ingest_note(conn, fake_llm([LLMError("bad"), LLMError("bad")]), text="head hurts")
    assert r.note and r.warning
    assert store.get_extractions(conn) == {}


def test_voice_note_is_transcribed(conn, fake_llm):
    r = ingest_note(conn, fake_llm([GOOD], transcript="my head hurts"), audio_bytes=b"x")
    assert r.note.text == "my head hurts" and r.note.source == "voice"


def test_empty_transcript_asks_user_to_type(conn, fake_llm):
    r = ingest_note(conn, fake_llm(transcript=" "), audio_bytes=b"x")
    assert r.needs_typing and r.note is None
    assert store.list_notes(conn) == []


def test_nothing_to_save(conn, fake_llm):
    r = ingest_note(conn, fake_llm(), text="  ")
    assert r.note is None and r.warning


def test_no_llm_still_saves(conn):
    r = ingest_note(conn, None, text="head hurts")
    assert r.note and r.warning
