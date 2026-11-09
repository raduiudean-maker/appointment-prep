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
- Model id that works: `gemini-3-8-flash`. Free limits as read from AI Studio: about 5 requests/min, 250K tokens/min, 20 requests/day.
- Learned: put the AI behind a tiny interface of my own, so tests use a fake and providers can be swapped.

## 2026-11-09 (model id fix)
- The first config used `gemini-3-8-flash` and got a 404. The id that passed the smoke test, found in the PowerShell history, is `gemini-3.8-flash` (with a dot). Learned: copy IDs from a command that worked, not from a display name.
