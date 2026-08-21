import os
import json


class SchemaLoader:
    """
    Loads form schemas from backend/app/schemas/.

    IMPORTANT -- this is what makes forms "dynamic":

    Any .json file dropped into the schemas folder that contains a
    non-empty "fields" object is automatically treated as a form.
    Nothing else needs to change in code. Files that don't look like
    a form (e.g. UNIVERSITIES.json, a reference/lookup list) are
    simply skipped instead of showing up as a broken form option.

    Matching is done by reading each file's declared "form_id" (or
    falling back to the filename) rather than guessing filenames from
    the requested id, so it no longer matters whether a file is named
    "employee_form.json" or "EMPLOYEE_FORM.json".
    """

    def __init__(self, schemas_dir=None):
        if schemas_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.schemas_dir = os.path.join(base_dir, "schemas")
        else:
            self.schemas_dir = schemas_dir

    # --------------------------------------------------------------
    # INTERNAL: scan every .json file and keep only valid forms
    # --------------------------------------------------------------

    def _scan_schemas(self):
        index = {}

        if not os.path.isdir(self.schemas_dir):
            print(f"[WARNING] Schemas directory not found: {self.schemas_dir}")
            return index

        for filename in os.listdir(self.schemas_dir):

            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(self.schemas_dir, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    schema = json.load(file)
            except (json.JSONDecodeError, OSError) as error:
                print(f"[SCHEMA ERROR] Could not load {filename}: {error}")
                continue

            if not isinstance(schema, dict):
                continue

            fields = schema.get("fields")

            # Not a form schema (e.g. reference/lookup data like
            # UNIVERSITIES.json). Skip it silently.
            if not isinstance(fields, dict) or not fields:
                continue

            form_id = schema.get("form_id") or os.path.splitext(filename)[0]
            form_name = schema.get("form_name", form_id)

            schema["form_id"] = form_id
            schema["form_name"] = form_name

            index[form_id] = schema
            index[form_id.lower()] = schema

        return index

    # --------------------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------------------

    def get_available_forms(self):
        """Returns [{"id": "...", "name": "..."}, ...] for every real form."""

        index = self._scan_schemas()

        unique = {}
        for schema in index.values():
            unique[schema["form_id"]] = schema["form_name"]

        return [
            {"id": form_id, "name": form_name}
            for form_id, form_name in sorted(unique.items())
        ]

    def load_schema(self, form_id):

        if not form_id:
            return {}

        index = self._scan_schemas()

        schema = index.get(form_id) or index.get(str(form_id).lower())

        if schema:
            print(f"[SCHEMA LOADED] {schema['form_id']}")
            return schema

        print(f"[SCHEMA NOT FOUND] {form_id}")
        return {}
