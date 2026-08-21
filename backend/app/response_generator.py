class ResponseGenerator:

    def generate(self, action_plan, schema):

        action = action_plan.get("action")
        field_name = action_plan.get("field")
        fields = schema.get("fields", {})

        label = field_name or "this information"
        rules = {}

        if isinstance(fields, dict) and field_name in fields:
            rules = fields.get(field_name, {})
            if isinstance(rules, dict):
                label = rules.get("label", field_name.replace("_", " "))

        if action == "CORRECT_VALIDATION_ERROR":

            messages = action_plan.get("messages", [])
            if not isinstance(messages, list):
                messages = [str(messages)]
            message = " ".join(str(message) for message in messages)

            custom_message = rules.get("error_message") if isinstance(rules, dict) else None
            if custom_message:
                return str(custom_message)

            return f"There is an issue with your {label}. {message}"

        if action == "REQUEST_MISSING_FIELD":

            custom_prompt = rules.get("prompt") if isinstance(rules, dict) else None
            if custom_prompt:
                return str(custom_prompt)

            return f"Please provide your {label}."

        if action == "CONFIRM_LOW_CONFIDENCE":

            value = action_plan.get("unconfirmed_value")
            return f"Did you mean your {label} is '{value}'?"

        if action == "CONFIRM_SECTION_ADVANCE":

            current_section = action_plan.get("current_section", "this part")
            next_section = action_plan.get("next_section", "the next part")
            return (
                f"That completes {current_section}. "
                f"Ready to move on to {next_section}? (yes/no)"
            )

        if action == "SECTION_ADVANCE_DECLINED":

            return (
                "No problem -- let me know if you'd like to change "
                "anything, or say \"continue\" when you're ready to move on."
            )

        if action == "COMPLETE_FORM":
            return "Thank you. Your form has been completed successfully."

        return "How can I help you complete your form?"
