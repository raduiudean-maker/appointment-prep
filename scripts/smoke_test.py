"""One test call to Gemini. Usage: python scripts/smoke_test.py <model-name>

Reads the key from env GEMINI_API_KEY or .streamlit/secrets.toml. Never prints the key.
"""
import os
import sys
import tomllib
from pathlib import Path


def load_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    secrets = Path(".streamlit/secrets.toml")
    if secrets.exists():
        return tomllib.loads(secrets.read_text(encoding="utf-8")).get("GEMINI_API_KEY", "")
    return ""


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/smoke_test.py <model-name>")
    key = load_key()
    if not key or key.startswith("paste-"):
        sys.exit("No API key found. Put it in .streamlit/secrets.toml as GEMINI_API_KEY.")
    from google import genai

    client = genai.Client(api_key=key)
    reply = client.models.generate_content(
        model=sys.argv[1], contents="Reply with exactly: smoke test ok"
    )
    print(reply.text)


if __name__ == "__main__":
    main()
