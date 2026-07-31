import os
import pytest
from app.schema_loader import SchemaLoader

def test_dynamic_schema_discovery(tmp_path):
    """Verifies SchemaLoader detects ANY dynamically added JSON schema file."""
    # 1. Create a temporary schemas directory
    custom_schema_dir = tmp_path / "schemas"
    custom_schema_dir.mkdir()

    # 2. Add two completely arbitrary custom forms
    (custom_schema_dir / "CUSTOM_A_FORM.json").write_text('{"fields": {}}')
    (custom_schema_dir / "XYZ_REGISTRATION.json").write_text('{"fields": {}}')

    # 3. Instantiate loader pointed at the temp directory
    loader = SchemaLoader(schemas_dir=str(custom_schema_dir))
    forms = loader.get_available_forms()

    # 4. Assert that ANY discovered form names are returned dynamically
    assert "CUSTOM_A" in forms or "CUSTOM_A_FORM" in forms
    assert "XYZ_REGISTRATION" in forms