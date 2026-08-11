class ResponseGenerator:

    def generate(self, action_plan, schema):

        action = action_plan.get("action")

        target_field = (
            action_plan.get("field")
            or action_plan.get("target_field")
        )

        fields = schema.get("fields", {})

        field_label = target_field

        if (
            isinstance(fields, dict)
            and target_field in fields
            and isinstance(fields[target_field], dict)
        ):
            field_label = fields[target_field].get(
                "label",
                target_field
            )

        # -----------------------------
        # Validation error
        # -----------------------------

        if action == "CORRECT_VALIDATION_ERROR":

            messages = action_plan.get(
                "messages",
                []
            )

            error_message = " ".join(messages)

            return (
                f"There is an issue with your "
                f"{field_label}: "
                f"{error_message}"
            )

        # -----------------------------
        # Missing field
        # -----------------------------

        if action == "REQUEST_MISSING_FIELD":

            return (
                f"Please provide your "
                f"{field_label}."
            )

        # -----------------------------
        # Low confidence
        # -----------------------------

        if action == "CONFIRM_LOW_CONFIDENCE":

            value = action_plan.get(
                "unconfirmed_value"
            )

            return (
                f"Did you mean your "
                f"{field_label} is "
                f"'{value}'? "
                f"Please confirm or re-enter."
            )

        # -----------------------------
        # Complete
        # -----------------------------

        if action == "COMPLETE_FORM":

            return (
                "Thank you! "
                "All required form details "
                "have been collected and saved."
            )

        return "How can I help you complete your form?"