from .db import (
    get_saved_conversation,
    get_session_status,
    save_conversation,
    save_submission
)

from .schema_loader import SchemaLoader
from .state_manager import StateManager
from .extractor import LLMExtractor
from .validator import FormValidator
from .missing_field import MissingFieldDetector
from .planner import Planner
from .response_generator import ResponseGenerator
from .confidence_engine import ConfidenceEngine
from .conversational_filter import (
    normalize_user_input,
    is_skip_phrase,
    looks_like_go_back_request
)
from . import sections as sections_module


# Words that suggest the user is trying to go back and fix something
# they already answered, rather than just answering the current
# question. When one of these shows up, we widen the extractor's
# field scope back to the whole form for that single turn -- normal
# turns stay cheap (missing fields only), corrections still work.
CORRECTION_KEYWORDS = {
    "actually", "change", "update", "correct", "instead",
    "wrong", "meant", "edit", "fix", "mistake", "typo"
}


def _looks_like_a_correction(message):
    lowered = message.lower()
    return any(keyword in lowered for keyword in CORRECTION_KEYWORDS)


def _mentions_a_filled_field(message, schema, current_state):
    """
    True if the user's message directly names a field that's already
    been filled in (by its label or its field name with underscores
    turned into spaces) -- e.g. "for fuel type i use gas" mentions
    the already-filled "fuel_type" field even though it contains none
    of the generic correction keywords above.
    """

    lowered = message.lower()
    fields = schema.get("fields", {})

    if not isinstance(fields, dict) or not isinstance(current_state, dict):
        return False

    for field_name, rules in fields.items():

        if current_state.get(field_name) in (None, ""):
            continue

        label = field_name.replace("_", " ")
        if isinstance(rules, dict):
            label = rules.get("label", label)

        if label.lower() in lowered or field_name.replace("_", " ").lower() in lowered:
            return True

    return False


def _message_mentions_other_field(message, schema, exclude_field):
    """
    Same idea as _mentions_a_filled_field, but checks ANY field
    (filled or not) other than exclude_field.
    """

    lowered = message.lower()
    fields = schema.get("fields", {})

    if not isinstance(fields, dict):
        return False

    for field_name, rules in fields.items():

        if field_name == exclude_field:
            continue

        label = field_name.replace("_", " ")
        if isinstance(rules, dict):
            label = rules.get("label", label)

        if label.lower() in lowered or field_name.replace("_", " ").lower() in lowered:
            return True

    return False


def _find_mentioned_field_names(message, schema):
    """
    Returns every field name whose label (or field name with
    underscores turned into spaces) is directly named in the message.
    Used to give a correction a narrow, targeted extraction scope
    instead of falling back to the entire schema -- naming a specific
    field should mean "look at this field", not "look at all 24".
    """

    lowered = message.lower()
    fields = schema.get("fields", {})
    mentioned = set()

    if not isinstance(fields, dict):
        return mentioned

    for field_name, rules in fields.items():

        label = field_name.replace("_", " ")
        if isinstance(rules, dict):
            label = rules.get("label", label)

        if label.lower() in lowered or field_name.replace("_", " ").lower() in lowered:
            mentioned.add(field_name)

    return mentioned


