import pytest


class FakeLLM:
    """Stands in for a real provider. Responses are returned in order; an Exception is raised."""

    def __init__(self, responses=None, transcript="a spoken note"):
        self._responses = list(responses or [])
        self.transcript = transcript
        self.calls: list[dict] = []

    def complete(self, system, user, max_tokens=1500, task="extract"):
        self.calls.append({"system": system, "user": user, "task": task})
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def transcribe(self, audio_bytes, mime_type="audio/wav"):
        return self.transcript


@pytest.fixture
def fake_llm():
    """The FakeLLM class, so a test can build one with its own responses."""
    return FakeLLM
