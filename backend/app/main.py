from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from .db import (
        init_tables,
        get_saved_conversation,
        save_conversation,
        save_submissions,
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
        save_submissions,
    )
    from backend.app.schema_loader import SchemaLoader
    from backend.app.extractor import LLMExtractor
    from backend.app.validator import FormValidator
    from backend.app.response_generator import ResponseGenerator
    from backend.app.confidence_engine import ConfidenceEngine
    from backend.app.missing_field import MissingFieldDetector
    from backend.app.state_manager import StateManager
    from backend.app.planner import Planner


# ---------------------------------------------------------
# Flask setup
# ---------------------------------------------------------

app = Flask(__name__)

CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=True
)


# ---------------------------------------------------------
# Initialize database
# ---------------------------------------------------------

try:
    init_tables()
except Exception as e:
    print(f"[WARNING] Could not initialize DB tables: {e}")


# ---------------------------------------------------------
# Initialize application components
# ---------------------------------------------------------

extractor = LLMExtractor()
response_generator = ResponseGenerator()
planner = Planner()
state_manager = StateManager()
missing_detector = MissingFieldDetector()
schema_loader = SchemaLoader()
confidence_engine = ConfidenceEngine()
validator = FormValidator()


# ---------------------------------------------------------
# GET AVAILABLE FORMS
# ---------------------------------------------------------

@app.route("/api/forms", methods=["GET"])
@app.route("/api/forms/", methods=["GET"])
def get_forms():

    try:
        available_forms = schema_loader.get_available_forms()

    except Exception as e:
        print("[FORMS ERROR]", e)
        available_forms = []

    return jsonify({
        "forms": available_forms
    })


# ---------------------------------------------------------
# CHAT ENDPOINT
# ---------------------------------------------------------

