import pytest

from app.validator import (
    FormValidator,
    FieldValidationError,
    check_not_empty,
    check_email_format,
    check_minimum_length
)


def test_check_not_empty_raises_error():

    print("\nRunning test_check_not_empty_raises_error...")

    with pytest.raises(FieldValidationError) as exc:
        check_not_empty("first_name", "   ")

    print("Error Raised:")
    print(exc.value)

    assert "first_name cannot be empty" in str(exc.value)

    print("✅ test_check_not_empty_raises_error passed")


def test_check_email_format_valid():

    print("\nRunning test_check_email_format_valid...")

    check_email_format(
        "email",
        "user@example.com"
    )

    print("Valid email accepted")

    print("✅ test_check_email_format_valid passed")


def test_check_email_format_invalid():

    print("\nRunning test_check_email_format_invalid...")

    with pytest.raises(FieldValidationError) as exc:
        check_email_format(
            "email",
            "bad_email_format"
        )

    print("Error Raised:")
    print(exc.value)

    assert "is not a valid email address" in str(exc.value)

    print("test_check_email_format_invalid passed")


def test_check_minimum_length_invalid():

    print("\nRunning test_check_minimum_length_invalid...")

    with pytest.raises(FieldValidationError) as exc:
        check_minimum_length(
            "phone",
            "123",
            10
        )

    print("Error Raised:")
    print(exc.value)

    assert "must be at least 10 characters long" in str(exc.value)

    print("test_check_minimum_length_invalid passed")


def test_form_validator_engine():

    print("\nRunning test_form_validator_engine...")

    rules = {
        "required": True,
        "type": "string"
    }

    errors = FormValidator.validate_field(
        "first_name",
        "",
        rules
    )

    print("Validation Errors:")
    print(errors)

    assert len(errors) == 1
    assert "first_name cannot be empty" in errors[0]

    print("test_form_validator_engine passed")


if __name__ == "__main__":

    test_check_not_empty_raises_error()
    test_check_email_format_valid()
    test_check_email_format_invalid()
    test_check_minimum_length_invalid()
    test_form_validator_engine()

    print("\nAll Validator Tests Passed!")