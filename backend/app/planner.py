class Planner:

    def next_question(
        self,
        validation_errors,
        missing_fields,
        low_confidence_fields
    ):

        # 1. Fix validation errors first
        if validation_errors:

            field_name = list(validation_errors.keys())[0]

            return {
                "action": "CORRECT_VALIDATION_ERROR",
                "field": field_name,
                "messages": validation_errors[field_name]
            }

        # 2. Ask for missing field
        if missing_fields:

            return {
                "action": "REQUEST_MISSING_FIELD",
                "field": missing_fields[0]
            }

        # 3. Confirm low confidence
        if low_confidence_fields:

            field_name, value = low_confidence_fields[0]

            return {
                "action": "CONFIRM_LOW_CONFIDENCE",
                "field": field_name,
                "unconfirmed_value": value
            }

        # 4. Everything is complete
        return {
            "action": "COMPLETE_FORM"
        }