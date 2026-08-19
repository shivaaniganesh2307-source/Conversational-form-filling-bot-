class ConfidenceEngine:
    """
    Determines whether extracted values need confirmation.

    Confidence is calculated by the backend rather than using
    another LLM call.
    """

    def confidence_evaluation(self, extracted_data):

        if not isinstance(extracted_data, dict):
            return {}

        confidence_scores = {}

        for field, value in extracted_data.items():

            if value is None or value == "":
                continue

            if isinstance(value, bool):
                confidence_scores[field] = 1.0
                continue

            if isinstance(value, (int, float)):
                confidence_scores[field] = 1.0
                continue

            if isinstance(value, str):
                if value.strip():
                    confidence_scores[field] = 0.95

        return confidence_scores

    def low_confidence_fields(self, confidence_scores, threshold=0.80):

        if not isinstance(confidence_scores, dict):
            return []

        low_confidence = []

        for field, score in confidence_scores.items():
            try:
                score = float(score)
            except (TypeError, ValueError):
                continue

            if score < threshold:
                low_confidence.append((field, score))

        return low_confidence
