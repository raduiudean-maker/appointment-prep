"""Gemini and Claude implementations of the LLM interface, and get_llm()."""
import os
import tomllib
from pathlib import Path

from prep import config
from prep.llm import LLM, LLMError, QuotaError, Task

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _raise_mapped(provider: str, exc: Exception) -> None:
    status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if status == 429 or "RESOURCE_EXHAUSTED" in str(exc):
        raise QuotaError("Daily AI limit reached.") from exc
    raise LLMError(f"{provider} call failed: {exc}") from exc


class GeminiLLM:
    def __init__(self, api_key: str, model: str, client=None):
        if client is None:
            from google import genai

            client = genai.Client(api_key=api_key)
        self._client = client
        self._model = model

    def complete(
        self, system: str, user: str, max_tokens: int = 1500, task: Task = "extract"
    ) -> str:
        from google.genai import types

        # max_tokens is deliberately not sent: on thinking models the cap also counts the
        # model's hidden reasoning, which can leave an empty answer.
        settings = types.GenerateContentConfig(
            system_instruction=system, response_mime_type="application/json"
        )
        try:
            response = self._client.models.generate_content(
                model=self._model, contents=user, config=settings
            )
        except Exception as exc:
            _raise_mapped("Gemini", exc)
        return response.text or ""

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        from google.genai import types

        audio = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=["Transcribe this voice note verbatim. Return only the text.", audio],
            )
        except Exception as exc:
            _raise_mapped("Gemini", exc)
        return (response.text or "").strip()


class ClaudeLLM:
    def __init__(self, api_key: str, client=None):
        if client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise LLMError("Install the anthropic package to use the Claude provider.") from exc
            client = anthropic.Anthropic(api_key=api_key)
        self._client = client

    def complete(
        self, system: str, user: str, max_tokens: int = 1500, task: Task = "extract"
    ) -> str:
        model = config.CLAUDE_BRIEF_MODEL if task == "brief" else config.CLAUDE_EXTRACT_MODEL
        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:
            _raise_mapped("Claude", exc)
        return response.content[0].text

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        raise NotImplementedError("Claude cannot transcribe audio. Type the note instead.")


def _secret(name: str) -> str | None:
    """Look in the environment, then Streamlit secrets, then .streamlit/secrets.toml."""
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st

        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    path = _REPO_ROOT / ".streamlit" / "secrets.toml"
    if path.exists():
        value = tomllib.loads(path.read_text(encoding="utf-8")).get(name)
        if value:
            return str(value)
    return None


def get_llm() -> LLM:
    if config.PROVIDER == "gemini":
        key = _secret("GEMINI_API_KEY")
        if not key:
            raise LLMError("GEMINI_API_KEY not found. Put it in .streamlit/secrets.toml.")
        if not config.GEMINI_MODEL:
            raise LLMError("Set GEMINI_MODEL in prep/config.py.")
        return GeminiLLM(key, config.GEMINI_MODEL)
    if config.PROVIDER == "claude":
        key = _secret("ANTHROPIC_API_KEY")
        if not key:
            raise LLMError("ANTHROPIC_API_KEY not found. Put it in .streamlit/secrets.toml.")
        return ClaudeLLM(key)
    raise LLMError(f"Unknown PROVIDER: {config.PROVIDER!r}")
