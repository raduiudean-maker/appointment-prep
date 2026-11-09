"""Dataclasses shared across the app."""
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


@dataclass
class Claim:
    text: str
    source_ids: list[int]  # ids of the notes that support this statement


@dataclass
class VisitBrief:
    summary: str  # at most 2 sentences
    timeline: list[Claim]
    patterns: list[Claim]
    questions: list[str]  # exactly 3
    red_flags: list[str]  # from the rule-based check, never from the model
    note_count: int
    date_range: tuple[str, str]
