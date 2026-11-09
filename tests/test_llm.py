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
