class MissingFieldDetector:
    """
    Figures out which required fields still need to be collected.

    Supports conditional fields (fields that are only required if
    another field has a certain value) with a few operators, so new
    forms can use whichever shape fits without touching this code:

        "condition": {"field": "has_allergies", "equals": true}
        "condition": {"field": "status", "not_equals": "inactive"}
        "condition": {"field": "facility_street", "exists": true}
        "condition": {"field": "country", "in": ["US", "CA"]}
    """

    def _condition_met(self, condition, state):

        if not isinstance(condition, dict):
            return True

        field = condition.get("field")
        value = state.get(field)

        if "equals" in condition:
            return value == condition.get("equals")

        if "not_equals" in condition:
            # An unset referenced field doesn't yet "not equal" anything
            # meaningfully -- treat it as undetermined rather than
            # trivially true, so a dependent field isn't required
            # before we actually know the referenced value.
            if value is None:
                return False
            return value != condition.get("not_equals")

        if "exists" in condition:
            has_value = value not in (None, "")
            return has_value == bool(condition.get("exists"))

        if "in" in condition:
            options = condition.get("in") or []
            return value in options

        return True

    def get_missing_fields(self, schema=None, state=None, form_name=None):

        # Prefer an already-loaded schema (avoids re-reading the
        # file from disk on every call). form_name is kept as a
        # fallback for backward compatibility.
        if schema is None and form_name:
            from .schema_loader import SchemaLoader
            schema = SchemaLoader().load_schema(form_name)

        if not isinstance(schema, dict):
            return []

        fields = schema.get("fields", {})

        if not isinstance(fields, dict):
            return []

        if not isinstance(state, dict):
            state = {}

        missing_fields = []

        for field_name, rules in fields.items():

            if not isinstance(rules, dict):
                continue

            condition = rules.get("condition")
            if condition and not self._condition_met(condition, state):
                # Condition not satisfied -- this field isn't
                # applicable right now, so don't ask for it.
                continue

            if not rules.get("required", False):
                continue

            value = state.get(field_name)

            if value is None:
                missing_fields.append(field_name)
                continue

            if isinstance(value, str) and not value.strip():
                missing_fields.append(field_name)

        return missing_fields
