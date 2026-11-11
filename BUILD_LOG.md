# Build log

One short entry per day: what I built, what broke, what I learned. This feeds the "Learning and Growth" score.

## 2026-11-08
- Created repo and project structure.
- Free Gemini model name: (fill in from AI Studio Pricing page)
- Free-tier rate limits: (fill in)

## 2026-11-09
- Task 1 done: `Note` and `Extraction` dataclasses, SQLite store (notes + extractions, upsert by note_id). 3 tests, no API calls.
- Learned: the free tier allows about 20 requests a day, so the demo patient's AI results are precomputed once and read from disk (see the plan's Quota strategy).
- Task 2 done: 21-day synthetic diary for "Ana" (2026-10-19 to 2026-11-08) and `seed.load_demo`. Planted patterns: weekday headaches after long screen days; 4 of the 5 worst days (7+/10) follow under 6h sleep; ibuprofen in 9 notes; one brief blurry-vision note (a question for the doctor, not a red flag). 4 new tests, no API calls.

## 2026-11-09 (Task 3)
- Task 3 done: LLM interface (`prep/llm.py`), Gemini and optional Claude providers, per-note extraction, and the resumable precompute for the demo patient's extractions. 22 new tests, all with fake AI responses, so no quota used.
- Model id that works: `gemini-3.8-flash` (first logged with dashes by mistake, see the fix entry below). Free limits as read from AI Studio: about 5 requests/min, 250K tokens/min, 20 requests/day.
- Learned: put the AI behind a tiny interface of my own, so tests use a fake and providers can be swapped.

## 2026-11-09 (Task 4)
- Task 4 done: `prep/safety.py`, a rule-based red-flag check (8 groups, e.g. "worst headache", chest pain, "cant breathe"). No AI, so it works offline and never uses quota. 21 tests; the whole suite is at 50.
- Learned: for safety, rules guard the dangerous case and the AI adds insight. A negation ("no chest pain") only counts when it sits right before the phrase in the same clause, so "no headache earlier but chest pain now" still flags. It is built to over-warn rather than miss one.

## 2026-11-09 (model id fix)
- The first config used `gemini-3-8-flash` and got a 404. The id that passed the smoke test, found in the PowerShell history, is `gemini-3.8-flash` (with a dot). Learned: copy IDs from a command that worked, not from a display name.

## 2026-11-09 (Task 5)
- Task 5 done: `prep/brief.py` builds the visit brief from the notes. Every pattern and timeline line carries the ids of the notes it came from. Invented ids are dropped, and a claim with no real source is dropped. Red flags come from the rules, never from the model. 15 new tests, all with fake AI responses.
- The prompt includes the weekday of each note, because the model cannot work out "mostly weekdays" from raw dates.
- The demo patient's brief is saved to `data/demo_brief.json` (1 real call) and loaded from disk afterwards. Its note ids are re-mapped through each note's date, so it still works if the database numbers the notes differently.

## 2026-11-09 (busy-model retry)
- Gemini 503 "high demand" is now retried up to 3 tries (waits of 2 s and 6 s). A quota error (429) is never retried and shows the daily-limit message.

## 2026-11-09 (Task 6)
- Task 6 done: `prep/transcribe.py`, `prep/pdf.py`, `prep/ingest.py` and the Streamlit app (consent gate, Diary, Add a note, Visit brief). The save-a-note steps live in `ingest.py` so they can be tested without Streamlit: safety check first, then transcription, then save, then extraction. If any AI step fails, the note is still kept.
- The PDF uses the built-in Latin-1 fonts, so punctuation like the em dash is mapped to plain characters. Learned: check what characters a PDF font supports before trusting it with real text.

## 2026-11-11 (slow brief)
- The brief is one big AI call, and a "thinking" model can spend a long time reasoning before it answers. Added an optional `GEMINI_THINKING_LEVEL` in `prep/config.py` (default off) and a "can take up to a minute" message. The demo patient's brief is read from disk once `precompute_brief.py` has run, so it opens instantly.
