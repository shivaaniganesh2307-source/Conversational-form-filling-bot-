import re
from datetime import datetime
from typing import Any, Dict, List


class FieldValidationError(Exception):
    """Raised when a field fails validation."""

    def __init__(self, field_name: str, message: str):
        self.field_name = field_name
        self.message = message
        super().__init__(message)


# ============================================================
# BASIC VALIDATORS
# ============================================================

def check_not_empty(field_name: str, value: Any) -> None:

    if value is None:
        raise FieldValidationError(
            field_name,
            "This field cannot be empty."
        )

    if isinstance(value, str) and not value.strip():
        raise FieldValidationError(
            field_name,
            "This field cannot be empty."
        )


def check_string(field_name: str, value: Any) -> None:

    if not isinstance(value, str):
        raise FieldValidationError(
            field_name,
            "Please enter text."
        )


# ============================================================
# NAME VALIDATION
# ============================================================

def check_name(field_name: str, value: Any) -> None:

    if not isinstance(value, str):
        raise FieldValidationError(
            field_name,
            "Please enter a valid name."
        )

    value = value.strip()

    if not value:
        raise FieldValidationError(
            field_name,
            "Please enter a valid name."
        )

    # Names can contain letters, spaces, apostrophes and hyphens.
    if not re.fullmatch(
        r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ' -]*",
        value
    ):
        raise FieldValidationError(
            field_name,
            "Please enter a valid name using letters."
        )

    # Remove spaces, apostrophes and hyphens.
    letters_only = re.sub(
        r"[^A-Za-zÀ-ÖØ-öø-ÿ]",
        "",
        value
    )

    # Prevent extremely short garbage.
    if len(letters_only) < 2:
        raise FieldValidationError(
            field_name,
            "Please enter a valid name."
        )

    # Detect keyboard smash / repeated characters.
    if re.search(r"(.)\1{2,}", letters_only.lower()):
        raise FieldValidationError(
            field_name,
            "That doesn't look like a valid name. Please try again."
        )

    # Detect strings with no vowels.
    vowels = set(
        "aeiouy"
        "AEIOUY"
        "àáâäãå"
        "ÀÁÂÄÃÅ"
        "èéêë"
        "ÈÉÊË"
        "ìíîï"
        "ÌÍÎÏ"
        "òóôöõ"
        "ÒÓÔÖÕ"
        "ùúûü"
        "ÙÚÛÜ"
    )

    if len(letters_only) > 2:
        if not any(char in vowels for char in letters_only):
            raise FieldValidationError(
                field_name,
                "That doesn't look like a valid name. Please try again."
            )


# ============================================================
# EMAIL
# ============================================================

def check_email(field_name: str, value: Any) -> None:

    if not isinstance(value, str):
        raise FieldValidationError(
            field_name,
            "Please enter a valid email address."
        )

    value = value.strip()

    pattern = (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@"
        r"[A-Za-z0-9-]+"
        r"(?:\.[A-Za-z0-9-]+)+$"
    )

    if not re.fullmatch(pattern, value):
        raise FieldValidationError(
            field_name,
            "Please enter a valid email address."
        )


# ============================================================
# PHONE
# ============================================================

def check_phone(field_name: str, value: Any) -> None:

    if not isinstance(value, str):
        value = str(value)

    digits = re.sub(r"\D", "", value)

    if len(digits) < 7 or len(digits) > 15:
        raise FieldValidationError(
            field_name,
            "Please enter a valid phone number."
        )


# ============================================================
# BOOLEAN
# ============================================================

def check_boolean(field_name: str, value: Any) -> None:

    if isinstance(value, bool):
        return

    if isinstance(value, str):

        normalized = value.strip().lower()

        if normalized in {
            "true",
            "false",
            "yes",
            "no"
        }:
            return

    raise FieldValidationError(
        field_name,
        "Please answer yes or no."
    )


# ============================================================
# NUMBER
# ============================================================

def check_number(field_name: str, value: Any) -> None:

    try:
        float(value)
    except (ValueError, TypeError):

        raise FieldValidationError(
            field_name,
            "Please enter a valid number."
        )


# ============================================================
# INTEGER
# ============================================================

def check_integer(field_name: str, value: Any) -> None:

    try:

        number = float(value)

        if not number.is_integer():
            raise ValueError

    except (ValueError, TypeError):

        raise FieldValidationError(
            field_name,
            "Please enter a whole number."
        )


# ============================================================
# DATE
# ============================================================

def check_date(
    field_name: str,
    value: Any,
    date_format: str = "%Y-%m-%d"
) -> None:

    if not isinstance(value, str):

        raise FieldValidationError(
            field_name,
            "Please enter a valid date."
        )

    try:
        datetime.strptime(value.strip(), date_format)

    except ValueError:

        raise FieldValidationError(
            field_name,
            f"Please enter the date in {date_format} format."
        )


# ============================================================
# CHOICE
# ============================================================