@app.route("/api/chat", methods=["POST", "OPTIONS"])
@app.route("/api/chat/", methods=["POST", "OPTIONS"])
def chat():

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return "", 200


    # -----------------------------------------------------
    # Read request
    # -----------------------------------------------------

    data = request.get_json() or {}

    session_id = data.get("session_id")
    form_name = data.get("form_name")
    user_message = data.get("message", "").strip()


    # -----------------------------------------------------
    # Validate request
    # -----------------------------------------------------

    if not session_id:
        return jsonify({
            "error": "session_id is required"
        }), 400

    if not form_name:
        return jsonify({
            "error": "form_name is required"
        }), 400


    # -----------------------------------------------------
    # Load schema
    # -----------------------------------------------------

    schema = schema_loader.load_schema(form_name)

    print("\n========== SCHEMA ==========")
    print(schema)
    print("============================\n")


    if not isinstance(schema, dict) or "fields" not in schema:

        return jsonify({
            "error": "Could not load form schema."
        }), 500


    fields = schema.get("fields", {})


    # -----------------------------------------------------
    # Load previous state
    # -----------------------------------------------------

    current_state = get_saved_conversation(session_id)


    # If this is a brand-new conversation
    if not current_state:

        current_state = state_manager.create_empty_space(form_name)

        save_conversation(
            session_id,
            form_name,
            current_state
        )


    # -----------------------------------------------------
    # Find missing fields BEFORE processing message
    # -----------------------------------------------------

    missing_fields = missing_detector.get_missing_fields(
        form_name,
        current_state
    )


    # Make sure detector returned a list
    if not isinstance(missing_fields, list):
        missing_fields = []


    # -----------------------------------------------------
    # Determine which field we are currently asking for
    # -----------------------------------------------------

    current_field = None

    if missing_fields:

        current_field = missing_fields[0]


    print("\n========== CURRENT FIELD ==========")
    print(current_field)
    print("===================================\n")


    validation_errors = {}


    # =====================================================
    # PROCESS USER MESSAGE
    # =====================================================

    if user_message:

        print("\n========== USER MESSAGE ==========")
        print(user_message)
        print("==================================\n")

        if any(word in user_message.lower() for word in ["change", "update", "edit", "fix", "wrong", "mistake", "error"]):
            for field_key in fields.keys():
                if field_key in user_message.lower() or field_key.replace("_", " ") in user_message.lower():
                    # Clear that field in the current state
                    current_state[field_key] = ""
                    
                    # Save the updated state
                    save_conversation(session_id, form_name, current_state)
                    
                    # Recalculate missing fields so it points to the edited field
                    missing_fields = missing_detector.get_missing_fields(form_name, current_state)
                    
                    return jsonify({
                        "response": f"No problem! Let's update your {field_key.replace('_', ' ')}. What should it be?",
                        "current_state": current_state,
                        "validation_errors": {},
                        "action_plan": {"action": "REQUEST_MISSING_FIELD", "field": field_key},
                        "missing_fields": missing_fields
                    })


        # -------------------------------------------------
        # Send message to Qwen
        # -------------------------------------------------
        '''
        result = extractor.extract_fields(
            user_message=user_message,
            schema=schema,
            current_state=current_state,
            current_field=current_field
        )
        '''
        # -------------------------------------------------
        # Deterministic Pre-Filter (0 Tokens / Government Safe)
        # -------------------------------------------------
        # -------------------------------------------------
        # Deterministic Pre-Filter (0 Tokens / Government Safe)
        # -------------------------------------------------
        # -------------------------------------------------
        # Deterministic Pre-Filter (0 Tokens / Government Safe)
        # -------------------------------------------------
        extracted_data = {}
        intent = "answer"
        
        cleaned_value, handled = normalize_user_input(current_field, user_message) if current_field else (user_message, False)

        if handled:
            print(f"[DETERMINISTIC FILTER] Handled '{user_message}' for '{current_field}' -> {cleaned_value}")
            if cleaned_value == "NOT_PROVIDED":
                # CRITICAL: Do NOT extract or pass anything to the validator for this field!
                extracted_data = {}
                intent = "skip"
            else:
                extracted_data = {current_field: cleaned_value}
                
            # Skip the LLM call entirely when deterministic filter handles it
            result = {"extracted_data": extracted_data, "intent": intent}
        else:
            # -------------------------------------------------
            # Send message to Qwen ONLY if deterministic filter didn't catch it
            # -------------------------------------------------
            result = extractor.extract_fields(
                user_message=user_message,
                schema=schema,
                current_state=current_state,
                current_field=current_field
            )

        print("\n========== EXTRACTOR RESULT ==========")
        print(result)
        print("=======================================\n")

        extracted_data = result.get("extracted_data", {})
        intent = result.get("intent", "chat")
        
        
        '''
        print("\n========== EXTRACTOR RESULT ==========")
        print(result)
        print("=======================================\n")


        extracted_data = result.get(
            "extracted_data",
            {}
        )

        intent = result.get(
            "intent",
            "chat"
        )

        '''
        # -------------------------------------------------
        # Safety check
        # -------------------------------------------------

        if not isinstance(extracted_data, dict):
            extracted_data = {}


        # -------------------------------------------------
        # FALLBACK: Catch conversational answers to current field
        # -------------------------------------------------
        
        if not extracted_data and current_field and user_message:
            cleaned_msg = user_message.strip()
            for prefix in ["its ", "it's ", "my name is ", "i am ", "im "]:
                if cleaned_msg.lower().startswith(prefix):
                    cleaned_msg = cleaned_msg[len(prefix):].strip()
            
            if cleaned_msg:
                extracted_data = {current_field: cleaned_msg}
                intent = "answer"
        


        # -------------------------------------------------
        # IMPORTANT:
        #
        # If Qwen says chat, do NOT save anything.
        # -------------------------------------------------

        if intent == "chat":

            extracted_data = {}


        # -------------------------------------------------
        # Process extracted fields
        # -------------------------------------------------

        for field_name, value in extracted_data.items():

            # Ignore fields that do not exist in schema
            if field_name not in fields:
                print(
                    f"[WARNING] Qwen returned unknown field: "
                    f"{field_name}"
                )
                continue


            rules = fields.get(
                field_name,
                {}
            )


            # -------------------------------------------------
            # Validate BEFORE saving
            # -------------------------------------------------

            errors = validator.validate_field(
                field_name,
                value,
                rules
            )


            if errors:

                validation_errors[field_name] = errors

                print(
                    f"[VALIDATION FAILED] "
                    f"{field_name}: {errors}"
                )

                continue


            # -------------------------------------------------
            # VALID VALUE
            # -------------------------------------------------

            print(
                f"[VALIDATION PASSED] "
                f"{field_name} = {value}"
            )


            current_state = state_manager.update_state(
                current_state,
                {
                    field_name: value
                }
            )


    # =====================================================
    # VALIDATE EVERYTHING CURRENTLY IN STATE
    # =====================================================

    for field_name, rules in fields.items():

        value = current_state.get(field_name)


        # Don't validate empty optional fields
        if value is None or value == "":
            continue


        errors = validator.validate_field(
            field_name,
            value,
            rules
        )


        if errors:

            validation_errors[field_name] = errors


    # =====================================================
    # FIND MISSING FIELDS AGAIN
    # =====================================================

    missing_fields = missing_detector.get_missing_fields(
        form_name,
        current_state
    )


    if not isinstance(missing_fields, list):
        missing_fields = []


    # =====================================================
    # CONFIDENCE
    # =====================================================

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


    # =====================================================
    # DEBUG
    # =====================================================

    print("\n------ DEBUG ------")
    print("Current State:", current_state)
    print("Missing Fields:", missing_fields)
    print("Validation Errors:", validation_errors)
    print("Confidence Scores:", confidence_scores)
    print("Low Confidence:", low_confidence_fields)
    print("-------------------\n")


    # =====================================================
    # PLAN NEXT ACTION
    # =====================================================

    action_plan = planner.next_question(
        validation_errors,
        missing_fields,
        low_confidence_fields
    )


    print("\n========== ACTION PLAN ==========")
    print(action_plan)
    print("=================================\n")


    # =====================================================
    # GENERATE RESPONSE
    # =====================================================

    bot_response = response_generator.generate(
        action_plan,
        schema
    )


    # =====================================================
    # SAVE CONVERSATION
    # =====================================================

    save_conversation(
        session_id,
        form_name,
        current_state
    )


    # =====================================================
    # SAVE SUBMISSION IF COMPLETE
    # =====================================================

    if action_plan.get("action") == "COMPLETE_FORM":

        save_submissions(
            session_id,
            form_name,
            current_state
        )


    # =====================================================
    # RETURN RESPONSE
    # =====================================================

    return jsonify({

        "response": bot_response,

        "current_state": current_state,

        "validation_errors": validation_errors,

        "action_plan": action_plan,

        "missing_fields": missing_fields

    })


# ---------------------------------------------------------
# START SERVER
# ---------------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )