class Planner:

    def next_question(
        self,
        validation_errors,
        missing_fields,
        low_confidence_fields
    ):

        # --------------------------------
        # 1. Validation error
        # --------------------------------

        if validation_errors:

            field_name = list(
                validation_errors.keys()
            )[0]

            return {
                "action": "CORRECT_VALIDATION_ERROR",
                "target_field": field_name,
                "field" : field_name,
                "messages": validation_errors[field_name]
            }

        # --------------------------------
        # 2. Missing field
        # --------------------------------

        if missing_fields:

            return {
                "action": "REQUEST_MISSING_FIELD",
                "target_field": missing_fields[0]
            }

        # --------------------------------
        # 3. Low confidence
        # --------------------------------

        if low_confidence_fields:

            field_name, value = low_confidence_fields[0]

            return {
                "action": "CONFIRM_LOW_CONFIDENCE",
                "field": field_name,
                "unconfirmed_value": value
            }

        # --------------------------------
        # 4. Everything complete
        # --------------------------------

        return {
            "action": "COMPLETE_FORM"
        }