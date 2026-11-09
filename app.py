"""Streamlit entry point: consent gate and page routing."""
import streamlit as st

from pages_ui import add_note, brief, diary
from prep import config, store

CONSENT = (
    "This is a student prototype. Use made-up or your own non-sensitive notes. "
    "Do not enter real patient data. This is not medical advice."
)

PAGES = {"Diary": diary.render, "Add a note": add_note.render, "Visit brief": brief.render}


@st.cache_resource
def get_conn():
    return store.init_db(str(config.repo_path(config.DB_PATH)))


def main() -> None:
    st.set_page_config(page_title="7-Minute Appointment Prep", page_icon="🩺")
    st.title("7-Minute Appointment Prep")
    if not st.session_state.get("consented"):
        st.info(CONSENT)
        if st.button("I understand"):
            st.session_state["consented"] = True
            st.rerun()
        return
    page = st.sidebar.radio("Go to", list(PAGES))
    PAGES[page](get_conn())


main()
