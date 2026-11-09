"""Streamlit page: add a text or voice note."""
import streamlit as st

from prep.ingest import ingest_note
from prep.llm import LLMError, QuotaError
from prep.providers import get_llm
from prep.safety import URGENT_MESSAGE

QUOTA_MESSAGE = "Daily AI limit reached. Try the demo patient or try again tomorrow."


def _llm():
    try:
        return get_llm()
    except LLMError:
        return None


def render(conn) -> None:
    st.header("Add a note")
    st.caption("Describe how you feel today: symptoms, how bad, sleep, medicine, what you did.")
    if st.session_state.pop("typing_needed", False):
        st.warning("Couldn't hear that clearly — please type your note.")
    text = st.text_area("Your note", key="note_text", height=140)
    audio = st.audio_input("Or record it")

    if st.button("Save note"):
        audio_bytes = audio.getvalue() if audio is not None else None
        try:
            with st.spinner("Saving…"):
                result = ingest_note(conn, _llm(), text, audio_bytes)
        except QuotaError:
            st.error(QUOTA_MESSAGE)
            return
        except LLMError as exc:
            st.error(str(exc))
            return
        if result.needs_typing:
            st.session_state["typing_needed"] = True
            st.rerun()
        if result.red_flags:
            st.error(URGENT_MESSAGE)
        if result.note:
            st.success(f"Saved note #{result.note.id}.")
        if result.warning:
            st.warning(result.warning)
