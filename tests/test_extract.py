import json

import pytest

from prep.extract import EXTRACT_SYSTEM, extract_note
from prep.models import Extraction, Note


def _note(text="Bad headache, slept 5h, took ibuprofen."):
    return Note(id=7, created_at="2026-11-01T21:00", text=text, source="text")


def test_extract_parses_all_fields(fake_llm):
    llm = fake_llm([json.dumps({
        "symptoms": ["headache"],
        "severity": 7,
        "triggers": ["screen time"],
        "medications": ["ibuprofen"],
        "sleep_hours": 5,
    })])

    ex = extract_note(llm, _note())

    assert ex == Extraction(7, ["headache"], 7, ["screen time"], ["ibuprofen"], 5.0)


def test_extract_clamps_severity(fake_llm):
    llm = fake_llm([json.dumps({"symptoms": [], "severity": 14})])

    assert extract_note(llm, _note()).severity == 10


def test_extract_non_numeric_severity_is_none(fake_llm):
    llm = fake_llm([json.dumps({"symptoms": [], "severity": "pretty bad"})])

    assert extract_note(llm, _note()).severity is None


def test_extract_missing_fields_become_empty(fake_llm):
    llm = fake_llm(["{}"])

    ex = extract_note(llm, _note())

    assert ex == Extraction(7, [], None, [], [], None)


def test_extract_rejects_empty_text_without_calling_the_llm(fake_llm):
    llm = fake_llm([])

    with pytest.raises(ValueError):
        extract_note(llm, _note("   "))

    assert llm.calls == []


def test_extract_sends_note_text_with_extract_task(fake_llm):
    llm = fake_llm(["{}"])

    extract_note(llm, _note("my note"))

    assert llm.calls[0]["task"] == "extract"
    assert llm.calls[0]["user"] == "my note"
    assert llm.calls[0]["system"] == EXTRACT_SYSTEM


def test_extract_system_forbids_diagnosis():
    assert "diagnosis" in EXTRACT_SYSTEM.lower()
