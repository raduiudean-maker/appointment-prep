"""VisitBrief to a one-page A4 PDF."""
from fpdf import FPDF

from prep.models import Claim, VisitBrief

HEADING = "Visit brief — prepared by the patient with AI assistance. Not a diagnosis."
NO_FLAGS = "None detected by safety rules"

_PUNCT = {"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "...", "→": "->"}


def _safe(text: str) -> str:
    """The built-in PDF fonts only know Latin-1, so map common punctuation and drop the rest."""
    for src, dst in _PUNCT.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


def _sources(claim: Claim) -> str:
    ids = ", ".join(f"#{i}" for i in claim.source_ids)
    return f"{_safe(claim.text)} (notes {ids})"


def brief_to_pdf(brief: VisitBrief, compress: bool = True) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_compression(compress)
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    w = pdf.epw

    def heading(text: str) -> None:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(w, 6, text, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9.5)

    def para(text: str) -> None:
        pdf.multi_cell(w, 4.8, text, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 12)
    pdf.multi_cell(w, 6, _safe(HEADING), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    start, end = brief.date_range[0][:10], brief.date_range[1][:10]
    para(f"{brief.note_count} notes, {start} to {end}")

    heading("Summary")
    para(_safe(brief.summary))

    heading("Timeline")
    for c in brief.timeline:
        para("- " + _sources(c))

    heading("Patterns")
    for c in brief.patterns:
        para("- " + _sources(c))

    heading("Questions to ask")
    for i, q in enumerate(brief.questions, 1):
        para(f"{i}. {_safe(q)}")

    heading("Red flags")
    if brief.red_flags:
        for f in brief.red_flags:
            para("- " + _safe(f))
    else:
        para(NO_FLAGS)

    return bytes(pdf.output())
