class Planner:
    def next_question(self, validation_errors: dict, missing_fields: list, low_confidence_fields: list) -> dict:
        # 1. Prioritize validation errors
        if validation_errors:
            field_name = list(validation_errors.keys())[0]
            return {
                "action": "CORRECT_FIELD",
                "target_field": field_name,
                "errors": validation_errors[field_name]
            }

        # 2. Ask for missing fields
        if missing_fields:
            return {
                "action": "ASK_MISSING_FIELD",
                "target_field": missing_fields[0]
            }

        # 3. Confirm low confidence fields
        if low_confidence_fields:
            field_name, val = low_confidence_fields[0]
            return {
                "action": "CONFIRM_LOW_CONFIDENCE",
                "target_field": field_name,
                "value": val
            }

        # 4. If all fields are present and valid, complete form
        return {
            "action": "COMPLETE_FORM"
        }