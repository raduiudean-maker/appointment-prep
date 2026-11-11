import pytest
from google.genai import errors

from prep import config
from prep.llm import LLMError, QuotaError, ask_json
from prep.providers import ClaudeLLM, GeminiLLM


def test_ask_json_strips_fences(fake_llm):
    llm = fake_llm(['```json\n{"a": 1}\n```'])

    assert ask_json(llm, "sys", "usr") == {"a": 1}


def test_ask_json_retries_once_then_succeeds(fake_llm):
    llm = fake_llm(["oops", '{"a": 1}'])

    result = ask_json(llm, "sys", "usr")

    assert result == {"a": 1}
    assert len(llm.calls) == 2
    assert llm.calls[1]["user"].endswith("Return only valid JSON.")


def test_ask_json_raises_after_two_failures(fake_llm):
    llm = fake_llm(["oops", "still not json"])

    with pytest.raises(LLMError):
        ask_json(llm, "sys", "usr")

    assert len(llm.calls) == 2


def test_ask_json_non_object_counts_as_failure(fake_llm):
    llm = fake_llm(["[1, 2]", "[3]"])

    with pytest.raises(LLMError):
        ask_json(llm, "sys", "usr")


def test_quota_error_is_not_retried(fake_llm):
    llm = fake_llm([QuotaError("daily limit")])

    with pytest.raises(QuotaError):
        ask_json(llm, "sys", "usr")

    assert len(llm.calls) == 1


class _GeminiResponse:
    text = '{"a": 1}'


class _GeminiModels:
    def __init__(self, error=None):
        self.error = error
        self.kwargs = None

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return _GeminiResponse()


class _GeminiClient:
    def __init__(self, error=None):
        self.models = _GeminiModels(error)


def test_gemini_complete_returns_text_and_uses_configured_model():
    client = _GeminiClient()
    llm = GeminiLLM("key", "my-model", client=client)

    text = llm.complete("be brief", "hello")

    assert text == '{"a": 1}'
    assert client.models.kwargs["model"] == "my-model"
    assert client.models.kwargs["config"].system_instruction == "be brief"


def test_gemini_maps_429_to_quota_error():
    error = errors.ClientError(
        429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}}
    )
    llm = GeminiLLM("key", "my-model", client=_GeminiClient(error))

    with pytest.raises(QuotaError):
        llm.complete("sys", "usr")


class _ClaudeBlock:
    text = '{"a": 1}'


class _ClaudeResponse:
    content = [_ClaudeBlock()]


class _ClaudeMessages:
    def __init__(self):
        self.kwargs = []

    def create(self, **kwargs):
        self.kwargs.append(kwargs)
        return _ClaudeResponse()


class _ClaudeClient:
    def __init__(self):
        self.messages = _ClaudeMessages()


def test_claude_picks_model_by_task():
    client = _ClaudeClient()
    llm = ClaudeLLM("key", client=client)

    llm.complete("sys", "usr", task="extract")
    llm.complete("sys", "usr", task="brief")

    models = [kw["model"] for kw in client.messages.kwargs]
    assert models == [config.CLAUDE_EXTRACT_MODEL, config.CLAUDE_BRIEF_MODEL]


class _FlakyModels:
    """Raises each queued error in turn, then answers normally."""

    def __init__(self, errors):
        self.errors = list(errors)
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return _GeminiResponse()


class _FlakyClient:
    def __init__(self, errors):
        self.models = _FlakyModels(errors)


def _busy():
    return errors.ServerError(
        503, {"error": {"code": 503, "message": "high demand", "status": "UNAVAILABLE"}}
    )


def test_gemini_retries_when_busy_then_succeeds():
    client = _FlakyClient([_busy(), _busy()])
    waits = []
    llm = GeminiLLM("key", "m", client=client, sleep=waits.append)

    assert llm.complete("sys", "usr") == '{"a": 1}'
    assert client.models.calls == 3
    assert waits == [2.0, 6.0]


def test_gemini_gives_up_after_three_busy_errors():
    client = _FlakyClient([_busy(), _busy(), _busy()])
    llm = GeminiLLM("key", "m", client=client, sleep=lambda s: None)

    with pytest.raises(LLMError) as caught:
        llm.complete("sys", "usr")

    assert not isinstance(caught.value, QuotaError)
    assert "busy" in str(caught.value).lower()
    assert client.models.calls == 3


def test_gemini_does_not_retry_quota_or_other_errors():
    quota = errors.ClientError(
        429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}}
    )
    missing = errors.ClientError(
        404, {"error": {"code": 404, "message": "no such model", "status": "NOT_FOUND"}}
    )
    for error, expected in [(quota, QuotaError), (missing, LLMError)]:
        client = _FlakyClient([error])
        llm = GeminiLLM("key", "m", client=client, sleep=lambda s: None)

        with pytest.raises(expected):
            llm.complete("sys", "usr")

        assert client.models.calls == 1


def test_gemini_thinking_level_is_sent_only_when_configured(monkeypatch):
    from prep import config

    client = _GeminiClient()
    llm = GeminiLLM("key", "m", client=client)
    llm.complete("s", "u")
    assert client.models.kwargs["config"].thinking_config is None

    monkeypatch.setattr(config, "GEMINI_THINKING_LEVEL", "low")
    llm.complete("s", "u")
    assert str(client.models.kwargs["config"].thinking_config.thinking_level).endswith("LOW")
