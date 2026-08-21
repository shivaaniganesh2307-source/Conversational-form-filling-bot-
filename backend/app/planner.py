class Planner:
    """
    Determines the next action based on the current validation and
    form state. Contains no form-specific logic -- everything
    form-specific comes from the schema.
    """

    def next_question(self, validation_errors=None, missing_fields=None, low_confidence_fields=None):

        if not isinstance(validation_errors, dict):
            validation_errors = {}

        if not isinstance(missing_fields, list):
            missing_fields = []

        if not isinstance(low_confidence_fields, list):
            low_confidence_fields = []

        if validation_errors:
            field_name = next(iter(validation_errors))
            messages = validation_errors.get(field_name, [])
            if not isinstance(messages, list):
                messages = [str(messages)]
            return {
                "action": "CORRECT_VALIDATION_ERROR",
                "field": field_name,
                "messages": messages
            }

        if missing_fields:
            field_name = missing_fields[0]
            return {
                "action": "REQUEST_MISSING_FIELD",
                "field": field_name
            }

        if low_confidence_fields:
            first_item = low_confidence_fields[0]
            if isinstance(first_item, (list, tuple)) and len(first_item) >= 2:
                field_name = first_item[0]
                value = first_item[1]
                return {
                    "action": "CONFIRM_LOW_CONFIDENCE",
                    "field": field_name,
                    "unconfirmed_value": value
                }

        return {"action": "COMPLETE_FORM"}
