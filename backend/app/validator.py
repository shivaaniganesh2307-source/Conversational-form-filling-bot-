import re
from datetime import datetime
from typing import Any, Dict, List

class FieldValidationError(Exception):
    """Raised when a field fails validation."""

    def __init__(self, field_name: str, message: str):
        self.field_name = field_name
        self.message = message
        super().__init__(message)

def check_not_empty(field_name: str, value: Any) -> None:
    if value is None:
        raise FieldValidationError(field_name, "This field cannot be empty.")
    if isinstance(value, str) and not value.strip():
        raise FieldValidationError(field_name, "This field cannot be empty.")

def check_string(field_name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise FieldValidationError(field_name, "Please enter text.")

def check_name(field_name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise FieldValidationError(field_name, "Please enter a valid name.")
    value = value.strip()
    if not value:
        raise FieldValidationError(field_name, "Please enter a valid name.")

    if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ' -]*", value):
        raise FieldValidationError(field_name, "Please enter a valid name using letters.")

    letters_only = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ]", "", value)

    if len(letters_only) < 2:
        raise FieldValidationError(field_name, "Please enter a valid name.")

    if re.search(r"(.)\1{2,}", letters_only.lower()):
        raise FieldValidationError(field_name, "That doesn't look like a valid name. Please try again.")
    vowels = set(
        "aeiouyAEIOUYàáâäãåÀÁÂÄÃÅèéêëÈÉÊËìíîïÌÍÎÏòóôöõÒÓÔÖÕùúûüÙÚÛÜ"
    )
    if len(letters_only) > 2:
        if not any(char in vowels for char in letters_only):
            raise FieldValidationError(field_name, "That doesn't look like a valid name. Please try again.")

def check_email(field_name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise FieldValidationError(field_name, "Please enter a valid email address.")
    value = value.strip()
    pattern = (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@"
        r"[A-Za-z0-9-]+"
        r"(?:\.[A-Za-z0-9-]+)+$"
    )
    if not re.fullmatch(pattern, value):
        raise FieldValidationError(field_name, "Please enter a valid email address.")

def check_phone(field_name: str, value: Any) -> None:
    if not isinstance(value, str):
        value = str(value)
    digits = re.sub(r"\D", "", value)
    if len(digits) < 7 or len(digits) > 15:
        raise FieldValidationError(field_name, "Please enter a valid phone number.")

def check_boolean(field_name: str, value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "false", "yes", "no"}:
            return
    raise FieldValidationError(field_name, "Please answer yes or no.")

def check_number(field_name: str, value: Any) -> None:
    try:
        float(value)
    except (ValueError, TypeError):
        raise FieldValidationError(field_name, "Please enter a valid number.")

def check_integer(field_name: str, value: Any) -> None:
    try:
        number = float(value)
        if not number.is_integer():
            raise ValueError
    except (ValueError, TypeError):
        raise FieldValidationError(field_name, "Please enter a whole number.")

def check_date(field_name: str, value: Any, date_format: str = "%Y-%m-%d") -> None:
    if not isinstance(value, str):
        raise FieldValidationError(field_name, "Please enter a valid date.")
    try:
        datetime.strptime(value.strip(), date_format)
    except ValueError:
        raise FieldValidationError(field_name, f"Please enter the date in {date_format} format.")

def check_choice(field_name: str, value: Any, choices: List[Any]) -> None:
    if value not in choices:
        raise FieldValidationError(field_name, f"Please choose one of: {', '.join(map(str, choices))}.")

def check_pattern(field_name: str, value: Any, pattern: str) -> None:
    if not isinstance(value, str):
        raise FieldValidationError(field_name, "Please enter a valid value.")
    try:
        if not re.fullmatch(pattern, value):
            raise FieldValidationError(field_name, "The value does not match the required format.")
    except re.error:
        raise FieldValidationError(field_name, "The form contains an invalid validation pattern.")

def check_min_length(field_name: str, value: Any, minimum: Any) -> None:
    try:
        minimum = int(minimum)
    except (ValueError, TypeError):
        raise FieldValidationError(field_name, "Invalid minimum length rule.")
    if len(str(value).strip()) < minimum:
        raise FieldValidationError(field_name, f"{field_name} must be at least {minimum} characters long.")

def check_max_length(field_name: str, value: Any, maximum: Any) -> None:
    try:
        maximum = int(maximum)
    except (ValueError, TypeError):
        raise FieldValidationError(field_name, "Invalid maximum length rule.")
    if len(str(value).strip()) > maximum:
        raise FieldValidationError(field_name, f"{field_name} must be at most {maximum} characters long.")

def check_min(field_name: str, value: Any, minimum: Any) -> None:
    try:
        if float(value) < float(minimum):
            raise FieldValidationError(field_name, f"{field_name} must be at least {minimum}.")
    except (ValueError, TypeError):
        pass

def check_max(field_name: str, value: Any, maximum: Any) -> None:
    try:
        if float(value) > float(maximum):
            raise FieldValidationError(field_name, f"{field_name} must be at most {maximum}.")
    except (ValueError, TypeError):
        pass

class FormValidator:
    @staticmethod
    def validate_field(field_name: str, value: Any, rules: Dict[str, Any]) -> List[str]:
        errors = []
        if not isinstance(rules, dict):
            return [f"Invalid validation rules for {field_name}."]

        required = rules.get("required", False)
        if required:
            try:
                check_not_empty(field_name, value)
            except FieldValidationError as error:
                errors.append(error.message)
                return errors

        if value is None or value == "":
            return errors

        field_type = rules.get("type", "string")
        try:
            if field_type in {"string", "text"}:
                check_string(field_name, value)
            elif field_type == "name":
                check_name(field_name, value)
            elif field_type == "email":
                check_email(field_name, value)
            elif field_type == "phone":
                check_phone(field_name, value)
            elif field_type == "boolean":
                check_boolean(field_name, value)
            elif field_type == "number":
                check_number(field_name, value)
            elif field_type == "integer":
                check_integer(field_name, value)
            elif field_type == "date":
                check_date(field_name, value, rules.get("format", "%Y-%m-%d"))
            elif field_type == "choice":
                check_choice(field_name, value, rules.get("choices", []))
            elif field_type == "pattern":
                check_pattern(field_name, value, rules.get("pattern", ""))
            else:
                errors.append(f"Unsupported field type '{field_type}'.")
        except FieldValidationError as error:
            errors.append(error.message)

        if "min_length" in rules:
            try:
                check_min_length(field_name, value, rules["min_length"])
            except FieldValidationError as error:
                errors.append(error.message)

        if "max_length" in rules:
            try:
                check_max_length(field_name, value, rules["max_length"])
            except FieldValidationError as error:
                errors.append(error.message)

        if "min" in rules:
            try:
                check_min(field_name, value, rules["min"])
            except FieldValidationError as error:
                errors.append(error.message)

        if "max" in rules:
            try:
                check_max(field_name, value, rules["max"])
            except FieldValidationError as error:
                errors.append(error.message)

        if "choices" in rules:
            choices = rules.get("choices")
            if isinstance(choices, list):
                if value not in choices:
                    errors.append(f"Please choose one of: {', '.join(map(str, choices))}.")

        if "pattern" in rules:
            pattern = rules.get("pattern")
            if isinstance(pattern, str) and pattern:
                try:
                    if not re.fullmatch(pattern, str(value)):
                        errors.append("The value does not match the required format.")
                except re.error:
                    errors.append("The form contains an invalid validation pattern.")
        return errors
