"""Turn a patient's notes into a one-page visit brief, with every claim traced to its notes."""
import json
from datetime import datetime

from prep import config
from prep.llm import LLM, ask_json
from prep.models import Claim, Extraction, Note, VisitBrief
from prep.safety import red_flags

MIN_NOTES = 3
MAX_TIMELINE = 6
MAX_PATTERNS = 4
PAD_QUESTION = "What should I watch for before my next visit?"


class NotEnoughNotes(Exception):
    """Fewer than MIN_NOTES notes, so there is nothing meaningful to summarise."""


BRIEF_SYSTEM = (
    "You prepare a one-page visit brief for a doctor from a patient's symptom diary. "
    "The doctor has 30 seconds, so be short and concrete. "
    "Each diary line looks like: [id] date weekday | severity | sleep | medications | "
    "symptoms | the patient's own words. "
    "Return only a JSON object with exactly these keys: "
    "summary (at most 2 sentences), "
    f"timeline (a list of at most {MAX_TIMELINE} objects with keys text and source_ids), "
    f"patterns (a list of at most {MAX_PATTERNS} objects with keys text and source_ids), "
    "questions (a list of exactly 3 strings: questions the patient could ask the doctor). "
    "source_ids are the [id] numbers of the diary lines that support a statement. "
    "Only state a pattern if at least 2 diary lines support it, and cite their ids. "
    "Count carefully whenever you give a number. "
    "Describe only what the patient reported. "
    "Do not diagnose, and do not suggest treatment or medication changes."
)


def _line(note: Note, ex: Extraction | None) -> str:
    when = datetime.fromisoformat(note.created_at)
    severity = f"severity {ex.severity}" if ex and ex.severity is not None else "severity n/a"
    sleep = f"sleep {ex.sleep_hours:g}h" if ex and ex.sleep_hours is not None else "sleep n/a"
    meds = ", ".join(ex.medications) if ex and ex.medications else "no medication"
    symptoms = ", ".join(ex.symptoms) if ex and ex.symptoms else "-"
    stamp = f"{when:%Y-%m-%d} {when:%a}"
    return f"[{note.id}] {stamp} | {severity} | {sleep} | {meds} | {symptoms} | {note.text}"


def _clean_claims(items, valid_ids: set[int], cap: int) -> list[Claim]:
    """Keep claims that cite at least one real note. Drop invented ids and unsourced claims."""
    claims: list[Claim] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not str(item.get("text", "")).strip():
            continue
        ids: list[int] = []
        for raw in item.get("source_ids") or []:
            try:
                note_id = int(raw)
            except (TypeError, ValueError):
                continue
            if note_id in valid_ids and note_id not in ids:
                ids.append(note_id)
        if ids:
            claims.append(Claim(str(item["text"]).strip(), ids))
    return claims[:cap]


def _clean_questions(items) -> list[str]:
    questions = [str(q).strip() for q in items if str(q).strip()] if isinstance(items, list) else []
    questions = questions[:3]
    return questions + [PAD_QUESTION] * (3 - len(questions))


def _all_red_flags(notes: list[Note]) -> list[str]:
    found: list[str] = []
    for note in notes:
        for flag in red_flags(note.text):
            if flag not in found:
                found.append(flag)
    return found


def build_brief(llm: LLM, notes: list[Note], extractions: dict[int, Extraction]) -> VisitBrief:
    if len(notes) < MIN_NOTES:
        raise NotEnoughNotes(f"Add at least {MIN_NOTES} notes to prepare a visit brief.")
    prompt = "\n".join(_line(n, extractions.get(n.id)) for n in notes)
    data = ask_json(llm, BRIEF_SYSTEM, prompt, task="brief", max_tokens=2500)
    valid_ids = {n.id for n in notes}
    dates = sorted(n.created_at for n in notes)
    return VisitBrief(
        summary=str(data.get("summary", "")).strip(),
        timeline=_clean_claims(data.get("timeline"), valid_ids, MAX_TIMELINE),
        patterns=_clean_claims(data.get("patterns"), valid_ids, MAX_PATTERNS),
        questions=_clean_questions(data.get("questions")),
        red_flags=_all_red_flags(notes),
        note_count=len(notes),
        date_range=(dates[0], dates[-1]),
    )


def brief_to_dict(brief: VisitBrief) -> dict:
    return {
        "summary": brief.summary,
        "timeline": [{"text": c.text, "source_ids": c.source_ids} for c in brief.timeline],
        "patterns": [{"text": c.text, "source_ids": c.source_ids} for c in brief.patterns],
        "questions": list(brief.questions),
        "red_flags": list(brief.red_flags),
        "note_count": brief.note_count,
        "date_range": list(brief.date_range),
    }


def brief_from_dict(data: dict) -> VisitBrief:
    return VisitBrief(
        summary=data["summary"],
        timeline=[Claim(c["text"], list(c["source_ids"])) for c in data["timeline"]],
        patterns=[Claim(c["text"], list(c["source_ids"])) for c in data["patterns"]],
        questions=list(data["questions"]),
        red_flags=list(data["red_flags"]),
        note_count=data["note_count"],
        date_range=(data["date_range"][0], data["date_range"][1]),
    )


def save_cached_brief(
    brief: VisitBrief, notes: list[Note], path: str = config.DEMO_BRIEF_PATH
) -> None:
    """Save a brief with each note's date, so its source ids can be re-mapped on load."""
    payload = {
        "brief": brief_to_dict(brief),
        "note_dates": {str(n.id): n.created_at for n in notes},
    }
    config.repo_path(path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def load_cached_brief(notes: list[Note], path: str = config.DEMO_BRIEF_PATH) -> VisitBrief | None:
    """Return the saved brief only if it was made from exactly these notes, else None.

    The database may number the notes differently than when the brief was saved, so source ids
    are re-mapped through each note's created_at.
    """
    p = config.repo_path(path)
    if not p.exists():
        return None
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
        saved_dates = {int(k): v for k, v in payload["note_dates"].items()}
        if set(saved_dates.values()) != {n.created_at for n in notes}:
            return None
        id_by_date = {n.created_at: n.id for n in notes}
        remap = {old: id_by_date[date] for old, date in saved_dates.items()}
        brief = brief_from_dict(payload["brief"])
        for claim in brief.timeline + brief.patterns:
            claim.source_ids = [remap[i] for i in claim.source_ids]
        return brief
    except (KeyError, ValueError, TypeError):
        return None
