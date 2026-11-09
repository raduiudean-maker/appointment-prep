"""Provider and model ids, paths, constants. Keep every model id here and nowhere else."""

PROVIDER = "gemini"  # "gemini" or "claude"

# Copy the exact model id from Google AI Studio (a Flash model with a free tier).
# Do not guess it. Leave empty until you have checked.
GEMINI_MODEL = ""

CLAUDE_EXTRACT_MODEL = "claude-haiku-5-5"
CLAUDE_BRIEF_MODEL = "claude-sonnet-5-5"

DB_PATH = "appointment_prep.db"
DEMO_PATIENT_PATH = "data/demo_patient.json"
DEMO_EXTRACTIONS_PATH = "data/demo_extractions.json"
DEMO_BRIEF_PATH = "data/demo_brief.json"
