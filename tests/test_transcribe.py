import pytest

from prep.transcribe import TranscriptionError, transcribe


def test_transcribe_strips_text(fake_llm):
    assert transcribe(fake_llm(transcript="  my head hurts \n"), b"audio") == "my head hurts"


def test_transcribe_empty_raises(fake_llm):
    with pytest.raises(TranscriptionError):
        transcribe(fake_llm(transcript="  "), b"audio")


def test_transcribe_wraps_any_error(fake_llm):
    llm = fake_llm()

    def boom(audio_bytes, mime_type="audio/wav"):
        raise NotImplementedError

    llm.transcribe = boom
    with pytest.raises(TranscriptionError):
        transcribe(llm, b"audio")


def test_transcribe_no_audio_raises(fake_llm):
    with pytest.raises(TranscriptionError):
        transcribe(fake_llm(), b"")
