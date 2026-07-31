# Connects our application with Qwen LLM using Ollama
# Extracts form answers from user messages and converts them into JSON
import json
import requests #helps python send the message to Ollama
class LLMExtractor: #connect to api, send prompt, get response
    def __init__(self):
        # Ollama API address
        self.ollama_url = "http://localhost:11434/api/generate"

    def extract_fields(self, user_message, schema):
        # Create instructions for the AI
        prompt = f"""
        Extract information from the user message
        based on this form schema:
        {json.dumps(schema)}
        User message:
        {user_message}
        Return only JSON.
        Format:
        {{
            "extracted_data": {{}},
            "confidence_scores": {{}}
        }}
        """
        try:
            # Send request to Ollama
            response = requests.post(
                self.ollama_url,
                json={
                    "model":"qwen3:8b",
                    "prompt":prompt,
                    "stream":False
                },
                timeout=10
            )
            # Convert response into JSON
            result = response.json()
            # Extract AI response
            answer = result.get(
                "response",
                "{}"
            )
            # Convert string JSON into Python dictionary
            return json.loads(answer)
        except Exception:
            # If AI fails return empty result
            return {
                "extracted_data": {},
                "confidence_scores": {}
            }
            #dumps- convert python to json
            #loads - convert json to python