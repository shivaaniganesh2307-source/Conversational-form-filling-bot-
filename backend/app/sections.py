"""
Support for optional multi-part forms.

A schema can declare a "sections" array to break a large form into
named parts, e.g.:

    "sections": [
        {"name": "Personal Information", "fields": ["first_name", "last_name"]},
        {"name": "Employment", "fields": ["uic", "date_hired"]}
    ]

This is entirely OPT-IN per form. A schema with no "sections" key
behaves exactly as it always has -- every function here returns None
or a no-op in that case, so small forms are completely unaffected.

The benefit isn't just UX (a progress bar, "Part 2 of 4" framing) --
it also shrinks how many fields the extractor has to consider at
once, the same way batching does, but grouped by *meaning* instead of
arbitrary chunk size. A dense paragraph about "personal info" only
gets checked against ~5 candidate fields instead of the whole form.

The current section index is stored inside the conversation state
itself under a reserved key, so no database schema changes are
needed -- it persists the same way any other field does.
"""

SECTION_INDEX_KEY = "__section_index__"


def get_sections(schema):
    """Returns the schema's sections list, or None if this form
    doesn't use sections."""

    sections = schema.get("sections")

    if not isinstance(sections, list) or not sections:
        return None

    return sections


def has_sections(schema):
    return get_sections(schema) is not None


def get_section_name(schema, index):
    sections = get_sections(schema)

    if sections is None or not (0 <= index < len(sections)):
        return f"Part {index + 1}"

    return sections[index].get("name", f"Part {index + 1}")


def get_section_fields(schema, index):
    sections = get_sections(schema)

    if sections is None or not (0 <= index < len(sections)):
        return []

    fields = sections[index].get("fields", [])

    return fields if isinstance(fields, list) else []


def get_current_section_index(state):
    if not isinstance(state, dict):
        return 0

    index = state.get(SECTION_INDEX_KEY, 0)

    return index if isinstance(index, int) else 0


def set_current_section_index(state, index):
    if not isinstance(state, dict):
        state = {}

    state[SECTION_INDEX_KEY] = index

    return state


def is_last_section(schema, index):
    sections = get_sections(schema)

    if sections is None:
        return True

    return index >= len(sections) - 1


def strip_internal_keys(state):
    """Returns a copy of state with reserved (__...__) keys removed --
    used whenever state is sent to the frontend, so internal
    bookkeeping like the section index doesn't show up in the
    'Collected Data' panel."""

    if not isinstance(state, dict):
        return {}

    return {
        key: value for key, value in state.items()
        if not (key.startswith("__") and key.endswith("__"))
    }


def build_section_progress(schema, state, missing_fields_full, validation_errors_full):
    """Returns [{"name", "index", "complete", "active"}] for every
    section, for the frontend progress bar. Returns None if this form
    doesn't use sections."""

    sections = get_sections(schema)

    if sections is None:
        return None

    current_index = get_current_section_index(state)
    missing_set = set(missing_fields_full)
    error_fields = set(validation_errors_full.keys())

    progress = []

    for index, section in enumerate(sections):
        section_fields = set(section.get("fields", []))
        incomplete = bool(section_fields & (missing_set | error_fields))

        progress.append({
            "index": index,
            "name": section.get("name", f"Part {index + 1}"),
            "complete": not incomplete,
            "active": index == current_index,
            # Only sections at or before the current one are navigable
            # via the progress bar -- this is a "go back and edit"
            # feature, not a way to skip ahead of required fields.
            "navigable": index <= current_index,
            # Exposed so the frontend can progressively reveal the
            # "Collected Data" panel section-by-section instead of
            # showing every field (including ones from parts the user
            # hasn't reached yet) all at once.
            "fields": section.get("fields", []),
        })

    return progress


def resolve_go_back_target(schema, current_index, message):
    """Figures out which section index the user meant when asking to
    go back -- by an explicit 'part N', by naming a section, or just
    defaulting to the previous one."""

    import re

    sections = get_sections(schema)

    if sections is None:
        return max(0, current_index - 1)

    lowered = message.lower()

    match = re.search(r"part\s+(\d+)", lowered)
    if match:
        target = int(match.group(1)) - 1
        if 0 <= target < len(sections):
            return target

    for index, section in enumerate(sections):
        name = section.get("name", "").strip().lower()
        if name and name in lowered:
            return index

    return max(0, current_index - 1)
