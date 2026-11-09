"""Generate data/demo_extractions.json in resumable batches.

Usage: python scripts/precompute_extractions.py [--max 15] [--sleep 13]

The free tier allows about 20 requests a day and 5 a minute, so run this on two days.
It skips notes already saved, pauses between calls, and stops cleanly when the quota runs out.
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from prep import config  # noqa: E402
from prep.llm import LLMError  # noqa: E402
from prep.precompute import precompute_extractions  # noqa: E402
from prep.providers import get_llm  # noqa: E402

NOTES_PATH = REPO / config.DEMO_PATIENT_PATH
OUT_PATH = REPO / config.DEMO_EXTRACTIONS_PATH


def save(entries: list[dict]) -> None:
    OUT_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=15, help="most real API calls this run")
    parser.add_argument("--sleep", type=float, default=13.0, help="seconds between calls")
    args = parser.parse_args()

    notes = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
    existing = json.loads(OUT_PATH.read_text(encoding="utf-8")) if OUT_PATH.exists() else []
    try:
        llm = get_llm()
        entries, hit_quota = precompute_extractions(
            llm, notes, existing, args.max, save, sleep_s=args.sleep
        )
    except LLMError as exc:
        print(f"Stopped: {exc}")
        return 1
    print(f"Saved {len(entries)} of {len(notes)} extractions to {OUT_PATH.name}.")
    if hit_quota:
        print("Daily limit reached. Run this again tomorrow to finish.")
    elif len(entries) < len(notes):
        print("Run it again (tomorrow, if you are near the daily limit) to finish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
