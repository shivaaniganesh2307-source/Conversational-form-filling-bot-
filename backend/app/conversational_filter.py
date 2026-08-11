import re

def normalize_user_input(field_name: str, raw_input: str) -> tuple[str, bool]:
    """
    Cleans up common conversational phrases, slang, or 'idk' 
    before sending it to an LLM or validator.
    Returns: (processed_value, is_handled_deterministically)
    """
    text = str(raw_input).strip().lower()

    # 1. Handle "IDK" or skip intents for any field
    skip_phrases = ["idk", "i don't know", "not sure", "skip", "none", "no idea"]
    if text in skip_phrases:
        return "NOT_PROVIDED", True  # Special flag your code can handle

    # 2. Deterministic handling for Booleans (yes/no fields)
    # This prevents wasting LLM tokens on simple yes/no questions!
    yes_phrases = ["yes", "y", "yeah", "yep", "sure", "true", "i do", "of course"]
    no_phrases = ["no", "n", "nope", "false", "i don't", "none"]

    if text in yes_phrases:
        return "yes", True
    if text in no_phrases:
        return "no", True

    # If it's a regular text field (like name, department, etc.), 
    # pass it through to your extractor/validator normally.
    return raw_input, False