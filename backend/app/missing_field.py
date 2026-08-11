from .schema_loader import SchemaLoader


class MissingFieldDetector:

    def get_missing_fields(
        self,
        form_name,
        state
    ):

        loader = SchemaLoader()

        schema = loader.load_schema(
            form_name
        )

        if not isinstance(
            schema,
            dict
        ):

            return []

        fields = schema.get(
            "fields",
            {}
        )

        if not isinstance(
            fields,
            dict
        ):

            return []

        if not isinstance(
            state,
            dict
        ):

            state = {}

        missing_fields = []

        for field_name, rules in fields.items():

            if not isinstance(
                rules,
                dict
            ):

                continue

            # ------------------------------------------------
            # CONDITIONAL FIELD
            # ------------------------------------------------

            condition = rules.get(
                "condition"
            )

            if isinstance(
                condition,
                dict
            ):

                condition_field = (
                    condition.get("field")
                )

                expected_value = (
                    condition.get("equals")
                )

                actual_value = state.get(
                    condition_field
                )

                # Condition is not satisfied.
                if actual_value != expected_value:

                    continue

            # ------------------------------------------------
            # REQUIRED
            # ------------------------------------------------

            if rules.get(
                "required",
                False
            ):

                value = state.get(
                    field_name
                )

                if value is None or value == "":

                    missing_fields.append(
                        field_name
                    )

        return missing_fields