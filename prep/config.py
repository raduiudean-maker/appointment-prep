"""Provider and model ids, paths, constants. Keep every model id here and nowhere else."""

PROVIDER = "gemini"  # "gemini" or "claude"

# Model id that passed scripts/smoke_test.py (a Flash model with a free tier).
GEMINI_MODEL = "gemini-3-8-flash"

CLAUDE_EXTRACT_MODEL = "claude-haiku-5-5"
CLAUDE_BRIEF_MODEL = "claude-sonnet-5-5"

DB_PATH = "appointment_prep.db"
DEMO_PATIENT_PATH = "data/demo_patient.json"
DEMO_EXTRACTIONS_PATH = "data/demo_extractions.json"
DEMO_BRIEF_PATH = "data/demo_brief.json"
