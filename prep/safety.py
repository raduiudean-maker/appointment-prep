"""Rule-based red-flag check. No AI: rules are predictable, work offline, and run first.

This is a conservative keyword screen, not a medical device. It would rather raise a
false alarm than hide a real one, so a negation only counts when it sits right before
the phrase in the same clause ("no chest pain", "not the worst headache").
"""
import re

URGENT_MESSAGE = (
    "Some of what you wrote can be a sign of an emergency. "
    "If this is happening now, call 112 or go to the nearest emergency department."
)

# Flag name -> phrase patterns, matched on lowercase text with apostrophes removed.
_FLAGS: dict[str, list[str]] = {
    "sudden severe headache": [
        r"worst headache",
        r"thunderclap",
        r"sudden(?:ly)? (?:and )?(?:severe|intense|terrible|violent) headache",
    ],
    "chest pain": [
        r"chest pain",
        r"pain in my chest",
        r"chest (?:pressure|tightness)",
        r"tightness in my chest",
    ],
    "trouble breathing": [
        r"trouble breathing",
        r"difficulty breathing",
        r"(?:cant|cannot|couldnt) breathe",
        r"short(?:ness)? of breath",
        r"struggling to breathe",
    ],
    "one-sided weakness or numbness": [
        r"(?:weak|weakness|numb|numbness) on (?:the |one )?(?:left |right )?side",
        r"one side of my (?:body|face)",
        r"(?:left|right) (?:arm|leg|side) (?:is |went |feels |felt )?(?:weak|numb)",
        r"face (?:is )?droop",
        r"facial droop",
    ],
    "trouble speaking": [
        r"trouble speaking",
        r"difficulty speaking",
        r"slurred speech",
        r"speech (?:was |is )?slurred",
        r"(?:cant|cannot) speak",
        r"words (?:came|come) out (?:wrong|jumbled|slurred)",
    ],
    "fainting": [
        r"faint(?:ed|ing)",
        r"(?:felt|feel|feeling) (?:a bit |a little |very |really )?faint",
        r"about to (?:faint|pass out)",
        r"passed out",
        r"blacked out",
        r"lost consciousness",
    ],
    "sudden vision loss": [
        r"sudden(?:ly)? (?:loss of vision|vision loss|lost (?:my )?vision)",
        r"lost my vision",
        r"went blind",
        r"suddenly (?:cant|couldnt) see",
    ],
    "thoughts of self-harm": [
        r"kill myself",
        r"suicid",
        r"end my life",
        r"hurt myself",
        r"self harm",
        r"want to die",
    ],
}

_COMPILED = {
    name: [re.compile(rf"\b{p}") for p in patterns] for name, patterns in _FLAGS.items()
}

_NEGATORS = {
    "no", "not", "never", "without", "nothing", "none", "denies", "denied",
    "dont", "didnt", "doesnt", "wasnt", "isnt", "havent", "hasnt", "hadnt",
}
_CLAUSE_BREAK = re.compile(r"[.,;:!?\n]|\b(?:but|however|although|though|except|yet)\b")


def _normalise(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‘", "'")
    text = text.replace("'", "").replace("-", " ")
    return re.sub(r"\s+", " ", text)


def _is_negated(text: str, start: int) -> bool:
    clause = _CLAUSE_BREAK.split(text[:start])[-1]
    return any(word in _NEGATORS for word in clause.split()[-3:])


def red_flags(text: str) -> list[str]:
    """Return the names of the red flags found in `text`, in a fixed order."""
    text = _normalise(text)
    found = []
    for name, patterns in _COMPILED.items():
        if any(
            not _is_negated(text, m.start())
            for pattern in patterns
            for m in pattern.finditer(text)
        ):
            found.append(name)
    return found
