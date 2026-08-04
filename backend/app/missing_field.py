# Checks which required form fields are missing from user answers
try:
    from .schema_loader import SchemaLoader
except ImportError:
    from backend.app.schema_loader import SchemaLoader

class MissingFieldDetector:
    def get_missing_fields(self, form_name, state):
        # Load the form schema
        loader = SchemaLoader()
        schema = loader.load_schema(form_name)

        # If form does not exist or returned error, return error
        if isinstance(schema, dict) and "error" in schema:
            return schema

        missing_fields = []

        # Get all fields from schema safely
        fields = schema.get("fields", {}) if isinstance(schema, dict) else {}

        # If fields is a dictionary of field_name -> rules
        if isinstance(fields, dict):
            for field_name, rules in fields.items():
                if isinstance(rules, dict) and rules.get("required") is True:
                    value = state.get(field_name)
                    if value is None or value == "":
                        missing_fields.append(field_name)

        # Handle list-based fields structure: [{"id": "name", "required": True}]
        elif isinstance(fields, list):
            for field in fields:
                if isinstance(field, dict) and field.get("required") is True:
                    field_name = field.get("id") or field.get("name")
                    if field_name:
                        value = state.get(field_name)
                        if value is None or value == "":
                            missing_fields.append(field_name)

        return missing_fields