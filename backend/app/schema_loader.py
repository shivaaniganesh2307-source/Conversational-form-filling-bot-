import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

class SchemaLoader:
    def __init__(self, schemas_dir=SCHEMAS_DIR):
        self.schemas_dir = schemas_dir
        if not os.path.exists(self.schemas_dir):
            os.makedirs(self.schemas_dir, exist_ok=True)

    def get_available_forms(self):
        """Scans the schemas directory dynamically for any .json form schema."""
        if not os.path.exists(self.schemas_dir):
            return []
        
        forms = []
        for filename in os.listdir(self.schemas_dir):
            if filename.endswith(".json"):
                # Clean filename to standard form name
                form_id = filename.rsplit(".", 1)[0].replace("_form", "")
                forms.append(form_id)
        return forms

    def load_schema(self, form_id):
        """Loads schema JSON by searching for form_id variations."""
        if not os.path.exists(self.schemas_dir):
            return {"error": f"Form schema for '{form_id}' does not exist"}

        possible_filenames = [
            f"{form_id}.json",
            f"{form_id}_form.json",
            f"{form_id.lower()}.json",
            f"{form_id.lower()}_form.json"
        ]

        for filename in possible_filenames:
            filepath = os.path.join(self.schemas_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r") as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    return {"error": f"Invalid JSON structure in '{filename}'"}

        return {"error": f"Form schema for '{form_id}' does not exist"}

    def add_form(self, form_id, schema_data):
        """Saves a new schema dynamically to disk as a JSON file."""
        if not os.path.exists(self.schemas_dir):
            os.makedirs(self.schemas_dir, exist_ok=True)

        filepath = os.path.join(self.schemas_dir, f"{form_id}.json")
        with open(filepath, "w") as f:
            json.dump(schema_data, f, indent=2)
        return True