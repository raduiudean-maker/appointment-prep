"""Dataclasses shared across the app. Claim and VisitBrief are added in Task 5."""
from dataclasses import dataclass, field
from typing import Literal

NoteSource = Literal["text", "voice", "seed"]


@dataclass
class Note:
    id: int | None
    created_at: str  # ISO 8601, e.g. "2026-11-01T08:00"
    text: str
    source: NoteSource


@dataclass
class Extraction:
    note_id: int
    symptoms: list[str] = field(default_factory=list)
    severity: int | None = None  # 0-10
    triggers: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    sleep_hours: float | None = None
