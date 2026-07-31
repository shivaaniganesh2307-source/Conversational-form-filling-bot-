from app.confidence_engine import ConfidenceEngine


def test_confidence_evaluation():

    print("\nRunning test_confidence_evaluation...")

    engine = ConfidenceEngine()

    extracted_data = {
        "first_name": "John",
        "last_name": "Smith"
    }

    print("Extracted Data:")
    print(extracted_data)

    scores = engine.confidence_evaluation(
        extracted_data
    )

    print("Confidence Scores:")
    print(scores)

    assert scores["first_name"] == 0.95
    assert scores["last_name"] == 0.95

    print("test_confidence_evaluation passed")


def test_low_confidence_fields():

    print("\nRunning test_low_confidence_fields...")

    engine = ConfidenceEngine()

    confidence_scores = {
        "first_name": 0.95,
        "uic": 0.60,
        "email": 0.70
    }

    print("Confidence Scores:")
    print(confidence_scores)

    low_confidence = engine.low_confidence_fields(
        confidence_scores
    )

    print("Low Confidence Fields:")
    print(low_confidence)

    assert "uic" in low_confidence
    assert "email" in low_confidence
    assert "first_name" not in low_confidence

    print("test_low_confidence_fields passed")


def test_no_low_confidence_fields():

    print("\nRunning test_no_low_confidence_fields...")

    engine = ConfidenceEngine()

    confidence_scores = {
        "first_name": 0.95,
        "last_name": 0.90
    }

    print("Confidence Scores:")
    print(confidence_scores)

    low_confidence = engine.low_confidence_fields(
        confidence_scores
    )

    print("Low Confidence Fields:")
    print(low_confidence)

    assert low_confidence == []

    print(" test_no_low_confidence_fields passed")


if __name__ == "__main__":

    test_confidence_evaluation()
    test_low_confidence_fields()
    test_no_low_confidence_fields()

    print("\n All ConfidenceEngine tests passed!")