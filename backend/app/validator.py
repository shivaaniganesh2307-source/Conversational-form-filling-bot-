import re
from typing import Any, Dict, List

class FieldValidationError(Exception):
    #exception thrown when a field fails validation
    def __init__(self, field_name: str, message: str):
        self.field_name = field_name
        self.message = message
        super().__init__(f"Validation Error [{field_name}]: {message}")
#helper functions
def check_not_empty(field_name: str, value: Any) -> None:
    """Helper to verify a required field is not empty, None, or whitespace."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise FieldValidationError(field_name, f"{field_name} cannot be empty.")
def check_email_format(field_name: str, value: str) -> None:
    #Helper to validate email format using regex.
    regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(regex, value):
        raise FieldValidationError(field_name, f"'{value}' is not a valid email address.")

def check_minimum_length(field_name: str, value: str, min_len: int) -> None:
    #to make sure password is long eenough
    if len(str(value)) < min_len:
        raise FieldValidationError(field_name, f"{field_name} must be at least {min_len} characters long.")

class FormValidator:
    @staticmethod
    def validate_field(field_name: str, value: Any, rules: Dict[str, Any]) -> List[str]:
        errors = []
        # 1. Empty Check
        if rules.get("required", False):
            try:
                check_not_empty(field_name, value)
            except FieldValidationError as err:
                errors.append(err.message)
                return errors

        if value is None or value == "":
            return errors

        # 2. Email Format Check
        if rules.get("type") == "email" or field_name == "email":
            try:
                check_email_format(field_name, str(value))
            except FieldValidationError as err:
                errors.append(err.message)

        # 3. Min Length Check  
        if "min_length" in rules:
            try:
                check_minimum_length(field_name, str(value), rules["min_length"])
            except FieldValidationError as err:
                errors.append(err.message)

        return errors