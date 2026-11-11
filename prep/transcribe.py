"""Audio bytes to text, through the active LLM provider."""
from prep.llm import LLM, QuotaError


class TranscriptionError(Exception):
    """Transcription failed or came back empty. The UI falls back to typing."""


def transcribe(llm: LLM, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    if not audio_bytes:
        raise TranscriptionError("No audio was recorded.")
    try:
        text = llm.transcribe(audio_bytes, mime_type)
    except QuotaError:
        raise
    except Exception as exc:  # includes NotImplementedError from providers without audio
        raise TranscriptionError(str(exc) or "Transcription failed.") from exc
    text = (text or "").strip()
    if not text:
        raise TranscriptionError("The recording had no speech in it.")
    return text
