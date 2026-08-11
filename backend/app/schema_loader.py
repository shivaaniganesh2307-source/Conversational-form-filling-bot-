import os
import json


class SchemaLoader:

    def __init__(self, schemas_dir=None):

        if schemas_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.schemas_dir = os.path.join(base_dir, "schemas")
        else:
            self.schemas_dir = schemas_dir

    def get_available_forms(self):

        if not os.path.exists(self.schemas_dir):
            return []

        forms = []

        for filename in os.listdir(self.schemas_dir):

            if filename.endswith(".json"):

                form_name = filename[:-5]
                forms.append(form_name)

        return sorted(forms)

    def load_schema(self, form_id):

        if not form_id:
            return {}

        possible_files = [
            f"{form_id}.json",
            f"{form_id.lower()}.json",
            f"{form_id}_form.json",
            f"{form_id.lower()}_form.json"
        ]

        for filename in possible_files:

            filepath = os.path.join(
                self.schemas_dir,
                filename
            )

            if os.path.isfile(filepath):

                try:

                    with open(
                        filepath,
                        "r",
                        encoding="utf-8"
                    ) as file:

                        schema = json.load(file)

                    if not isinstance(schema, dict):
                        return {}

                    return schema

                except (json.JSONDecodeError, OSError) as e:

                    print(
                        f"[SCHEMA ERROR] {filepath}: {e}"
                    )

                    return {}

        print(
            f"[SCHEMA NOT FOUND] {form_id}"
        )

        return {}