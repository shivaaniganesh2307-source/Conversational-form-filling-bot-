from app.missing_field import MissingFieldDetector


def test_missing_required_fields():

    print("\nStarting Missing Field Test...")

    detector = MissingFieldDetector()

    state = {
        "first_name": "John",
        "last_name": "",
        "email": None
    }

    print("Current State:")
    print(state)

    missing = detector.get_missing_fields(
        "user_registration",  # filename without _form.json
        state
    )

    print("\nMissing Fields Found:")
    print(missing)

    # Ensure we didn't get a schema error
    assert "error" not in missing

    # Verify expected missing fields
    assert "last_name" in missing
    assert "email" in missing

    print("\nMissingFieldDetector logic works")


if __name__ == "__main__":
    test_missing_required_fields()