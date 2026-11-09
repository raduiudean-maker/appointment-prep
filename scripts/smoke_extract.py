"""One real extraction on one demo note (uses 1 API call).

Usage: python scripts/smoke_extract.py [note-index]   (default 1, the 2026-10-20 note)
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from prep import config  # noqa: E402
from prep.extract import extract_note  # noqa: E402
from prep.llm import LLMError  # noqa: E402
from prep.models import Note  # noqa: E402
from prep.providers import get_llm  # noqa: E402


def main() -> int:
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    notes = json.loads((REPO / config.DEMO_PATIENT_PATH).read_text(encoding="utf-8"))
    item = notes[index]
    print("NOTE:", item["text"])
    try:
        print("RESULT:", extract_note(get_llm(), Note(0, item["created_at"], item["text"], "seed")))
    except LLMError as exc:
        print(f"Stopped: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
