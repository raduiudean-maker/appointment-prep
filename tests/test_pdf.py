from prep.models import Claim, VisitBrief
from prep.pdf import HEADING, brief_to_pdf


def _brief(red_flags=None):
    return VisitBrief(
        summary="Headaches on weekdays after screen time.",
        timeline=[Claim("Headache after a long screen day", [1, 2])],
        patterns=[Claim("Worse after under 6 hours of sleep", [3, 7])],
        questions=["Q one?", "Q two?", "Q three?"],
        red_flags=red_flags or [],
        note_count=21,
        date_range=("2026-10-01T08:00", "2026-10-21T08:00"),
    )


def test_pdf_returns_pdf_bytes():
    assert brief_to_pdf(_brief()).startswith(b"%PDF")


def test_pdf_mentions_not_a_diagnosis():
    assert "Not a diagnosis" in HEADING
    pdf = brief_to_pdf(_brief(), compress=False)
    assert b"Not a diagnosis" in pdf


def test_pdf_lists_sources_and_no_red_flags():
    pdf = brief_to_pdf(_brief(), compress=False)
    assert b"notes #3, #7" in pdf
    assert b"None detected by safety rules" in pdf


def test_pdf_shows_red_flags():
    pdf = brief_to_pdf(_brief(["chest pain"]), compress=False)
    assert b"chest pain" in pdf
    assert b"None detected" not in pdf


def test_pdf_handles_non_latin_text():
    b = _brief()
    b.summary = "Durere de cap — și ță → ok"
    assert brief_to_pdf(b).startswith(b"%PDF")
