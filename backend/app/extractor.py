# Connects our application with Qwen LLM using Ollama
# Extracts form answers from user messages and converts them into JSON

import json
import requests


class LLMExtractor:

    def __init__(self):
        # Ollama API address
        self.ollama_url = "http://localhost:11434/api/generate"

    def extract_fields(
        self,
        user_message,
        schema,
        current_state=None,
        current_field=None
    ):

        if current_state is None:
            current_state = {}

        fields = schema.get("fields", {})

        # Give Qwen only the useful information about each field
        field_information = {}

        for field_name, rules in fields.items():
            field_information[field_name] = {
                "type": rules.get("type"),
                "required": rules.get("required", False)
            }

        prompt = f"""
You are an intelligent conversational form-filling assistant.

Your job is to understand the user's message and determine
whether they are providing information for a form.

FORM FIELDS:
{json.dumps(field_information, indent=2)}

CURRENT FORM STATE:
{json.dumps(current_state, indent=2)}

CURRENT FIELD BEING REQUESTED:
{current_field}

USER MESSAGE:
"{user_message}"

Follow these rules carefully:

1. Only extract information when the user is actually
   providing information.

2. The CURRENT FIELD BEING REQUESTED is very important.

3. If the current field is "first_name" and the user says:

   "Shivaani"

   then extract:

   {{
       "first_name": "Shivaani"
   }}

4. If the current field is "last_name" and the user says:

   "Ganesh"

   then extract:

   {{
       "last_name": "Ganesh"
   }}

5. If the user says:

   "my first name is Shivaani"

   extract:

   {{
       "first_name": "Shivaani"
   }}

6. If the user says:

   "my last name is Ganesh"

   extract:

   {{
       "last_name": "Ganesh"
   }}

7. If the user says:

   "actually my first name is Sarah"

   this means they are correcting/updating their first name.

   Extract:

   {{
       "first_name": "Sarah"
   }}

   and use intent "update".

8. If the user says something conversational such as:

   "hello"
   "hi"
   "ok"
   "thanks"
   "help me"
   "can I enter my first name again?"
   "what do you need?"

   DO NOT put that sentence into a form field.

9. If the user asks a question, do not treat the question
   itself as a form answer.

10. Never invent information.

11. Never randomly assign a message to a field.

12. If you are not confident that the user provided a value,
   return an empty extracted_data object.

13. If CURRENT FIELD BEING REQUESTED is "first_name" and the
    user provides a normal-looking name such as "Shivaani",
    treat it as the first name.

14. If CURRENT FIELD BEING REQUESTED is "last_name" and the
    user provides a normal-looking name such as "Ganesh",
    treat it as the last name.

15. If the user explicitly mentions a different field,
    use that field instead.

16. The intent must be one of:

    "answer"
    "update"
    "chat"

17. Return ONLY valid JSON.

Examples:

Example 1:

CURRENT FIELD:
first_name

USER:
Shivaani

RETURN:

{{
    "extracted_data": {{
        "first_name": "Shivaani"
    }},
    "confidence_scores": {{
        "first_name": 0.95
    }},
    "intent": "answer"
}}


Example 2:

CURRENT FIELD:
first_name

USER:
my first name is Shivaani

RETURN:

{{
    "extracted_data": {{
        "first_name": "Shivaani"
    }},
    "confidence_scores": {{
        "first_name": 0.98
    }},
    "intent": "answer"
}}


Example 3:

CURRENT FIELD:
first_name

USER:
actually change my first name to Sarah

RETURN:

{{
    "extracted_data": {{
        "first_name": "Sarah"
    }},
    "confidence_scores": {{
        "first_name": 0.98
    }},
    "intent": "update"
}}


Example 4:

CURRENT FIELD:
first_name

USER:
hello

RETURN:

{{
    "extracted_data": {{}},
    "confidence_scores": {{}},
    "intent": "chat"
}}


Example 5:

CURRENT FIELD:
first_name

USER:
can I enter my first name again?

RETURN:

{{
    "extracted_data": {{}},
    "confidence_scores": {{}},
    "intent": "chat"
}}


Example 6:

CURRENT FIELD:
employee_id

USER:
12345

RETURN:

{{
    "extracted_data": {{
        "employee_id": "12345"
    }},
    "confidence_scores": {{
        "employee_id": 0.98
    }},
    "intent": "answer"
}}

Now analyze the user's message.

Return ONLY JSON.
"""

        try:

            response = requests.post(
                self.ollama_url,
                json={
                    "model": "phi3:3.8b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )

            response.raise_for_status()

            result = response.json()

            answer = result.get("response", "{}").strip()

            print("\n========== QWEN RAW RESPONSE ==========")
            print(answer)
            print("========================================\n")

            # Remove markdown if Qwen returns ```json ... ```
            if "```json" in answer:
                answer = answer.split("```json", 1)[1]
                answer = answer.split("```", 1)[0].strip()

            elif "```" in answer:
                answer = answer.split("```", 1)[1]
                answer = answer.split("```", 1)[0].strip()

            parsed = json.loads(answer)

            # Make sure Qwen returned a dictionary
            if not isinstance(parsed, dict):
                raise ValueError("Qwen returned invalid JSON")

            extracted_data = parsed.get(
                "extracted_data",
                {}
            )
            # Only allow fields that actually exist in the schema
            extracted_data = {
                field_name: value
                for field_name, value in extracted_data.items()
                if field_name in fields
            }

            confidence_scores = parsed.get(
                "confidence_scores",
                {}
            )

            intent = parsed.get(
                "intent",
                "chat"
            )

            # Safety checks
            if not isinstance(extracted_data, dict):
                extracted_data = {}

            if not isinstance(confidence_scores, dict):
                confidence_scores = {}

            if intent not in [
                "answer",
                "update",
                "chat"
            ]:
                intent = "chat"

            return {
                "extracted_data": extracted_data,
                "confidence_scores": confidence_scores,
                "intent": intent
            }

        except Exception as e:

            print("\n========== QWEN ERROR ==========")
            print(str(e))
            print("=================================\n")

            return {
                "extracted_data": {},
                "confidence_scores": {},
                "intent": "chat"
            }