class ConversationEngine:
    """
    The single source of truth for "what happens on one chat turn".

    Forms may optionally declare "sections" in their schema to break a
    large form into named parts (see sections.py). This is fully
    opt-in per form -- a schema with no "sections" key behaves
    exactly as it always has, section-related code paths simply never
    trigger.
    """

    def __init__(self):
        self.schema_loader = SchemaLoader()
        self.state_manager = StateManager()
        self.extractor = LLMExtractor()
        self.validator = FormValidator()
        self.missing_detector = MissingFieldDetector()
        self.planner = Planner()
        self.response_generator = ResponseGenerator()
        self.confidence_engine = ConfidenceEngine()

    def _validate_state(self, fields, state):
        """Re-validate every non-empty field currently in state."""

        errors = {}

        for field_name, rules in fields.items():

            value = state.get(field_name)

            if value in (None, ""):
                continue

            field_errors = self.validator.validate_field(field_name, value, rules)

            if field_errors:
                errors[field_name] = field_errors

        return errors

    def _scope_to_section(self, schema, state, missing_fields_full, validation_errors_full):
        """If this form uses sections, restrict missing_fields and
        validation_errors down to just the active section's fields.
        Forms without sections get the full, unscoped lists back
        unchanged."""

        if not sections_module.has_sections(schema):
            return missing_fields_full, validation_errors_full

        section_index = sections_module.get_current_section_index(state)
        section_field_names = set(sections_module.get_section_fields(schema, section_index))

        scoped_missing = [f for f in missing_fields_full if f in section_field_names]
        scoped_errors = {
            k: v for k, v in validation_errors_full.items() if k in section_field_names
        }

        return scoped_missing, scoped_errors

    def _get_extractable_optional_fields(self, schema, state):
        """
        Optional (non-required) fields that are still empty. These
        are never something the bot proactively ASKS about (that stays
        governed entirely by missing_fields, i.e. required fields
        only) -- but they should still be ACCEPTABLE if the user
        volunteers the info unprompted, e.g. mentioning gender in the
        same breath as their name even though gender isn't required.

        Scoped to the active section when this form uses sections, so
        it doesn't reintroduce "many fields at once" -- an optional
        field from a later section still isn't offered until that
        section is reached.
        """

        fields = schema.get("fields", {})

        if sections_module.has_sections(schema):
            section_index = sections_module.get_current_section_index(state)
            allowed_names = set(sections_module.get_section_fields(schema, section_index))
        else:
            allowed_names = None

        optional_fields = []

        for field_name, rules in fields.items():

            if not isinstance(rules, dict):
                continue

            if rules.get("required", False):
                continue

            if allowed_names is not None and field_name not in allowed_names:
                continue

            value = state.get(field_name)
            if value not in (None, ""):
                continue

            condition = rules.get("condition")
            if condition and not self.missing_detector.condition_met(condition, state):
                continue

            optional_fields.append(field_name)

        return optional_fields

    def _respond(
        self,
        schema,
        fields,
        current_state,
        session_id,
        form_name,
        status,
        action_plan=None,
        response_prefix="",
        extracted_data_for_confidence=None
    ):
        """
        Shared tail-end of process(): recompute validation/missing
        state, decide (or accept a pre-decided) action_plan, generate
        the response text, persist, and build the returned dict. Used
        by every exit path -- normal answers, section transitions,
        and explicit navigation -- so there's exactly one place that
        decides "what does the user see next".
        """

        uses_sections = sections_module.has_sections(schema)

        validation_errors_full = self._validate_state(fields, current_state)
        missing_fields_full = self.missing_detector.get_missing_fields(
            schema=schema, state=current_state
        )

        confidence_scores = self.confidence_engine.confidence_evaluation(
            extracted_data_for_confidence or {}
        )
        low_confidence_fields = self.confidence_engine.low_confidence_fields(confidence_scores)

        if action_plan is None:

            scoped_missing, scoped_errors = self._scope_to_section(
                schema, current_state, missing_fields_full, validation_errors_full
            )

            if uses_sections:

                section_index = sections_module.get_current_section_index(current_state)
                section_complete = not scoped_missing and not scoped_errors
                is_last = sections_module.is_last_section(schema, section_index)

                if section_complete and not is_last:
                    action_plan = {
                        "action": "CONFIRM_SECTION_ADVANCE",
                        "current_section": sections_module.get_section_name(schema, section_index),
                        "next_section": sections_module.get_section_name(schema, section_index + 1)
                    }
                elif section_complete and is_last:
                    # Last section done -- completion depends on the
                    # WHOLE form, not just this section (covers the
                    # rare case of a field not assigned to any section).
                    if not missing_fields_full and not validation_errors_full:
                        action_plan = {"action": "COMPLETE_FORM"}
                    else:
                        action_plan = self.planner.next_question(
                            validation_errors_full, missing_fields_full, []
                        )
                else:
                    action_plan = self.planner.next_question(
                        scoped_errors, scoped_missing, low_confidence_fields
                    )
            else:
                action_plan = self.planner.next_question(
                    validation_errors_full, missing_fields_full, low_confidence_fields
                )

        response_text = response_prefix + self.response_generator.generate(action_plan, schema)

        save_conversation(session_id, form_name, current_state)

        if action_plan.get("action") == "COMPLETE_FORM" and status != "COMPLETED":
            save_submission(session_id, current_state)
            status = "COMPLETED"

        if uses_sections:
            report_missing, report_errors = self._scope_to_section(
                schema, current_state, missing_fields_full, validation_errors_full
            )
        else:
            report_missing, report_errors = missing_fields_full, validation_errors_full

        return {
            "response": response_text,
            "current_state": sections_module.strip_internal_keys(current_state),
            "validation_errors": report_errors,
            "action_plan": action_plan,
            "missing_fields": report_missing,
            "sections": sections_module.build_section_progress(
                schema, current_state, missing_fields_full, validation_errors_full
            )
        }

    def process(self, session_id, form_name, user_message, target_section=None):

        # ----------------------------------------------------
        # LOAD SCHEMA
        # ----------------------------------------------------

        schema = self.schema_loader.load_schema(form_name)

        if not schema:
            return {"error": f"Could not load form schema for '{form_name}'."}

        fields = schema.get("fields", {})

        if not isinstance(fields, dict):
            return {"error": "Schema fields must be an object."}

        uses_sections = sections_module.has_sections(schema)

        # ----------------------------------------------------
        # LOAD STATE + STATUS
        # ----------------------------------------------------

        current_state = get_saved_conversation(session_id)

        if not isinstance(current_state, dict):
            current_state = {}

        status = get_session_status(session_id)

        just_created = False

        if not current_state:
            current_state = self.state_manager.create_empty_state(schema)
            save_conversation(session_id, form_name, current_state)
            status = "COLLECTING"
            just_created = True

        # ----------------------------------------------------
        # GUARD: don't let a completed form keep re-submitting
        # ----------------------------------------------------

        if status == "COMPLETED" and user_message:
            return {
                "response": "This form has already been submitted. Thank you!",
                "current_state": sections_module.strip_internal_keys(current_state),
                "validation_errors": {},
                "action_plan": {"action": "COMPLETE_FORM"},
                "missing_fields": [],
                "sections": sections_module.build_section_progress(
                    schema, current_state, [], {}
                )
            }

        # ----------------------------------------------------
        # INTRO MESSAGE for a brand-new sectioned form
        # ----------------------------------------------------

        if uses_sections and just_created and not user_message:
            sections_list = sections_module.get_sections(schema)
            intro = (
                f"This form is broken into {len(sections_list)} parts. "
                f"Let's start with {sections_module.get_section_name(schema, 0)}. "
            )
            return self._respond(
                schema, fields, current_state, session_id, form_name, status,
                response_prefix=intro
            )

        # ----------------------------------------------------
        # EXPLICIT SECTION NAVIGATION (progress-bar button click)
        # ----------------------------------------------------

        if uses_sections and target_section is not None:
            sections_list = sections_module.get_sections(schema)
            if isinstance(target_section, int) and 0 <= target_section < len(sections_list):
                current_state = sections_module.set_current_section_index(
                    current_state, target_section
                )
                target_name = sections_module.get_section_name(schema, target_section)
                return self._respond(
                    schema, fields, current_state, session_id, form_name, status,
                    response_prefix=f"Sure, here's {target_name}. "
                )
            # invalid index -- ignore and fall through to normal processing

        # ----------------------------------------------------
        # FIND CURRENT FIELD (section-scoped when applicable)
        #
        # This MUST use the same priority the planner uses when it
        # picks what to show the user (validation error first, then
        # missing field) -- otherwise "current_field" can silently
        # point at a different field than the one the user was
        # actually just asked about.
        # ----------------------------------------------------

        pre_validation_errors_full = self._validate_state(fields, current_state)
        missing_fields_full = self.missing_detector.get_missing_fields(
            schema=schema, state=current_state
        )

        pre_missing, pre_errors = self._scope_to_section(
            schema, current_state, missing_fields_full, pre_validation_errors_full
        )

        if pre_errors:
            current_field = next(iter(pre_errors))
        elif pre_missing:
            current_field = pre_missing[0]
        else:
            current_field = None

        # ----------------------------------------------------
        # SECTION TRANSITION HANDLING
        #
        # If the active section has nothing left to fill/fix and
        # there's a next section, the incoming message is first
        # checked as a possible answer to "ready to move on?" before
        # anything else happens.
        # ----------------------------------------------------

        if (
            uses_sections
            and user_message
            and current_field is None
            and not sections_module.is_last_section(
                schema, sections_module.get_current_section_index(current_state)
            )
        ):
            section_index = sections_module.get_current_section_index(current_state)

            if looks_like_go_back_request(user_message):
                target = sections_module.resolve_go_back_target(
                    schema, section_index, user_message
                )
                current_state = sections_module.set_current_section_index(current_state, target)
                target_name = sections_module.get_section_name(schema, target)
                return self._respond(
                    schema, fields, current_state, session_id, form_name, status,
                    response_prefix=f"Sure, taking you back to {target_name}. "
                )

            cleaned, handled = normalize_user_input("_section_confirm", user_message)

            if handled and cleaned in ("yes", "true"):
                new_index = section_index + 1
                current_state = sections_module.set_current_section_index(current_state, new_index)
                new_name = sections_module.get_section_name(schema, new_index)
                return self._respond(
                    schema, fields, current_state, session_id, form_name, status,
                    response_prefix=f"Great job! Let's move on to {new_name}. "
                )

            if handled and cleaned in ("no", "false"):
                return self._respond(
                    schema, fields, current_state, session_id, form_name, status,
                    action_plan={"action": "SECTION_ADVANCE_DECLINED"}
                )

            if handled:
                # Recognized as some other fixed response (e.g. a
                # skip phrase) that doesn't clearly mean yes or no --
                # just re-show the confirmation question.
                return self._respond(
                    schema, fields, current_state, session_id, form_name, status,
                    action_plan={
                        "action": "CONFIRM_SECTION_ADVANCE",
                        "current_section": sections_module.get_section_name(schema, section_index),
                        "next_section": sections_module.get_section_name(schema, section_index + 1)
                    }
                )

            # Not handled as yes/no/skip -- fall through and treat
            # this as a normal message (e.g. a correction) within the
            # current, already-complete section.

        # ----------------------------------------------------
        # GO-BACK REQUEST MID-SECTION (not just at a transition point)
        # ----------------------------------------------------

        if uses_sections and user_message and looks_like_go_back_request(user_message):
            section_index = sections_module.get_current_section_index(current_state)
            target = sections_module.resolve_go_back_target(schema, section_index, user_message)
            current_state = sections_module.set_current_section_index(current_state, target)
            target_name = sections_module.get_section_name(schema, target)
            return self._respond(
                schema, fields, current_state, session_id, form_name, status,
                response_prefix=f"Sure, taking you back to {target_name}. "
            )

        # ----------------------------------------------------
        # NORMAL MESSAGE PROCESSING
        # ----------------------------------------------------

        extracted_data = {}
        intent = "chat"

        if user_message:

            handled = False

            # Deterministic yes/no handling for boolean fields.
            if current_field:

                current_rules = fields.get(current_field, {})

                if current_rules.get("type") == "boolean":

                    cleaned_value, handled = normalize_user_input(
                        current_field, user_message
                    )

                    if handled:
                        if cleaned_value == "NOT_PROVIDED":
                            extracted_data = {}
                            intent = "chat"
                        else:
                            extracted_data = {
                                current_field: cleaned_value in ("yes", "true")
                            }
                            intent = "answer"

            if not handled:

                # Normal scope = required-missing fields (what the bot
                # is actively asking about) PLUS still-empty optional
                # fields (things the user is allowed to volunteer even
                # though the bot won't ask for them). This is what
                # lets "I am a female" register for an optional gender
                # field without the bot ever needing to nag for it.
                normal_scope = pre_missing + self._get_extractable_optional_fields(
                    schema, current_state
                )

                is_correction = (
                    _looks_like_a_correction(user_message)
                    or _mentions_a_filled_field(user_message, schema, current_state)
                )

                if is_correction:
                    # A correction gets a NARROW scope, not the whole
                    # form: the current section's fields (so a normal
                    # answer still works) plus whatever specific
                    # field the message actually names (so correcting
                    # something from an earlier, already-completed
                    # section still works by naming it directly).
                    # This keeps corrections targeted instead of
                    # dumping all fields from every section into one
                    # call, which would defeat the whole point of
                    # sections.
                    mentioned = _find_mentioned_field_names(user_message, schema)
                    extraction_scope = list(set(normal_scope) | mentioned)

                    if not extraction_scope:
                        # Correction language with nothing identifiable
                        # to scope to (rare) -- fall back to the full
                        # form as a last resort.
                        extraction_scope = None
                else:
                    extraction_scope = normal_scope

                result = self.extractor.extract_fields(
                    user_message=user_message,
                    schema=schema,
                    current_state=current_state,
                    current_field=current_field,
                    missing_fields=extraction_scope
                )

                extracted_data = result.get("extracted_data", {})
                intent = result.get("intent", "chat")

            # Raw-value fallback: if nothing was extracted for the
            # field currently being asked about, and the message is
            # short, doesn't look like a decline, and doesn't mention
            # some other field, treat the raw message as the answer.
            if (
                current_field
                and current_field not in extracted_data
                and fields.get(current_field, {}).get("type") != "boolean"
                and not is_skip_phrase(user_message)
                and len(user_message.split()) <= 8
                and not _message_mentions_other_field(user_message, schema, current_field)
            ):
                extracted_data[current_field] = user_message.strip()
                intent = "answer"

            if intent == "chat":
                extracted_data = {}

            for field_name, value in extracted_data.items():

                if field_name not in fields:
                    continue

                rules = fields[field_name]

                errors = self.validator.validate_field(field_name, value, rules)

                current_state = self.state_manager.update_state(
                    current_state, {field_name: value}
                )

                # (errors are recomputed authoritatively in _respond
                # via _validate_state -- no need to track them here)

        return self._respond(
            schema, fields, current_state, session_id, form_name, status,
            extracted_data_for_confidence=extracted_data
        )
