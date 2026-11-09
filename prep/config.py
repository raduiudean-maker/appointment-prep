"""Provider and model ids, paths, constants. Keep every model id here and nowhere else."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def repo_path(path: str) -> Path:
    """Resolve a repo-relative path, so scripts and the app work from any folder."""
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p

PROVIDER = "gemini"  # "gemini" or "claude"

# Model id that passed scripts/smoke_test.py (a Flash model with a free tier).
GEMINI_MODEL = "gemini-3.8-flash"

CLAUDE_EXTRACT_MODEL = "claude-haiku-5-5"
CLAUDE_BRIEF_MODEL = "claude-sonnet-5-5"

DB_PATH = "appointment_prep.db"
DEMO_PATIENT_PATH = "data/demo_patient.json"
DEMO_EXTRACTIONS_PATH = "data/demo_extractions.json"
DEMO_BRIEF_PATH = "data/demo_brief.json"
