
import re


SKIP_PHRASES = {
    "idk", "i don't know", "i do not know", "not sure", "skip",
    "no idea", "i have no idea", "don't remember", "do not remember",
    "i don't remember", "i do not remember",
    "can we come back to it later", "come back to it later"
}

# Broader PATTERNS (not exact phrases) for "this doesn't apply to me /
# I have nothing to give here" -- e.g. "I have no middle name", "I
# don't have a suite number", "N/A", "not applicable". This is
# intentionally separate from SKIP_PHRASES (used by the boolean yes/
# no path below): "I have no allergies" is a real, meaningful FALSE
# answer for a boolean field, not a decline -- these patterns are
# only consulted by is_skip_phrase(), which the raw-value fallback in
# conversation_engine.py uses for non-boolean fields. Boolean fields
# keep using the exact-match SKIP_PHRASES check further down,
# unaffected by this.
DECLINE_PATTERNS = [
    re.compile(r"^i (have|has|got) no\b"),
    re.compile(r"^i don'?t have\b"),
    re.compile(r"^i do not have\b"),
    re.compile(r"^none$"),
    re.compile(r"^n/?a$"),
    re.compile(r"^not applicable$"),
    re.compile(r"^doesn'?t apply$"),
    re.compile(r"^does not apply$"),
]


def is_skip_phrase(text: str) -> bool:
    """Generic 'the user doesn't want to / has nothing to answer with
    for this field' check, usable for any non-boolean field type. This
    is what the raw-value fallback consults before deciding to shove a
    bare message into a field verbatim -- without this, a phrase like
    "I have no middle name" would otherwise get stored as the literal
    text of someone's middle name."""

    normalized = str(text).strip().lower()

    if normalized in SKIP_PHRASES:
        return True

    return any(pattern.match(normalized) for pattern in DECLINE_PATTERNS)


GO_BACK_PHRASES = {
    "go back", "back", "previous", "previous section", "previous part",
    "let's go back", "lets go back", "can i go back", "i want to go back",
    "take me back", "return to", "go back to previous section"
}


def looks_like_go_back_request(text: str) -> bool:
    """Detects a request to navigate to an earlier section of a
    multi-part form -- used only for forms that declare 'sections' in
    their schema. Deterministic phrase-check, not an LLM call, since
    navigation intent should never depend on a small model guessing
    correctly."""

    normalized = str(text).strip().lower()

    if normalized in GO_BACK_PHRASES:
        return True

    return normalized.startswith("go back") or normalized.startswith("take me back")


def normalize_user_input(field_name: str, raw_input: str):

    text = str(raw_input).strip()
    normalized = text.lower()

    if normalized in SKIP_PHRASES:
        return "NOT_PROVIDED", True

    yes_phrases = {"yes", "y", "yeah", "yep", "sure", "true", "i do", "of course"}

    if normalized in yes_phrases:
        return "yes", True

    no_phrases = {"no", "n", "nope", "false", "i don't", "i do not", "none"}

    if normalized in no_phrases:
        return "no", True

    if normalized in {"yes please", "yes please do", "yes i am", "yes i do"}:
        return "yes", True

    if normalized in {"no thanks", "no thank you", "no i am not", "no i don't", "no i do not"}:
        return "no", True

    return text, False
