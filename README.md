# 7-Minute Appointment Prep

A patient jots down how they feel over a few weeks, by voice or text. Before the visit, the app turns those notes into a one-page brief for the doctor: a timeline, patterns, red flags and three questions to ask. Every claim in the brief points back to the notes it came from.

Built for the STEM2Connect AI Hackathon, **Healthcare** track, as a solo project.

## Problem

Doctor visits are short, and patients forget what happened over the weeks before. "It hurts sometimes" is hard to act on. "Headaches on weekdays after long screen days, worst after under 6 hours of sleep" is not.

## What it does

- **Diary:** add notes in your own words, by text or by voice. A severity chart builds up from them.
- **Visit brief:** one page with a summary, a timeline, patterns (each with its source notes, which you can expand), three questions for the doctor, and any red flags. Download it as a PDF.
- **Safety check:** a rule-based check (no AI) looks for emergency phrases such as "worst headache of my life" or "chest pain". It runs first and shows a red banner, even if the AI is down.
- **Demo patient:** "Ana" is a made-up patient with 21 days of headache notes. Her results are pre-generated and saved in `data/`, so trying the demo uses no AI quota.

The brief never diagnoses or suggests treatment.

## Demo

- Live app: _add the link after deployment_
- Demo video: _add the link after upload_

## How to run locally

    python -m venv .venv
    .venv\Scripts\activate        (macOS/Linux: source .venv/bin/activate)
    pip install -r requirements.txt
    streamlit run app.py

Create `.streamlit/secrets.toml` from `.streamlit/secrets.toml.example` and put your free Gemini key in it (get one at aistudio.google.com). Run the tests with `pytest`. They use fake AI responses, so they need no key.

## How AI is used

- **Gemini API (free tier), at runtime:** reads each note and pulls out symptoms, severity, triggers, medicines and sleep; transcribes voice notes; and writes the brief from the extracted notes.
- **Grounding:** the model must cite note ids for every claim. Any claim that cites a note that doesn't exist is dropped. Red flags come from the rules, never from the model.
- **Swappable provider:** the AI sits behind a small interface (`prep/llm.py`). Claude is available as an optional provider in `prep/providers.py`.
- **Quota-aware:** the free tier allows about 20 requests a day, so the demo patient's results are computed once and loaded from disk. When the daily limit is reached, the app says so and still shows the saved demo brief.

## AI tools used

- **Claude Code** (Anthropic) was used as a build assistant: it wrote most of the code and tests in this repository, working from a plan I chose, and I reviewed and merged each change.
- **Gemini API** (Google, free tier) runs inside the app, as described above. Claude is an optional provider and is not used in the deployed demo.
- Google may use free-tier inputs to improve its products. That is why the app only accepts made-up data (see below).

## Safety and limits

- This is a student prototype, not a medical device, and not medical advice.
- Use made-up or non-sensitive notes only. The app asks you to agree to this before you start. The demo patient is fictional.
- The red-flag rules are deliberately cautious and can raise false alarms. They can also miss things, so they are not a substitute for emergency judgement.
- Notes are stored in a local SQLite file on the machine running the app.

## Credits

Streamlit, google-genai, fpdf2, pandas, pytest.

## What's next

- Check the brief format with real clinicians.
- Support more languages, including Romanian.
- Let patients share the brief as a PDF or a link before the visit.
