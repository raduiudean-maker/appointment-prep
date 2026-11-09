"""Save one new note: safety check, optional transcription, store, extract."""
import sqlite3
from dataclasses import dataclass, field

from prep import store
from prep.extract import extract_note
from prep.llm import LLM, LLMError
from prep.models import Note
from prep.safety import red_flags
from prep.transcribe import transcribe


@dataclass
class IngestResult:
    note: Note | None = None
    red_flags: list[str] = field(default_factory=list)
    warning: str | None = None  # note saved, but something went wrong
    needs_typing: bool = False  # transcription failed, ask the user to type


def ingest_note(
    conn: sqlite3.Connection,
    llm: LLM | None,
    text: str = "",
    audio_bytes: bytes | None = None,
) -> IngestResult:
    """llm may be None when no key is configured: the note is then saved as raw text."""
    result = IngestResult()
    text = text.strip()
    source = "text"
    if not text and audio_bytes:
        if llm is None:
            result.needs_typing = True
            return result
        try:
            text = transcribe(llm, audio_bytes)
            source = "voice"
        except LLMError:
            raise
        except Exception:
            result.needs_typing = True
            return result
    if not text:
        result.warning = "Write or record something first."
        return result
    # The safety check runs on the text before any AI call, so it works even if the API is down.
    result.red_flags = red_flags(text)
    note = store.add_note(conn, text, source)
    result.note = note
    if llm is None:
        result.warning = "Saved, but no AI key is set, so details were not extracted."
        return result
    try:
        store.save_extraction(conn, extract_note(llm, note))
    except LLMError as exc:
        result.warning = f"Saved, but couldn't extract details: {exc}"
    except Exception:
        result.warning = "Saved, but couldn't extract details from this note."
    return result
