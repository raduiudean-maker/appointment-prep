"""The LLM interface every provider implements, plus JSON parsing with one retry."""
import json
import re
from typing import Literal, Protocol

Task = Literal["extract", "brief"]


class LLMError(Exception):
    """The model could not give a usable answer."""


class QuotaError(LLMError):
    """The API reports a rate limit or exhausted quota. Never retried."""


class LLM(Protocol):
    def complete(
        self, system: str, user: str, max_tokens: int = 1500, task: Task = "extract"
    ) -> str: ...

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str: ...


_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)


def _parse_object(text: str) -> dict:
    text = text.strip()
    fenced = _FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    data = json.loads(text)  # json.JSONDecodeError is a ValueError
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    return data


def ask_json(
    llm: LLM, system: str, user: str, task: Task = "extract", max_tokens: int = 1500
) -> dict:
    """Ask for a JSON object. One retry on bad JSON; a QuotaError is passed straight through."""
    text = llm.complete(system, user, max_tokens=max_tokens, task=task)
    try:
        return _parse_object(text)
    except ValueError:
        pass
    text = llm.complete(
        system, f"{user}\n\nReturn only valid JSON.", max_tokens=max_tokens, task=task
    )
    try:
        return _parse_object(text)
    except ValueError as exc:
        raise LLMError("The model did not return valid JSON.") from exc
