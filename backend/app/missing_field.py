try:
    from .schema_loader import SchemaLoader
except ImportError:
    from backend.app.schema_loader import SchemaLoader


class MissingFieldDetector:

    def get_missing_fields(self, form_name, state):

        loader = SchemaLoader()
        schema = loader.load_schema(form_name)

        if isinstance(schema, dict) and "error" in schema:
            return schema

        missing_fields = []

        fields = schema.get("fields", {}) if isinstance(schema, dict) else {}

        if not isinstance(fields, dict):
            return missing_fields

        for field_name, rules in fields.items():

            if not isinstance(rules, dict):
                continue

            # --------------------------------
            # Check conditional field
            # --------------------------------

            condition = rules.get("condition")

            if condition:

                condition_field = condition.get("field")
                expected_value = condition.get("equals")

                actual_value = state.get(condition_field)

                # If the condition is not satisfied,
                # this field is not required right now.
                if actual_value != expected_value:
                    continue

            # --------------------------------
            # Check required field
            # --------------------------------

            if rules.get("required") is True:

                value = state.get(field_name)

                if value is None or value == "":
                    missing_fields.append(field_name)

        return missing_fields