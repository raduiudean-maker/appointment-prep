import json

from prep.llm import QuotaError
from prep.precompute import precompute_extractions

NOTES = [
    {"created_at": f"2026-10-{19 + i}T21:00", "text": f"note {i}"} for i in range(5)
]
EXTRACTION = json.dumps({"symptoms": ["headache"], "severity": 5})


def _run(llm, existing=(), max_calls=15, saved=None, sleeps=None):
    saved = saved if saved is not None else []
    sleeps = sleeps if sleeps is not None else []
    return precompute_extractions(
        llm, NOTES, list(existing), max_calls,
        save=lambda entries: saved.append(list(entries)),
        sleep_s=13.0, sleep=sleeps.append,
    )


def test_precompute_skips_existing_and_respects_max(fake_llm):
    existing = [{"created_at": NOTES[0]["created_at"], "symptoms": [], "severity": 1,
                 "triggers": [], "medications": [], "sleep_hours": None}]
    llm = fake_llm([EXTRACTION, EXTRACTION])

    entries, hit_quota = _run(llm, existing, max_calls=2)

    assert hit_quota is False
    assert len(llm.calls) == 2
    assert [e["created_at"] for e in entries] == [n["created_at"] for n in NOTES[:3]]
    assert "note_id" not in entries[-1]
    assert entries[-1]["severity"] == 5


def test_precompute_saves_after_every_call(fake_llm):
    saved = []

    _run(fake_llm([EXTRACTION] * 3), max_calls=3, saved=saved)

    assert [len(s) for s in saved] == [1, 2, 3]


def test_precompute_stops_cleanly_on_quota(fake_llm):
    llm = fake_llm([EXTRACTION, QuotaError("daily limit")])

    entries, hit_quota = _run(llm)

    assert hit_quota is True
    assert len(entries) == 1
    assert len(llm.calls) == 2


def test_precompute_sleeps_between_calls_only(fake_llm):
    sleeps = []

    _run(fake_llm([EXTRACTION] * 3), max_calls=3, sleeps=sleeps)

    assert sleeps == [13.0, 13.0]
