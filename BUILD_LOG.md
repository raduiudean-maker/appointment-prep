# Build log

One short entry per day: what I built, what broke, what I learned. This feeds the "Learning and Growth" score.

## 2026-11-08
- Created repo and project structure.
- Free Gemini model name: (fill in from AI Studio Pricing page)
- Free-tier rate limits: (fill in)

## 2026-11-09
- Task 1 done: `Note` and `Extraction` dataclasses, SQLite store (notes + extractions, upsert by note_id). 3 tests, no API calls.
- Learned: the free tier allows about 20 requests a day, so the demo patient's AI results are precomputed once and read from disk (see the plan's Quota strategy).
