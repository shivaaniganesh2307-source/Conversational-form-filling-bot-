
import re


def normalize_user_input(
    field_name: str,
    raw_input: str
) -> tuple[str, bool]:

    text = str(raw_input).strip()

    normalized = text.lower()

    # --------------------------------------------------
    # SKIP / UNKNOWN
    # --------------------------------------------------

    skip_phrases = {
        "idk",
        "i don't know",
        "i do not know",
        "not sure",
        "skip",
        "no idea",
        "i have no idea",
        "don't remember",
        "do not remember",
        "i don't remember",
        "i do not remember",
        "can we come back to it later",
        "come back to it later"
    }

    if normalized in skip_phrases:

        return "NOT_PROVIDED", True


    # --------------------------------------------------
    # YES
    # --------------------------------------------------

    yes_phrases = {
        "yes",
        "y",
        "yeah",
        "yep",
        "sure",
        "true",
        "i do",
        "of course"
    }

    if normalized in yes_phrases:

        return "yes", True


    # --------------------------------------------------
    # NO
    # --------------------------------------------------

    no_phrases = {
        "no",
        "n",
        "nope",
        "false",
        "i don't",
        "i do not",
        "none"
    }

    if normalized in no_phrases:

        return "no", True


    # --------------------------------------------------
    # SIMPLE "YES/NO" SENTENCES
    # --------------------------------------------------

    if normalized in {
        "yes please",
        "yes please do",
        "yes i am",
        "yes i do"
    }:

        return "yes", True


    if normalized in {
        "no thanks",
        "no thank you",
        "no i am not",
        "no i don't",
        "no i do not"
    }:

        return "no", True


    # --------------------------------------------------
    # Otherwise let the LLM interpret it
    # --------------------------------------------------

    return text, False

