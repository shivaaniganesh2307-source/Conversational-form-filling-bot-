import re
from typing import Any, Dict, List


class FieldValidationError(Exception):
    """Exception thrown when a field fails validation."""

    def __init__(self, field_name: str, message: str):
        self.field_name = field_name
        self.message = message
        super().__init__(f"Validation Error [{field_name}]: {message}")


def check_not_empty(field_name: str, value: Any) -> None:
    """Check that a required field is not empty."""

    if value is None or (isinstance(value, str) and not value.strip()):
        raise FieldValidationError(
            field_name,
            f"{field_name} cannot be empty."
        )


def check_name(field_name: str, value: Any) -> None:
    """
    Validate first and last names.

    Allows normal names such as:
    Shivaani
    John
    Mary Jane
    O'Connor
    Smith-Jones
    """

    value = str(value).strip()

    # Names should contain only letters, spaces, apostrophes or hyphens
    if not re.fullmatch(r"[A-Za-z][A-Za-z' -]*", value):
        raise FieldValidationError(
            field_name,
            "That doesn't look like a valid name. Please enter your actual name."
        )

    # Remove spaces for length check
    letters_only = re.sub(r"[^A-Za-z]", "", value)

    if len(letters_only) < 2:
        raise FieldValidationError(
            field_name,
            "That name is too short. Please enter your actual name."
        )


def check_email_format(field_name: str, value: str) -> None:
    """Validate email format."""

    regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    if not re.fullmatch(regex, value):
        raise FieldValidationError(
            field_name,
            f"'{value}' is not a valid email address."
        )


def check_minimum_length(
    field_name: str,
    value: str,
    min_len: int
) -> None:

    if len(str(value)) < min_len:
        raise FieldValidationError(
            field_name,
            f"{field_name} must be at least {min_len} characters long."
        )


def check_boolean(field_name: str, value: Any) -> None:
    """Validate boolean fields."""

    if isinstance(value, bool):
        return

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in [
            "yes",
            "no",
            "true",
            "false"
        ]:
            return

    raise FieldValidationError(
        field_name,
        "Please answer yes or no."
    )


def check_number(field_name: str, value: Any) -> None:
    """Validate number fields."""

    try:
        float(value)
    except (ValueError, TypeError):
        raise FieldValidationError(
            field_name,
            f"Please enter a valid number for {field_name}."
        )


class FormValidator:

    @staticmethod
    def validate_field(
        field_name: str,
        value: Any,
        rules: Dict[str, Any]
    ) -> List[str]:

        errors = []

        # --------------------------------
        # 1. Required / empty check
        # --------------------------------

        if rules.get("required", False):

            try:
                check_not_empty(field_name, value)

            except FieldValidationError as err:
                errors.append(err.message)
                return errors

        # Nothing else to validate if empty optional field
        if value is None or value == "":
            return errors

        # --------------------------------
        # 2. String validation
        # --------------------------------

        field_type = rules.get("type")

        if field_name in ["first_name", "last_name"]:

            try:
                check_name(field_name, value)

            except FieldValidationError as err:
                errors.append(err.message)

        # --------------------------------
        # 3. Email validation
        # --------------------------------

        if field_type == "email" or field_name == "email":

            try:
                check_email_format(
                    field_name,
                    str(value)
                )

            except FieldValidationError as err:
                errors.append(err.message)

        # --------------------------------
        # 4. Boolean validation
        # --------------------------------

        if field_type == "boolean":

            try:
                check_boolean(
                    field_name,
                    value
                )

            except FieldValidationError as err:
                errors.append(err.message)

        # --------------------------------
        # 5. Number validation
        # --------------------------------

        if field_type == "number":

            try:
                check_number(
                    field_name,
                    value
                )

            except FieldValidationError as err:
                errors.append(err.message)

        # --------------------------------
        # 6. Minimum length
        # --------------------------------

        if "min_length" in rules:

            try:
                check_minimum_length(
                    field_name,
                    str(value),
                    rules["min_length"]
                )

            except FieldValidationError as err:
                errors.append(err.message)

        return errors