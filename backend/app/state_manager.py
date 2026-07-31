try:
    from .schema_loader import SchemaLoader
except ImportError:
    from backend.app.schema_loader import SchemaLoader


class StateManager:
    def create_empty_space(self, form_name):
        loader = SchemaLoader()
        schema = loader.load_schema(form_name)

        if isinstance(schema, dict) and "error" in schema:
            return schema

        state = {}
        fields = schema.get("fields", {}) if isinstance(schema, dict) else {}

        # Handles dictionary-based schema format
        if isinstance(fields, dict):
            for field_id in fields:
                state[field_id] = ""
        # Handles list-based schema format
        elif isinstance(fields, list):
            for field in fields:
                field_id = field.get("id") or field.get("name")
                if field_id:
                    state[field_id] = ""

        return state

    def update_state(self, current_state, extracted_data):
        if not isinstance(current_state, dict):
            current_state = {}
        if isinstance(extracted_data, dict):
            current_state.update(extracted_data)
        return current_state