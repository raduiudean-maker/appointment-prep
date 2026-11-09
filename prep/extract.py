"""Turn one diary note into structured fields with the LLM."""
from prep.llm import LLM, ask_json
from prep.models import Extraction, Note

EXTRACT_SYSTEM = (
    "You read one short symptom-diary note written by a patient and extract fields from it. "
    "Return only a JSON object with exactly these keys: "
    "symptoms (list of strings, in the patient's own words), "
    "severity (integer 0-10, or null), "
    "triggers (list of strings), "
    "medications (list of strings), "
    "sleep_hours (number of hours slept the night before, or null). "
    "Use null when the note does not say. "
    "Do not infer a diagnosis. Do not add anything the note does not state."
)


def _as_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _as_number(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def extract_note(llm: LLM, note: Note) -> Extraction:
    if not note.text.strip():
        raise ValueError("Cannot extract from an empty note.")
    data = ask_json(llm, EXTRACT_SYSTEM, note.text, task="extract")

    severity = _as_number(data.get("severity"))
    if severity is not None:
        severity = max(0, min(10, round(severity)))
    sleep_hours = _as_number(data.get("sleep_hours"))
    if sleep_hours is not None and not 0 <= sleep_hours <= 24:
        sleep_hours = None

    return Extraction(
        note_id=note.id,
        symptoms=_as_list(data.get("symptoms")),
        severity=severity,
        triggers=_as_list(data.get("triggers")),
        medications=_as_list(data.get("medications")),
        sleep_hours=sleep_hours,
    )
