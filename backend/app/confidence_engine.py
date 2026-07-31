class ConfidenceEngine:
    def confidence_evaluation(self, extracted_data):
        confidence_scores = {}
        for field in extracted_data:
            confidence_scores[field] = 0.95
        return confidence_scores

    def low_confidence_fields(self, confidence_scores, threshold=0.80):
        low_confidence = []
        for field, score in confidence_scores.items():
            if score < threshold:
                low_confidence.append(field)
        return low_confidence  