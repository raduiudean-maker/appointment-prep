"""Streamlit page: diary and severity chart."""
import pandas as pd
import streamlit as st

from prep import seed, store
from prep.safety import URGENT_MESSAGE, red_flags


def render(conn) -> None:
    st.header("Diary")
    notes = store.list_notes(conn)
    if not notes:
        st.write("No notes yet. Add one, or load the made-up demo patient.")
    if st.button("Load demo patient (Ana)"):
        seed.load_demo(conn)
        seed.load_extractions(conn)
        st.rerun()
    if not notes:
        return

    if any(red_flags(n.text) for n in notes):
        st.error(URGENT_MESSAGE)

    extractions = store.get_extractions(conn)
    rows = [
        {"date": n.created_at[:10], "severity": extractions[n.id].severity}
        for n in notes
        if n.id in extractions and extractions[n.id].severity is not None
    ]
    if rows:
        st.subheader("Severity over time")
        st.line_chart(pd.DataFrame(rows).set_index("date"))
    else:
        st.caption("No severity scores yet: they appear once notes are processed.")

    st.subheader(f"Notes ({len(notes)})")
    for n in reversed(notes):
        ex = extractions.get(n.id)
        label = f"#{n.id} · {n.created_at[:16].replace('T', ' ')}"
        if ex and ex.severity is not None:
            label += f" · severity {ex.severity}/10"
        with st.expander(label):
            st.write(n.text)
            flags = red_flags(n.text)
            if flags:
                st.error(URGENT_MESSAGE)
