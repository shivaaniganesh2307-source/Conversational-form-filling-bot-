class ResponseGenerator:

    def generate(
        self,
        action_plan,
        schema
    ):

        action = action_plan.get(
            "action"
        )

        field_name = action_plan.get(
            "field"
        )

        fields = schema.get(
            "fields",
            {}
        )

        label = field_name or "this information"

        if (
            isinstance(fields, dict)
            and field_name in fields
        ):

            rules = fields[field_name]

            if isinstance(rules, dict):

                label = rules.get(
                    "label",
                    field_name.replace(
                        "_",
                        " "
                    )
                )

        if action == "CORRECT_VALIDATION_ERROR":

            messages = action_plan.get(
                "messages",
                []
            )

            return (
                f"There is an issue with your "
                f"{label}. "
                f"{' '.join(messages)}"
            )

        if action == "REQUEST_MISSING_FIELD":

            return (
                f"Please provide your "
                f"{label}."
            )

        if action == "CONFIRM_LOW_CONFIDENCE":

            value = action_plan.get(
                "unconfirmed_value"
            )

            return (
                f"Did you mean your "
                f"{label} is '{value}'?"
            )

        if action == "COMPLETE_FORM":

            return (
                "Thank you. Your form has been "
                "completed successfully."
            )

        return (
            "How can I help you complete "
            "your form?"
        )