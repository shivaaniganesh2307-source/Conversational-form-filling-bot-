from app.llm_extractor import LLMExtractor
from unittest.mock import patch


def test_extract_fields_success():

    print("\nRunning test_extract_fields_success...")

    mock_response = {
        "response": """
        {
            "extracted_data": {
                "first_name": "John"
            },
            "confidence_scores": {
                "first_name": 0.95
            }
        }
        """
    }

    print("Mock Response:")
    print(mock_response)

    with patch("requests.post") as mock_post:

        mock_post.return_value.json.return_value = mock_response

        extractor = LLMExtractor()

        print("\nSending Sample Message:")
        print("My name is John")

        result = extractor.extract_fields(
            "My name is John",
            {}
        )

        print("\nLLM Result:")
        print(result)

        assert result["extracted_data"]["first_name"] == "John"
        assert result["confidence_scores"]["first_name"] == 0.95

        print("\ntest_extract_fields_success passed")


if __name__ == "__main__":

    test_extract_fields_success()

    print("\nLLM Extractor Test Passed!")