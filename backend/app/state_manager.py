class StateManager:

    def create_empty_state(self, schema):
        """
        Create an empty state dynamically from the loaded form schema.

        No fields are hardcoded here. Whatever fields exist in the
        JSON schema become fields in the conversation state, so a
        brand new form works with zero code changes.
        """

        state = {}

        fields = schema.get("fields", {})

        if isinstance(fields, dict):
            for field_name in fields:
                state[field_name] = None

        elif isinstance(fields, list):
            for field in fields:
                if not isinstance(field, dict):
                    continue
                field_name = field.get("id") or field.get("name")
                if field_name:
                    state[field_name] = None

        return state

    # Backward-compatible alias for old call sites.
    def create_empty_space(self, *args):
        schema = args[-1] if args else {}
        return self.create_empty_state(schema)

    def update_state(self, current_state, extracted_data):
        """
        Update the current conversation state with newly extracted
        values. Only extracted values are changed; existing values
        remain untouched.
        """

        if not isinstance(current_state, dict):
            current_state = {}

        if not isinstance(extracted_data, dict):
            return current_state

        for field_name, value in extracted_data.items():
            if value is not None:
                current_state[field_name] = value

        return current_state
