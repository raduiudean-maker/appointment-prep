import json

import pytest

from prep.brief import (
    BRIEF_SYSTEM,
    MIN_NOTES,
    NotEnoughNotes,
    brief_from_dict,
    brief_to_dict,
    build_brief,
    load_cached_brief,
    save_cached_brief,
)
from prep.models import Claim, Extraction, Note, VisitBrief

PAD_QUESTION = "What should I watch for before my next visit?"


def _notes(n=4, text="headache"):
    return [
        Note(id=i, created_at=f"2026-10-{19 + i - 1}T21:00", text=text, source="seed")
        for i in range(1, n + 1)
    ]


def _answer(**overrides):
    data = {
        "summary": "Recurring headaches.",
        "timeline": [{"text": "Started Monday", "source_ids": [1]}],
        "patterns": [{"text": "Worse after short sleep", "source_ids": [1, 2]}],
        "questions": ["Q1?", "Q2?", "Q3?"],
    }
    data.update(overrides)
    return json.dumps(data)


def test_not_enough_notes_skips_api(fake_llm):
    llm = fake_llm([])

    with pytest.raises(NotEnoughNotes):
        build_brief(llm, _notes(MIN_NOTES - 1), {})

    assert llm.calls == []


def test_drops_unknown_source_ids(fake_llm):
    llm = fake_llm([_answer(patterns=[{"text": "p", "source_ids": [1, 99]}])])

    brief = build_brief(llm, _notes(), {})

    assert brief.patterns == [Claim("p", [1])]


def test_drops_claim_with_no_valid_sources(fake_llm):
    llm = fake_llm([_answer(
        timeline=[{"text": "ghost", "source_ids": [99]}, {"text": "real", "source_ids": [2]}],
        patterns=[{"text": "no sources", "source_ids": []}],
    )])

    brief = build_brief(llm, _notes(), {})

    assert brief.timeline == [Claim("real", [2])]
    assert brief.patterns == []


def test_source_ids_given_as_strings_are_accepted(fake_llm):
    llm = fake_llm([_answer(patterns=[{"text": "p", "source_ids": ["1", "2", "x"]}])])

    assert build_brief(llm, _notes(), {}).patterns == [Claim("p", [1, 2])]


def test_questions_exactly_three(fake_llm):
    many = build_brief(fake_llm([_answer(questions=["a", "b", "c", "d", "e"])]), _notes(), {})
    one = build_brief(fake_llm([_answer(questions=["only one"])]), _notes(), {})

    assert many.questions == ["a", "b", "c"]
    assert one.questions == ["only one", PAD_QUESTION, PAD_QUESTION]


def test_caps_timeline_at_6_and_patterns_at_4(fake_llm):
    claims = [{"text": f"c{i}", "source_ids": [1]} for i in range(8)]
    llm = fake_llm([_answer(timeline=claims, patterns=claims)])

    brief = build_brief(llm, _notes(), {})

    assert len(brief.timeline) == 6
    assert len(brief.patterns) == 4


def test_red_flags_from_rules_not_model(fake_llm):
    notes = _notes()
    notes[1].text = "Worst headache of my life today"
    llm = fake_llm([_answer(red_flags=["made up by the model"])])

    brief = build_brief(llm, notes, {})

    assert brief.red_flags == ["sudden severe headache"]


def test_note_count_and_date_range(fake_llm):
    brief = build_brief(fake_llm([_answer()]), _notes(4), {})

    assert brief.note_count == 4
    assert brief.date_range == ("2026-10-19T21:00", "2026-10-22T21:00")


def test_prompt_has_one_line_per_note_with_id_weekday_and_extraction(fake_llm):
    notes = [
        Note(1, "2026-10-19T21:05", "Monday note", "seed"),
        Note(2, "2026-10-20T21:40", "Tuesday note", "seed"),
        Note(3, "2026-10-21T20:30", "Wednesday note", "seed"),
    ]
    extractions = {2: Extraction(2, ["headache"], 7, ["calls"], ["ibuprofen"], 5.0)}
    llm = fake_llm([_answer()])

    build_brief(llm, notes, extractions)

    lines = llm.calls[0]["user"].splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("[1] 2026-10-19 Mon")
    assert "severity 7" in lines[1] and "sleep 5" in lines[1] and "ibuprofen" in lines[1]
    assert lines[1].endswith("Tuesday note")
    assert llm.calls[0]["task"] == "brief"


def test_brief_system_forbids_diagnosis():
    assert "diagnos" in BRIEF_SYSTEM.lower()
    assert "30 seconds" in BRIEF_SYSTEM


def _brief():
    return VisitBrief(
        summary="s",
        timeline=[Claim("t", [1])],
        patterns=[Claim("p", [1, 2])],
        questions=["a", "b", "c"],
        red_flags=["chest pain"],
        note_count=2,
        date_range=("2026-10-19T21:00", "2026-10-20T21:00"),
    )


def test_brief_dict_roundtrip():
    brief = _brief()

    assert brief_from_dict(json.loads(json.dumps(brief_to_dict(brief)))) == brief


def test_load_cached_brief_missing_file_returns_none(tmp_path):
    assert load_cached_brief(_notes(), str(tmp_path / "nope.json")) is None


def test_cached_brief_is_remapped_to_current_note_ids(tmp_path):
    path = str(tmp_path / "brief.json")
    saved_notes = _notes(2)
    save_cached_brief(_brief(), saved_notes, path)
    # Same notes, but the database gave them different ids this time.
    current = [Note(10, saved_notes[0].created_at, "x", "seed"),
               Note(11, saved_notes[1].created_at, "y", "seed")]

    loaded = load_cached_brief(current, path)

    assert loaded.timeline == [Claim("t", [10])]
    assert loaded.patterns == [Claim("p", [10, 11])]


def test_cached_brief_is_none_when_notes_differ(tmp_path):
    path = str(tmp_path / "brief.json")
    save_cached_brief(_brief(), _notes(2), path)

    extra = _notes(2) + [Note(3, "2026-11-30T09:00", "a new note", "text")]

    assert load_cached_brief(extra, path) is None
    assert load_cached_brief(_notes(2)[:1], path) is None
