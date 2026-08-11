from flask import Flask, request, jsonify
from flask_cors import CORS

try:

    from .db import (
        init_tables,
        get_saved_conversation,
        save_conversation,
        save_submission,
    )

    from .schema_loader import SchemaLoader
    from .extractor import LLMExtractor
    from .validator import FormValidator
    from .response_generator import ResponseGenerator
    from .confidence_engine import ConfidenceEngine
    from .missing_field import MissingFieldDetector
    from .state_manager import StateManager
    from .planner import Planner
    from .conversational_filter import normalize_user_input

except ImportError:

    from backend.app.db import (
        init_tables,
        get_saved_conversation,
        save_conversation,
        save_submission,
    )

    from backend.app.schema_loader import SchemaLoader
    from backend.app.extractor import LLMExtractor
    from backend.app.validator import FormValidator
    from backend.app.response_generator import ResponseGenerator
    from backend.app.confidence_engine import ConfidenceEngine
    from backend.app.missing_field import MissingFieldDetector
    from backend.app.state_manager import StateManager
    from backend.app.planner import Planner
    from backend.app.conversational_filter import normalize_user_input


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*"
        }
    },
    supports_credentials=True
)


# ============================================================
# DATABASE
# ============================================================

try:

    init_tables()

except Exception as error:

    print(
        f"[WARNING] Could not initialize DB tables: {error}"
    )


# ============================================================
# COMPONENTS
# ============================================================

extractor = LLMExtractor()
response_generator = ResponseGenerator()
planner = Planner()
state_manager = StateManager()
missing_detector = MissingFieldDetector()
schema_loader = SchemaLoader()
confidence_engine = ConfidenceEngine()
validator = FormValidator()


# ============================================================
# GET AVAILABLE FORMS
# ============================================================

@app.route(
    "/api/forms",
    methods=["GET"]
)
@app.route(
    "/api/forms/",
    methods=["GET"]
)
def get_forms():

    try:

        available_forms = (
            schema_loader.get_available_forms()
        )

    except Exception as error:

        print(
            f"[FORMS ERROR] {error}"
        )

        available_forms = []

    return jsonify({
        "forms": available_forms
    })


# ============================================================
# CHAT
# ============================================================

