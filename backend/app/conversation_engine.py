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
from .conversational_filter import normalize_user_input, is_skip_phrase


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
    of the generic correction keywords above. This is a more reliable
    signal for "the user wants to touch this field" than keyword
    guessing alone, and it's schema-driven so it works for any form.
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
    (filled or not) other than exclude_field. Used to decide whether
    it's safe to assume a bare answer belongs to the field currently
    being asked about, or whether the user seems to be talking about
    something else entirely.
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


class ConversationEngine:
    """
    The single source of truth for "what happens on one chat turn".

    This used to be duplicated (and out of sync) between this file
    and main.py. main.py now just calls process() -- all the actual
    logic lives here exactly once.
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
        """Re-validate every non-empty field currently in state.
        Used both before and after processing a message so the
        notion of 'current field' and the planner's own priority
        (validation error beats missing field) always agree."""

        errors = {}

        for field_name, rules in fields.items():

            value = state.get(field_name)

            if value in (None, ""):
                continue

            field_errors = self.validator.validate_field(field_name, value, rules)

            if field_errors:
                errors[field_name] = field_errors

        return errors

    def process(self, session_id, form_name, user_message):

        # ----------------------------------------------------
        # LOAD SCHEMA
        # ----------------------------------------------------

        schema = self.schema_loader.load_schema(form_name)

        if not schema:
            return {"error": f"Could not load form schema for '{form_name}'."}

        fields = schema.get("fields", {})

        if not isinstance(fields, dict):
            return {"error": "Schema fields must be an object."}

        # ----------------------------------------------------
        # LOAD STATE + STATUS
        # ----------------------------------------------------

        current_state = get_saved_conversation(session_id)

        if not isinstance(current_state, dict):
            current_state = {}

        status = get_session_status(session_id)

        if not current_state:
            current_state = self.state_manager.create_empty_state(schema)
            save_conversation(session_id, form_name, current_state)
            status = "COLLECTING"

        # ----------------------------------------------------
        # GUARD: don't let a completed form keep re-submitting
        # ----------------------------------------------------

        if status == "COMPLETED" and user_message:
            return {
                "response": "This form has already been submitted. Thank you!",
                "current_state": current_state,
                "validation_errors": {},
                "action_plan": {"action": "COMPLETE_FORM"},
                "missing_fields": []
            }

        # ----------------------------------------------------
        # FIND CURRENT FIELD
        #
        # This MUST use the same priority the planner uses when it
        # picks what to show the user (validation error first, then
        # missing field) -- otherwise "current_field" can silently
        # point at a different field than the one the user was
        # actually just asked about, and any raw/ambiguous answer
        # gets attributed to the wrong place.
        # ----------------------------------------------------

        pre_validation_errors = self._validate_state(fields, current_state)

        missing_fields = self.missing_detector.get_missing_fields(
            schema=schema,
            state=current_state
        )

        if pre_validation_errors:
            current_field = next(iter(pre_validation_errors))
        elif missing_fields:
            current_field = missing_fields[0]
        else:
            current_field = None

        validation_errors = {}
        extracted_data = {}
        intent = "chat"

        # ----------------------------------------------------
        # PROCESS USER MESSAGE
        # ----------------------------------------------------

        if user_message:

            handled = False

            # Deterministic yes/no handling for boolean fields --
            # skips the LLM call entirely for the common case,
            # which is both faster and cheaper.
            if current_field:

                current_rules = fields.get(current_field, {})

                if current_rules.get("type") == "boolean":

                    cleaned_value, handled = normalize_user_input(
                        current_field,
                        user_message
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

                # Normally only describe still-missing fields to the
                # model (cheap). If the message looks like a
                # correction to something already filled, widen the
                # scope to the whole form just for this turn so the
                # model can actually see the field being corrected.
                extraction_scope = (
                    None
                    if (
                        _looks_like_a_correction(user_message)
                        or _mentions_a_filled_field(user_message, schema, current_state)
                    )
                    else missing_fields
                )

                result = self.extractor.extract_fields(
                    user_message=user_message,
                    schema=schema,
                    current_state=current_state,
                    current_field=current_field,
                    missing_fields=extraction_scope
                )

                extracted_data = result.get("extracted_data", {})
                intent = result.get("intent", "chat")

            # --------------------------------------------------------
            # RAW-VALUE FALLBACK
            #
            # A small local model sometimes fails to map a short,
            # unqualified answer onto the field currently being asked
            # about. If nothing was extracted for the current field,
            # the message doesn't look like "skip" and doesn't
            # mention some other field by name, and it's short enough
            # to plausibly be a single direct answer, treat the raw
            # message itself as the answer to the current field. It
            # still goes through the normal validator below, so a
            # genuinely bad answer just produces the same "please
            # correct this" flow as always.
            # --------------------------------------------------------

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

                # Always persist the attempt, valid or not. An invalid
                # value needs to survive into the next turn so it gets
                # picked up again by _validate_state() above --
                # otherwise a pending correction (like a bad VIN) is
                # forgotten the moment this response is sent, and the
                # next turn's "current field" silently drifts to
                # whatever the next missing field happens to be.
                current_state = self.state_manager.update_state(
                    current_state,
                    {field_name: value}
                )

                if errors:
                    validation_errors[field_name] = errors

        # ----------------------------------------------------
        # RE-VALIDATE FULL STATE (authoritative, post-update)
        # ----------------------------------------------------

        validation_errors = self._validate_state(fields, current_state)

        # ----------------------------------------------------
        # FIND MISSING FIELDS (post-update)
        # ----------------------------------------------------

        missing_fields = self.missing_detector.get_missing_fields(
            schema=schema,
            state=current_state
        )

        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        confidence_scores = self.confidence_engine.confidence_evaluation(
            extracted_data
        )

        low_confidence_fields = self.confidence_engine.low_confidence_fields(
            confidence_scores
        )

        # ----------------------------------------------------
        # PLAN + RESPONSE
        # ----------------------------------------------------

        action_plan = self.planner.next_question(
            validation_errors,
            missing_fields,
            low_confidence_fields
        )

        response = self.response_generator.generate(action_plan, schema)

        # ----------------------------------------------------
        # SAVE STATE
        # ----------------------------------------------------

        save_conversation(session_id, form_name, current_state)

        if action_plan.get("action") == "COMPLETE_FORM" and status != "COMPLETED":
            save_submission(session_id, current_state)

        return {
            "response": response,
            "current_state": current_state,
            "validation_errors": validation_errors,
            "action_plan": action_plan,
            "missing_fields": missing_fields
        }
