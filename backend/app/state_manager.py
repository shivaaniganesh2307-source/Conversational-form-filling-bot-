
class StateManager:

    def create_empty_space(self, form_name, schema):
        """
        Create an empty state dynamically from the loaded form schema.

        No fields are hardcoded here.
        Whatever fields exist in the JSON schema become
        fields in the conversation state.
        """

        state = {}

        fields = schema.get("fields", {})

        # Dictionary-based schema
        if isinstance(fields, dict):

            for field_name in fields:
                state[field_name] = None

        # List-based schema
        elif isinstance(fields, list):

            for field in fields:

                if not isinstance(field, dict):
                    continue

                field_name = (
                    field.get("id")
                    or field.get("name")
                )

                if field_name:
                    state[field_name] = None

        return state

    def update_state(self, current_state, extracted_data):
        """
        Update the current conversation state with
        newly extracted values.

        Only extracted values are changed.
        Existing values remain untouched.
        """

        if not isinstance(current_state, dict):
            current_state = {}

        if not isinstance(extracted_data, dict):
            return current_state

        for field_name, value in extracted_data.items():

            # Do not overwrite a value with None
            if value is not None:
                current_state[field_name] = value

        return current_state

