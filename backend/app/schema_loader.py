import os
import json

class SchemaLoader:
    def __init__(self, schemas_dir=None):
        if schemas_dir is None:
            # Default directory pointing to your backend schemas folder
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

    def load_schema(self, form_name: str) -> dict:
        """Load specific schema json file."""
        file_path = os.path.join(self.schemas_dir, f"{form_name}.json")
        if not os.path.exists(file_path):
            return {}
        
        with open(file_path, "r") as f:
            return json.load(f)