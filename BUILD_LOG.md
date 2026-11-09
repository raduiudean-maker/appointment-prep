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
