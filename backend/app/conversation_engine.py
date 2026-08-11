from .db import (
    get_saved_conversation,
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


class ConversationEngine:

    def __init__(self):

        self.schema_loader = SchemaLoader()

        self.state_manager = StateManager()

        self.extractor = LLMExtractor()

        self.validator = FormValidator()

        self.missing_detector = (
            MissingFieldDetector()
        )

        self.planner = Planner()

        self.response_generator = (
            ResponseGenerator()
        )

    def process(
        self,
        session_id,
        form_name,
        user_message
    ):

        # ----------------------------------------
        # LOAD SCHEMA
        # ----------------------------------------

        schema = self.schema_loader.load_schema(
            form_name
        )

        if not schema:

            return {
                "error": "Could not load form schema."
            }

        fields = schema.get(
            "fields",
            {}
        )

        # ----------------------------------------
        # LOAD STATE
        # ----------------------------------------

        current_state = (
            get_saved_conversation(
                session_id
            )
        )

        if not current_state:

            current_state = (
                self.state_manager
                .create_empty_state(schema)
            )

            save_conversation(
                session_id,
                form_name,
                current_state
            )

        # ----------------------------------------
        # FIND CURRENT FIELD
        # ----------------------------------------

        missing_fields = (
            self.missing_detector
            .get_missing_fields(
                schema,
                current_state
            )
        )

        current_field = (
            missing_fields[0]
            if missing_fields
            else None
        )

        validation_errors = {}

        # ----------------------------------------
        # EXTRACT USER MESSAGE
        # ----------------------------------------

        if user_message:

            result = (
                self.extractor
                .extract_fields(
                    user_message=user_message,
                    schema=schema,
                    current_state=current_state,
                    current_field=current_field
                )
            )

            extracted_data = result.get(
                "extracted_data",
                {}
            )

            intent = result.get(
                "intent",
                "chat"
            )

            # ------------------------------------
            # CHAT
            # ------------------------------------

            if intent == "chat":

                action_plan = {
                    "action": "REQUEST_MISSING_FIELD",
                    "field": current_field
                } if current_field else {
                    "action": "COMPLETE_FORM"
                }

                response = (
                    self.response_generator
                    .generate(
                        action_plan,
                        schema
                    )
                )

                return {
                    "response": response,
                    "current_state": current_state,
                    "validation_errors": {},
                    "action_plan": action_plan,
                    "missing_fields": missing_fields
                }

            # ------------------------------------
            # VALIDATE EXTRACTED DATA
            # ------------------------------------

            for field_name, value in extracted_data.items():

                if field_name not in fields:
                    continue

                rules = fields[field_name]

                errors = (
                    self.validator
                    .validate_field(
                        field_name,
                        value,
                        rules
                    )
                )

                if errors:

                    validation_errors[
                        field_name
                    ] = errors

                    continue

                current_state = (
                    self.state_manager
                    .update_state(
                        current_state,
                        {
                            field_name: value
                        }
                    )
                )

        # ----------------------------------------
        # VALIDATE CURRENT STATE
        # ----------------------------------------

        for field_name, rules in fields.items():

            value = current_state.get(
                field_name
            )

            if value is None or value == "":
                continue

            errors = (
                self.validator
                .validate_field(
                    field_name,
                    value,
                    rules
                )
            )

            if errors:

                validation_errors[
                    field_name
                ] = errors

        # ----------------------------------------
        # FIND MISSING FIELDS
        # ----------------------------------------

        missing_fields = (
            self.missing_detector
            .get_missing_fields(
                schema,
                current_state
            )
        )

        # ----------------------------------------
        # PLAN
        # ----------------------------------------

        action_plan = (
            self.planner
            .next_question(
                validation_errors,
                missing_fields
            )
        )

        # ----------------------------------------
        # RESPONSE
        # ----------------------------------------

        response = (
            self.response_generator
            .generate(
                action_plan,
                schema
            )
        )

        # ----------------------------------------
        # SAVE STATE
        # ----------------------------------------

        save_conversation(
            session_id,
            form_name,
            current_state
        )

        # ----------------------------------------
        # SAVE COMPLETED FORM
        # ----------------------------------------

        if (
            action_plan.get("action")
            == "COMPLETE_FORM"
        ):

            save_submission(
                session_id,
                form_name,
                current_state
            )

        return {
            "response": response,
            "current_state": current_state,
            "validation_errors": validation_errors,
            "action_plan": action_plan,
            "missing_fields": missing_fields
        }