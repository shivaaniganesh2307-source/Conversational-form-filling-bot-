from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from .db import init_tables, get_session
    from .schema_loader import SchemaLoader
    from .conversation_engine import ConversationEngine

except ImportError:
    from backend.app.db import init_tables, get_session
    from backend.app.schema_loader import SchemaLoader
    from backend.app.conversation_engine import ConversationEngine


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)

CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=True
)


# ============================================================
# DATABASE
# ============================================================

try:
    init_tables()
except Exception as error:
    print(f"[WARNING] Could not initialize DB tables: {error}")


# ============================================================
# COMPONENTS
#
# main.py is intentionally thin -- all conversation logic lives
# in ConversationEngine so there is exactly one implementation
# of "what happens on a chat turn".
# ============================================================

schema_loader = SchemaLoader()
engine = ConversationEngine()


# ============================================================
# GET AVAILABLE FORMS
# ============================================================

@app.route("/api/forms", methods=["GET"])
@app.route("/api/forms/", methods=["GET"])
def get_forms():

    try:
        available_forms = schema_loader.get_available_forms()
    except Exception as error:
        print(f"[FORMS ERROR] {error}")
        available_forms = []

    # Each entry looks like {"id": "employee_form", "name": "Employee Form"}
    return jsonify({"forms": available_forms})


# ============================================================
# GET A SESSION'S LIVE DETAILS (resume / "my forms" list)
# ============================================================
#
# The frontend remembers which session_ids belong to this browser
# (localStorage) -- it doesn't need the backend to know "whose"
# sessions these are. This just answers "what's the live status and
# saved data for this one session_id", which the frontend calls once
# per remembered session to build the "My Forms" list and to resume
# a session's chat.
# ============================================================

@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session_route(session_id):

    session = get_session(session_id)

    if not session:
        return jsonify({"error": "Session not found"}), 404

    schema = schema_loader.load_schema(session["form_id"])
    session["form_name"] = (
        schema.get("form_name", session["form_id"]) if schema else session["form_id"]
    )
    session["session_id"] = session_id

    return jsonify(session)


# ============================================================
# CHAT
# ============================================================

@app.route("/api/chat", methods=["POST", "OPTIONS"])
@app.route("/api/chat/", methods=["POST", "OPTIONS"])
def chat():

    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json() or {}

    session_id = data.get("session_id")
    form_name = data.get("form_name")
    user_message = str(data.get("message", "")).strip()

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    if not form_name:
        return jsonify({"error": "form_name is required"}), 400

    result = engine.process(session_id, form_name, user_message)

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
