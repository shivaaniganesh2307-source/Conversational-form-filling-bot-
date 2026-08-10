class ResponseGenerator:
    def __init__(self):
        # Friendly field names for better prompt readability
        self.field_labels = {
            "first_name": "first name",
            "last_name": "last name",
            "email": "email address",
            "phone_number": "phone number",
            "country": "country",
            "is_student": "student status",
            "university_name": "university name"
        }

    def generate(self, action_plan: dict, schema: dict) -> str:
        action = action_plan.get("action")
        target_field = action_plan.get("target_field") or action_plan.get("field")

        # Get a user-friendly label if target_field is present
        friendly_name = self.field_labels.get(target_field, target_field) if target_field else ""
        if action in ["ASK_MISSING_FIELD", "REQUEST_MISSING_FIELD"]:

        #if action == "ASK_MISSING_FIELD":
            if friendly_name:
                return f"Please provide your {friendly_name}."
            return "Please provide the missing information to continue."

        elif action in ["CORRECT_FIELD", "CORRECT_VALIDATION_ERROR"]:
        #elif action == "CORRECT_FIELD":
            errors = action_plan.get("errors", [])
            error_msg = " ".join(errors) if errors else "invalid value."
            return f"There is an issue with your {friendly_name}: {error_msg}"

        elif action == "CONFIRM_LOW_CONFIDENCE":
            val = action_plan.get("value")
            return f"Just to confirm, is your {friendly_name} '{val}'?"

        elif action == "COMPLETE_FORM":
            return "Thank you! All information has been collected and your form submission is complete."

        # Catch-all fallback
        return "How can I help you complete your form?"