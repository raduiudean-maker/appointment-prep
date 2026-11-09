"""Generate the demo patient's extractions in small, resumable batches (free-tier quota)."""
import time
from dataclasses import asdict
from typing import Callable

from prep.extract import extract_note
from prep.llm import LLM, QuotaError
from prep.models import Note


def precompute_extractions(
    llm: LLM,
    notes: list[dict],
    existing: list[dict],
    max_calls: int,
    save: Callable[[list[dict]], None],
    sleep_s: float = 13.0,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[list[dict], bool]:
    """Extract notes not yet in `existing`, at most `max_calls` of them.

    Saves after every call. Returns (all entries, hit_quota). The pause between calls
    keeps us under the free tier's requests-per-minute limit.
    """
    entries = list(existing)
    done = {e["created_at"] for e in entries}
    calls = 0
    for item in notes:
        if item["created_at"] in done:
            continue
        if calls >= max_calls:
            break
        if calls > 0:
            sleep(sleep_s)
        calls += 1
        note = Note(id=0, created_at=item["created_at"], text=item["text"], source="seed")
        try:
            extraction = extract_note(llm, note)
        except QuotaError:
            return entries, True
        fields = asdict(extraction)
        fields.pop("note_id")
        entries.append({"created_at": item["created_at"], **fields})
        save(entries)
    return entries, False