@app.route(
    "/api/chat",
    methods=["POST", "OPTIONS"]
)
@app.route(
    "/api/chat/",
    methods=["POST", "OPTIONS"]
)
def chat():

    # --------------------------------------------------------
    # CORS
    # --------------------------------------------------------

    if request.method == "OPTIONS":

        return "", 200

    # --------------------------------------------------------
    # Request
    # --------------------------------------------------------

    data = request.get_json() or {}

    session_id = data.get(
        "session_id"
    )

    form_name = data.get(
        "form_name"
    )

    user_message = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    # --------------------------------------------------------
    # Request validation
    # --------------------------------------------------------

    if not session_id:

        return jsonify({
            "error": "session_id is required"
        }), 400

    if not form_name:

        return jsonify({
            "error": "form_name is required"
        }), 400

    # --------------------------------------------------------
    # Load schema
    # --------------------------------------------------------

    schema = schema_loader.load_schema(
        form_name
    )

    if not isinstance(schema, dict):

        return jsonify({
            "error": "Could not load form schema."
        }), 500

    fields = schema.get(
        "fields",
        {}
    )

    if not isinstance(fields, dict):

        return jsonify({
            "error": "Schema fields must be an object."
        }), 500

    # --------------------------------------------------------
    # Load state
    # --------------------------------------------------------

    current_state = get_saved_conversation(
        session_id
    )

    if not isinstance(
        current_state,
        dict
    ):

        current_state = {}

    # New conversation
    if not current_state:

        current_state = (
            state_manager.create_empty_space(
                form_name, schema
            )
        )

        save_conversation(
            session_id,
            form_name,
            current_state
        )

    # --------------------------------------------------------
    # Find current missing field
    # --------------------------------------------------------

    missing_fields = (
        missing_detector.get_missing_fields(
            form_name,
            current_state
        )
    )

    if not isinstance(
        missing_fields,
        list
    ):

        missing_fields = []

    current_field = (
        missing_fields[0]
        if missing_fields
        else None
    )

    validation_errors = {}

    # ========================================================
    # PROCESS USER MESSAGE
    # ========================================================

    if user_message:

        print(
            f"\n[USER] {user_message}"
        )

        # ----------------------------------------------------
        # Deterministic handling
        # ----------------------------------------------------

        handled = False
        extracted_data = {}
        intent = "chat"

        # Only use deterministic boolean processing when
        # the CURRENT FIELD is actually boolean.
        if current_field:

            current_rules = fields.get(
                current_field,
                {}
            )

            current_type = current_rules.get(
                "type"
            )

            if current_type == "boolean":

                cleaned_value, handled = (
                    normalize_user_input(
                        current_field,
                        user_message
                    )
                )

                if handled:

                    if cleaned_value == "NOT_PROVIDED":

                        extracted_data = {}
                        intent = "chat"

                    else:

                        if cleaned_value in {
                            "yes",
                            "true"
                        }:

                            cleaned_value = True

                        elif cleaned_value in {
                            "no",
                            "false"
                        }:

                            cleaned_value = False

                        extracted_data = {
                            current_field:
                                cleaned_value
                        }

                        intent = "answer"

        # ----------------------------------------------------
        # LLM extraction
        # ----------------------------------------------------

        if not handled:

            result = extractor.extract_fields(
                user_message=user_message,
                schema=schema,
                current_state=current_state,
                current_field=current_field
            )

            extracted_data = result.get(
                "extracted_data",
                {}
            )

            intent = result.get(
                "intent",
                "chat"
            )

        print(
            "\n[EXTRACTOR RESULT]"
        )

        print(
            extracted_data
        )

        # ----------------------------------------------------
        # Never save conversational text
        # ----------------------------------------------------

        if intent == "chat":

            extracted_data = {}

        # ----------------------------------------------------
        # Process every extracted field
        # ----------------------------------------------------

        for field_name, value in (
            extracted_data.items()
        ):

            # Security whitelist
            if field_name not in fields:

                print(
                    f"[WARNING] Ignoring unknown field: "
                    f"{field_name}"
                )

                continue

            rules = fields.get(
                field_name,
                {}
            )

            # ------------------------------------------------
            # Validate BEFORE updating state
            # ------------------------------------------------

            errors = (
                validator.validate_field(
                    field_name,
                    value,
                    rules
                )
            )

            if errors:

                validation_errors[
                    field_name
                ] = errors

                print(
                    f"[VALIDATION FAILED] "
                    f"{field_name}: {errors}"
                )

                continue

            # ------------------------------------------------
            # Valid value
            # ------------------------------------------------

            current_state = (
                state_manager.update_state(
                    current_state,
                    {
                        field_name: value
                    }
                )
            )

            print(
                f"[VALIDATION PASSED] "
                f"{field_name} = {value}"
            )

    # ========================================================
    # VALIDATE EXISTING STATE
    # ========================================================

    for field_name, rules in fields.items():

        value = current_state.get(
            field_name
        )

        if value in [
            None,
            ""
        ]:

            continue

        errors = (
            validator.validate_field(
                field_name,
                value,
                rules
            )
        )

        if errors:

            validation_errors[
                field_name
            ] = errors

    # ========================================================
    # MISSING FIELDS
    # ========================================================

    missing_fields = (
        missing_detector.get_missing_fields(
            form_name,
            current_state
        )
    )

    if not isinstance(
        missing_fields,
        list
    ):

        missing_fields = []

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence_scores = (
        confidence_engine.confidence_evaluation(
            current_state
        )
    )

    low_confidence_fields = (
        confidence_engine.low_confidence_fields(
            confidence_scores
        )
    )

    # ========================================================
    # PLAN
    # ========================================================

    action_plan = planner.next_question(
        validation_errors,
        missing_fields,
        low_confidence_fields
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    bot_response = (
        response_generator.generate(
            action_plan,
            schema
        )
    )

    # ========================================================
    # SAVE PROGRESS
    # ========================================================

    save_conversation(
        session_id,
        form_name,
        current_state
    )

    # ========================================================
    # SAVE COMPLETED FORM
    # ========================================================

    if action_plan.get(
        "action"
    ) == "COMPLETE_FORM":

        save_submission(
            session_id,
            
            current_state
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return jsonify({

        "response": bot_response,

        "current_state": current_state,

        "validation_errors":
            validation_errors,

        "action_plan":
            action_plan,

        "missing_fields":
            missing_fields

    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )