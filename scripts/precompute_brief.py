"""Generate data/demo_brief.json: the visit brief for the demo patient (1 API call).

Usage: python scripts/precompute_brief.py

Run scripts/precompute_extractions.py first, until data/demo_extractions.json holds all 21 notes.
Rerunning replaces the saved brief and costs 1 more call. Judges and rehearsals then read the
saved file, so they use no quota.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from prep.brief import build_brief, save_cached_brief  # noqa: E402
from prep.llm import LLMError, QuotaError  # noqa: E402
from prep.models import Claim  # noqa: E402
from prep.providers import get_llm  # noqa: E402
from prep.seed import load_demo, load_extractions  # noqa: E402
from prep.store import get_extractions, init_db, list_notes  # noqa: E402


def _show(title: str, claims: list[Claim]) -> None:
    print(f"\n{title}")
    for claim in claims:
        print(f"  - {claim.text}  (notes {', '.join('#' + str(i) for i in claim.source_ids)})")


def main() -> int:
    conn = init_db(":memory:")
    load_demo(conn)
    attached = load_extractions(conn)
    notes = list_notes(conn)
    if attached < len(notes):
        print(
            f"Only {attached} of {len(notes)} notes have extractions. "
            "Run scripts/precompute_extractions.py first."
        )
        return 1
    try:
        brief = build_brief(get_llm(), notes, get_extractions(conn))
    except QuotaError:
        print("Daily limit reached. Try again tomorrow.")
        return 1
    except LLMError as exc:
        print(f"Stopped: {exc}")
        return 1

    save_cached_brief(brief, notes)
    print("SUMMARY:", brief.summary)
    _show("TIMELINE", brief.timeline)
    _show("PATTERNS", brief.patterns)
    print("\nQUESTIONS")
    for question in brief.questions:
        print("  -", question)
    print("\nRED FLAGS:", ", ".join(brief.red_flags) or "none")
    print("\nSaved to data/demo_brief.json. Check that PATTERNS found the four planted ones:")
    print("  1. headaches mostly on weekdays after long screen days")
    print("  2. 4 of the 5 worst days (7+/10) follow under 6h sleep")
    print("  3. ibuprofen in 9 notes")
    print("  4. the blurry-vision note (as a question for the doctor, not an emergency)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
