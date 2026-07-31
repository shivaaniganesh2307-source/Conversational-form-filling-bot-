from app.state_manager import StateManager


def test_create_empty_state():

    print("\nRunning test_create_empty_state...")

    manager = StateManager()

    state = manager.create_empty_space("MEDICAL_FORM")

    print("Generated State:")
    print(state)

    assert isinstance(state, dict)
    assert "first_name" in state
    assert "last_name" in state

    print("test_create_empty_state passed")


def test_update_state():

    print("\nRunning test_update_state...")

    manager = StateManager()

    state = {
        "first_name": "",
        "last_name": ""
    }

    print("Original State:")
    print(state)

    extracted_data = {
        "first_name": "John"
    }

    print("Extracted Data:")
    print(extracted_data)

    updated_state = manager.update_state(
        state,
        extracted_data
    )

    print("Updated State:")
    print(updated_state)

    assert updated_state["first_name"] == "John"

    print("test_update_state passed")


def test_invalid_form():

    print("\nRunning test_invalid_form...")

    manager = StateManager()

    result = manager.create_empty_space(
        "INVALID_FORM"
    )

    print("Result:")
    print(result)

    assert "error" in result

    print("test_invalid_form passed")


if __name__ == "__main__":

    test_create_empty_state()
    test_update_state()
    test_invalid_form()

    print("\n All StateManager tests passed!")