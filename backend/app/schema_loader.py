import os
import json

class SchemaLoader:
    def __init__(self, schemas_dir=None):
        if schemas_dir is None:
            # Default directory pointing to your backend schemas folder
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.schemas_dir = os.path.join(base_dir, "schemas")
        else:
            self.schemas_dir = schemas_dir

    def get_available_forms(self) -> list:
        """Scan schemas folder and return available form names."""
        if not os.path.exists(self.schemas_dir):
            return ["user_registration"]
        
        forms = []
        for filename in os.listdir(self.schemas_dir):
            if filename.endswith(".json"):
                form_name = filename.replace(".json", "")
                forms.append(form_name)
        
        return forms if forms else ["user_registration"]

    def load_schema(self, form_id):
        print("Looking for:", form_id)
        print("Schema directory:", self.schemas_dir)

        possible_filenames = [
            f"{form_id}.json",
            f"{form_id}_form.json",
            f"{form_id.lower()}.json",
            f"{form_id.lower()}_form.json"
        ]
        print("Possible files:", possible_filenames)
        for filename in possible_filenames:
            filepath = os.path.join(self.schemas_dir, filename)
            print("Checking:", filepath)
            if os.path.exists(filepath):
                print("FOUND:", filepath)
                with open(filepath, "r") as f:
                    return json.load(f)
        print("NOT FOUND")
        return {}