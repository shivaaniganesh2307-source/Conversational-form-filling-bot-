import os
from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from .db import (
        init_tables,
        load_form_schema_from_db,
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
except ImportError:
    from backend.app.db import (
        init_tables,
        load_form_schema_from_db,
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

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

try:
    init_tables()
except Exception as e:
    print(f"[WARNING] Could not initialize DB tables on import: {e}")

extractor = LLMExtractor()
validator = FormValidator()
response_generator = ResponseGenerator()
planner = Planner()
state_manager = StateManager()
missing_detector = MissingFieldDetector()
schema_loader = SchemaLoader()
confidence_engine = ConfidenceEngine()


@app.route("/api/forms", methods=["GET"])
def get_forms():
    """Dynamically return list of all available form names."""
    try:
        available_forms = schema_loader.get_available_forms()
    except Exception as e:
        available_forms = ["user_registration"]
    return jsonify({"forms": available_forms})


@app.route("/api/chat", methods=["POST", "OPTIONS"])
@app.route("/api/chat/", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json() or {}
    session_id = data.get("session_id")
    form_name = data.get("form_name")
    user_message = data.get("message", "").strip()

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    if not form_name:
        return jsonify({"error": "form_name is required. Please select a form."}), 400

    # Load form schema dynamically based on selected form_name
    schema = schema_loader.load_schema(form_name)

    # Load previous conversation state
    current_state = get_saved_conversation(session_id)
    if not current_state:
        current_state = state_manager.create_empty_space(form_name)

    # Detect current missing fields prior to extraction
    missing_fields = missing_detector.get_missing_fields(form_name, current_state)

    # Extract info if user sent a message
    if user_message != "":
        try:
            result = extractor.extract_fields(user_message, schema, missing_fields=missing_fields)
        except TypeError:
            result = extractor.extract_fields(user_message, schema)

        extracted_data = result.get("extracted_data", {})
        
        # Smart Fallback logic
        if not extracted_data and missing_fields:
            user_str = user_message.strip()
            
            if "@" in user_str and "." in user_str and "email" in missing_fields:
                extracted_data = {"email": user_str}
            elif user_str.replace("-", "").replace("+", "").replace(" ", "").isdigit() and "phone_number" in missing_fields:
                extracted_data = {"phone_number": user_str}
            else:
                target_field = missing_fields[0]
                extracted_data = {target_field: user_str}

        current_state = state_manager.update_state(current_state, extracted_data)

    # Validate fields against schema rules
    validation_errors = {}
    fields = schema.get("fields", {}) if isinstance(schema, dict) else {}
    for field_name, rules in fields.items():
        value = current_state.get(field_name)
        errors = validator.validate_field(field_name, value, rules)
        if errors:
            validation_errors[field_name] = errors

    # Re-detect missing fields & evaluate confidence
    missing_fields = missing_detector.get_missing_fields(form_name, current_state)
    confidence_scores = confidence_engine.confidence_evaluation(current_state)
    low_confidence_fields = confidence_engine.low_confidence_fields(confidence_scores)

    # Plan next question/action
    action_plan = planner.next_question(
        validation_errors, missing_fields, low_confidence_fields
    )

    # Generate bot response string
    bot_response = response_generator.generate(action_plan, schema)

    # Save state / submissions safely in correct foreign-key order
    save_conversation(session_id, form_name, current_state)

    if action_plan.get("action") == "COMPLETE_FORM":
        save_submissions(session_id, form_name, current_state)

    return jsonify({
        "response": bot_response,
        "current_state": current_state,
        "validation_errors": validation_errors,
        "action_plan": action_plan
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)