def check_choice(
    field_name: str,
    value: Any,
    choices: List[Any]
) -> None:

    if value not in choices:

        raise FieldValidationError(
            field_name,
            f"Please choose one of: {', '.join(map(str, choices))}."
        )


# ============================================================
# REGEX / PATTERN
# ============================================================

def check_pattern(
    field_name: str,
    value: Any,
    pattern: str
) -> None:

    if not isinstance(value, str):

        raise FieldValidationError(
            field_name,
            "Please enter a valid value."
        )

    try:

        if not re.fullmatch(pattern, value):

            raise FieldValidationError(
                field_name,
                "The value does not match the required format."
            )

    except re.error:

        raise FieldValidationError(
            field_name,
            "The form contains an invalid validation pattern."
        )


# ============================================================
# MAIN VALIDATOR
# ============================================================

class FormValidator:

    @staticmethod
    def validate_field(
        field_name: str,
        value: Any,
        rules: Dict[str, Any]
    ) -> List[str]:

        errors = []

        if not isinstance(rules, dict):

            return [
                f"Invalid validation rules for {field_name}."
            ]

        # ----------------------------------------------------
        # Required
        # ----------------------------------------------------

        required = rules.get(
            "required",
            False
        )

        if required:

            try:

                check_not_empty(
                    field_name,
                    value
                )

            except FieldValidationError as error:

                errors.append(error.message)

                return errors

        # Optional empty fields don't need further validation.
        if value is None or value == "":
            return errors

        # ----------------------------------------------------
        # Type
        # ----------------------------------------------------

        field_type = rules.get(
            "type",
            "string"
        )

        try:

            if field_type in {
                "string",
                "text"
            }:

                check_string(
                    field_name,
                    value
                )

            elif field_type == "name":

                check_name(
                    field_name,
                    value
                )

            elif field_type == "email":

                check_email(
                    field_name,
                    value
                )

            elif field_type == "phone":

                check_phone(
                    field_name,
                    value
                )

            elif field_type == "boolean":

                check_boolean(
                    field_name,
                    value
                )

            elif field_type == "number":

                check_number(
                    field_name,
                    value
                )

            elif field_type == "integer":

                check_integer(
                    field_name,
                    value
                )

            elif field_type == "date":

                check_date(
                    field_name,
                    value,
                    rules.get(
                        "format",
                        "%Y-%m-%d"
                    )
                )

            elif field_type == "choice":

                check_choice(
                    field_name,
                    value,
                    rules.get(
                        "choices",
                        []
                    )
                )

            elif field_type == "pattern":

                check_pattern(
                    field_name,
                    value,
                    rules.get(
                        "pattern",
                        ""
                    )
                )

            else:

                errors.append(
                    f"Unsupported field type '{field_type}'."
                )

        except FieldValidationError as error:

            errors.append(
                error.message
            )

        # ----------------------------------------------------
        # Minimum length
        # ----------------------------------------------------

        if "min_length" in rules:

            try:

                minimum = int(
                    rules["min_length"]
                )

                if len(str(value).strip()) < minimum:

                    errors.append(
                        f"{field_name} must be at least "
                        f"{minimum} characters long."
                    )

            except (ValueError, TypeError):

                errors.append(
                    f"Invalid min_length rule for {field_name}."
                )

        # ----------------------------------------------------
        # Maximum length
        # ----------------------------------------------------

        if "max_length" in rules:

            try:

                maximum = int(
                    rules["max_length"]
                )

                if len(str(value).strip()) > maximum:

                    errors.append(
                        f"{field_name} must be at most "
                        f"{maximum} characters long."
                    )

            except (ValueError, TypeError):

                errors.append(
                    f"Invalid max_length rule for {field_name}."
                )

        # ----------------------------------------------------
        # Minimum number
        # ----------------------------------------------------

        if "min" in rules:

            try:

                if float(value) < float(rules["min"]):

                    errors.append(
                        f"{field_name} must be at least "
                        f"{rules['min']}."
                    )

            except (ValueError, TypeError):

                pass

        # ----------------------------------------------------
        # Maximum number
        # ----------------------------------------------------

        if "max" in rules:

            try:

                if float(value) > float(rules["max"]):

                    errors.append(
                        f"{field_name} must be at most "
                        f"{rules['max']}."
                    )

            except (ValueError, TypeError):

                pass

        # ----------------------------------------------------
        # Choices
        # ----------------------------------------------------

        if "choices" in rules and rules.get("type") != "choice":

            choices = rules.get(
                "choices"
            )

            if isinstance(choices, list):

                if value not in choices:

                    errors.append(
                        f"Please choose one of: "
                        f"{', '.join(map(str, choices))}."
                    )

        # ----------------------------------------------------
        # Custom regex
        # ----------------------------------------------------

        if "pattern" in rules:

            try:

                if not re.fullmatch(
                    rules["pattern"],
                    str(value)
                ):

                    errors.append(
                        "The value does not match the required format."
                    )

            except re.error:

                errors.append(
                    "The form contains an invalid validation pattern."
                )

        return errors