"""Streamlit page: generate and show the visit brief."""
import streamlit as st

from prep import store
from prep.brief import NotEnoughNotes, build_brief, load_cached_brief
from prep.llm import LLMError, QuotaError
from prep.models import Claim, VisitBrief
from prep.pdf import brief_to_pdf
from prep.providers import get_llm
from prep.safety import URGENT_MESSAGE

QUOTA_MESSAGE = "Daily AI limit reached. Try the demo patient or try again tomorrow."


def _claims(title: str, claims: list[Claim], by_id: dict) -> None:
    st.subheader(title)
    for c in claims:
        ids = ", ".join(f"#{i}" for i in c.source_ids)
        st.markdown(f"- {c.text}  \n  <small>notes {ids}</small>", unsafe_allow_html=True)
        with st.expander(f"Source notes for: {c.text[:60]}"):
            for i in c.source_ids:
                n = by_id.get(i)
                if n:
                    st.markdown(f"**#{i}** · {n.created_at[:10]}: {n.text}")


def _show(b: VisitBrief, notes) -> None:
    by_id = {n.id: n for n in notes}
    if b.red_flags:
        st.error(URGENT_MESSAGE)
        st.write("Mentioned in your notes: " + ", ".join(b.red_flags))
    st.write(b.summary)
    _claims("Timeline", b.timeline, by_id)
    _claims("Patterns", b.patterns, by_id)
    st.subheader("Questions to ask")
    for i, q in enumerate(b.questions, 1):
        st.write(f"{i}. {q}")
    st.download_button(
        "Download PDF", brief_to_pdf(b), file_name="visit_brief.pdf", mime="application/pdf"
    )


def render(conn) -> None:
    st.header("Visit brief")
    notes = store.list_notes(conn)
    if not notes:
        st.write("Add some notes first, or load the demo patient from the Diary page.")
        return
    if st.button("Prepare my visit"):
        st.session_state.pop("brief", None)
        cached = load_cached_brief(notes)
        if cached:
            st.session_state["brief"] = (cached, "Pre-generated example for the demo patient")
        else:
            try:
                with st.spinner("Preparing your brief…"):
                    b = build_brief(get_llm(), notes, store.get_extractions(conn))
                st.session_state["brief"] = (b, None)
            except NotEnoughNotes as exc:
                st.info(str(exc))
            except QuotaError:
                st.error(QUOTA_MESSAGE)
            except LLMError as exc:
                st.error(str(exc))
    saved = st.session_state.get("brief")
    if saved:
        b, label = saved
        if label:
            st.caption(label)
        _show(b, notes)
