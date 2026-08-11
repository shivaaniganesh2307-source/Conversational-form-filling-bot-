import json
import requests


class LLMExtractor:

    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "qwen2.5:3b"

    def extract_fields(
        self,
        user_message,
        schema,
        current_state=None,
        current_field=None
    ):

        current_state = (
            current_state
            if isinstance(current_state, dict)
            else {}
        )

        fields = schema.get("fields", {})

        if not isinstance(fields, dict):
            return {
                "extracted_data": {},
                "confidence_scores": {},
                "intent": "chat"
            }

        # -----------------------------------------
        # Build dynamic field information
        # -----------------------------------------

        field_information = {}

        for field_name, rules in fields.items():

            if not isinstance(rules, dict):
                continue

            field_information[field_name] = {
                "label": rules.get("label", field_name),
                "type": rules.get("type", "string"),
                "required": rules.get("required", False),
                "choices": rules.get("choices"),
                "condition": rules.get("condition")
            }

        # -----------------------------------------
        # Only send fields that are useful
        # -----------------------------------------

        relevant_state = {
            field: value
            for field, value in current_state.items()
            if value not in [None, ""]
        }

        # -----------------------------------------
        # Build prompt
        # -----------------------------------------

        prompt = f"""
You extract information from a user's message and fill a form.

Return ONLY valid JSON.

FORM FIELDS:
{json.dumps(field_information, separators=(",", ":"))}

CURRENT VALUES:
{json.dumps(relevant_state, separators=(",", ":"))}

CURRENT FIELD:
{current_field}

USER MESSAGE:
{user_message}

RULES:

1. Extract information explicitly provided by the user.

2. A user may provide multiple fields in one message.

3. Only return fields that exist in FORM FIELDS.

4. Never invent information.

5. If the user provides a full name and the form contains separate
   fields for first name and last name, split the full name into
   those fields.

6. The CURRENT FIELD is the field the conversation is currently
   asking about, so prioritize extracting that field.

7.However, the CURRENT FIELD does NOT restrict extraction.
   If the user provides information for other form fields in
   the same message, extract those fields too.

8.Extract ALL clearly provided form information from the user's
   message, even when the user answers more than one field at once.

9.If the user provides a person's name as an emergency contact,
   contact, supervisor, parent, guardian, or similar relationship,
   match it to the appropriate contact-name field in the schema.

10.If the user provides a phone number and the schema contains an
   appropriate phone/contact-phone field, extract it.

11. Never ignore information simply because it is not related to
    the CURRENT FIELD.

12. Do not put the entire full name into first_name when a separate
   last_name field exists.

13. If the user provides multiple pieces of information in one
   message, extract every piece that clearly matches a form field.

14. Evaluate each statement independently. One field being true
   does not imply that another field is false.

15. If the user provides information about a field, assign it to
   the appropriate field based on the field label and schema.

16. If the user answers the current field with a short answer,
   assign that answer to the current field.

17. If the user says they do not know, want to skip, or will provide
    the information later, do not invent a value.

18. For boolean fields, determine the value from the meaning of
   the user's statement.

   A positive statement means true.
   A negative statement means false.

   Examples:
   "I have it" -> true
   "I don't have it" -> false
   "I take it" -> true
   "I don't take it" -> false
   "Yes" -> true
   "No" -> false

   Pay attention to negation words such as:
   don't, do not, doesn't, does not, never, no, none.

   Do not assume false merely because the user did not explicitly
   say "yes".

19. For number fields, return a number.

20. Do not return fields with null values.

21. Do not return fields with empty string values.

22. If the message contains no form information, return an empty
    extracted_data object.

Return exactly:

{{
    "extracted_data": {{}},
    "confidence_scores": {{}},
    "intent": "answer"
}}

intent must be one of:

answer
update
chat
"""

        try:

            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0
                    }
                },
                timeout=120
            )

            response.raise_for_status()

            result = response.json()

            raw_response = result.get(
                "response",
                "{}"
            ).strip()

            print("\n========== RAW LLM RESPONSE ==========")
            print(raw_response)
            print("=======================================\n")

            parsed = json.loads(raw_response)

            if not isinstance(parsed, dict):
                raise ValueError(
                    "LLM response is not a JSON object"
                )

            extracted_data = parsed.get(
                "extracted_data",
                {}
            )

            confidence_scores = parsed.get(
                "confidence_scores",
                {}
            )

            intent = parsed.get(
                "intent",
                "chat"
            )

            if not isinstance(extracted_data, dict):
                extracted_data = {}

            if not isinstance(confidence_scores, dict):
                confidence_scores = {}

            # -----------------------------------------
            # SECURITY:
            # Only schema fields are allowed
            # -----------------------------------------

            extracted_data = {
                field: value
                for field, value in extracted_data.items()
                if field in fields
                and value not in [None, ""]
            }

            confidence_scores = {
                field: score
                for field, score in confidence_scores.items()
                if field in extracted_data
            }

            # -----------------------------------------
            # Normalize confidence
            # -----------------------------------------

            for field in list(confidence_scores.keys()):

                try:
                    score = float(
                        confidence_scores[field]
                    )

                    confidence_scores[field] = max(
                        0.0,
                        min(1.0, score)
                    )

                except (TypeError, ValueError):

                    confidence_scores.pop(
                        field,
                        None
                    )

            # -----------------------------------------
            # Validate intent
            # -----------------------------------------

            if intent not in {
                "answer",
                "update",
                "chat"
            }:

                intent = (
                    "answer"
                    if extracted_data
                    else "chat"
                )

            return {
                "extracted_data": extracted_data,
                "confidence_scores": confidence_scores,
                "intent": intent
            }

        except requests.exceptions.Timeout:

            print(
                "[EXTRACTOR ERROR] Ollama request timed out."
            )

            return {
                "extracted_data": {},
                "confidence_scores": {},
                "intent": "chat"
            }

        except Exception as e:

            print(
                f"[EXTRACTOR ERROR] {e}"
            )

            return {
                "extracted_data": {},
                "confidence_scores": {},
                "intent": "chat"
            }