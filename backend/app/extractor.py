import os
import json
import requests


class LLMExtractor:
    """
    Uses a locally-hosted Ollama model to pull form field values out
    of free-text user messages. No external API calls.

    Token-efficiency notes:
    - Only fields that are still missing (plus whichever field is
      currently being asked about) are described to the model. A
      field that's already filled is never asked about again anyway,
      so leaving it out of the prompt costs nothing functionally and
      is the single biggest token saver on long forms.
    - Field descriptions are trimmed to just {type, choices} -- no
      label text, no restating already-known values every turn.
    - The response token budget scales a little with how many fields
      are in play instead of always requesting the same fixed amount.

    Batching (adaptive, generic across any form):
    - Small local models lose recall when asked to check a message
      against many candidate fields in one pass. Rather than always
      sending every relevant field in a single call, fields are split
      into chunks of EXTRACTOR_CHUNK_SIZE and each chunk gets its own
      call, merging the results.
    - This only costs anything when it needs to: a form (or a turn)
      with few relevant fields still makes exactly one call, same as
      before. The extra calls only happen on the exact cases where
      recall was actually struggling -- many fields active at once.
    - Nothing here is per-form. Chunking just slices whatever
      field_information was computed for this turn, so it applies the
      same way to every schema without any per-form code.
    """

    def __init__(self):
        self.ollama_url = os.getenv(
            "OLLAMA_URL",
            "http://localhost:11434/api/generate"
        )
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        self.debug = os.getenv("EXTRACTOR_DEBUG", "0") == "1"

        # Off by default: real testing on qwen2.5:3b showed schema-
        # constrained decoding reduces how many fields the model
        # bothers to fill in (an empty extracted_data trivially
        # satisfies the schema, so a small model takes that easy out
        # more often than it should). Loose JSON mode measured better
        # recall in practice. Larger models tend to handle constraints
        # without that tradeoff, so this is left available to opt
        # into if you move to a bigger model later.
        self.use_structured_output = os.getenv("EXTRACTOR_STRUCTURED_OUTPUT", "0") == "1"

        # How many fields go into a single extraction call. Forms/
        # turns with more relevant fields than this get split into
        # multiple smaller calls instead of one big one. Set high
        # enough that a normal-sized form (e.g. 8 fields) never pays
        # the extra-call cost -- only genuinely large forms do.
        self.chunk_size = int(os.getenv("EXTRACTOR_CHUNK_SIZE", "10"))

        # How long a single Ollama call can take before giving up.
        # Raised from the original 120s: with batching, a form can
        # now involve more than one sequential call, and a model that
        # got unloaded from memory between messages needs time to
        # reload before it can even start generating.
        self.request_timeout = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))

    # ------------------------------------------------------------
    # STRUCTURED OUTPUT SCHEMA (opt-in, see use_structured_output)
    # ------------------------------------------------------------

    def _json_type_for_field(self, rules):
        field_type = rules.get("type", "string")

        if field_type == "choice":
            choices = rules.get("choices")
            if isinstance(choices, list) and choices:
                return {"type": "string", "enum": choices}
            return {"type": "string"}

        if field_type == "boolean":
            return {"type": "boolean"}

        if field_type == "integer":
            return {"type": "integer"}

        if field_type == "number":
            return {"type": "number"}

        return {"type": "string"}

    def _build_response_schema(self, field_information, fields):
        properties = {}

        for field_name in field_information:
            rules = fields.get(field_name, {})
            properties[field_name] = self._json_type_for_field(
                rules if isinstance(rules, dict) else {}
            )

        return {
            "type": "object",
            "properties": {
                "extracted_data": {
                    "type": "object",
                    "properties": properties,
                    "additionalProperties": False
                },
                "intent": {
                    "type": "string",
                    "enum": ["answer", "update", "chat"]
                }
            },
            "required": ["extracted_data", "intent"]
        }

    # ------------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ------------------------------------------------------------

    def extract_fields(
        self,
        user_message,
        schema,
        current_state=None,
        current_field=None,
        missing_fields=None
    ):
        current_state = current_state if isinstance(current_state, dict) else {}
        fields = schema.get("fields", {})

        if not isinstance(fields, dict):
            return {"extracted_data": {}, "confidence_scores": {}, "intent": "chat"}

        # Only describe fields that are still relevant.
        if missing_fields:
            relevant_field_names = set(missing_fields)
            if current_field:
                relevant_field_names.add(current_field)
        else:
            relevant_field_names = set(fields.keys())

        field_information = {}
        for field_name in relevant_field_names:
            rules = fields.get(field_name)
            if not isinstance(rules, dict):
                continue
            entry = {"type": rules.get("type", "string")}
            choices = rules.get("choices")
            if choices:
                entry["choices"] = choices
            field_information[field_name] = entry

        if not field_information:
            # Nothing left to extract for -- avoid a wasted LLM call.
            return {"extracted_data": {}, "confidence_scores": {}, "intent": "chat"}

        field_items = list(field_information.items())

        # Fast path: few enough fields that one call is fine (this is
        # the common case -- most forms most of the time).
        if len(field_items) <= self.chunk_size:
            return self._extract_single_call(
                user_message, dict(field_items), fields, current_field
            )

        # Chunked path: split into groups of chunk_size and merge.
        # current_field is always kept visible in every chunk's
        # prompt context (even if its own definition lives in a
        # different chunk) so "what's being asked about" stays
        # consistent across all the calls.
        combined_extracted = {}
        any_answer = False

        for i in range(0, len(field_items), self.chunk_size):
            chunk = dict(field_items[i:i + self.chunk_size])
            result = self._extract_single_call(
                user_message, chunk, fields, current_field
            )
            combined_extracted.update(result.get("extracted_data", {}))
            if result.get("intent") == "answer":
                any_answer = True

        intent = "answer" if (any_answer or combined_extracted) else "chat"

        return {
            "extracted_data": combined_extracted,
            "confidence_scores": {},
            "intent": intent
        }

    # ------------------------------------------------------------
    # SINGLE OLLAMA CALL FOR ONE CHUNK OF FIELDS
    # ------------------------------------------------------------

    def _extract_single_call(self, user_message, field_information, fields, current_field):

        current_field_text = current_field if current_field in fields else "none"

        prompt = f"""Extract form data from the user's message. Return ONLY JSON, no prose, no markdown.

FIELDS NEEDED:
{json.dumps(field_information, separators=(",", ":"))}

CURRENTLY ASKING ABOUT:
{current_field_text}

USER MESSAGE:
{user_message}

FORMAT:
{{"extracted_data":{{}},"intent":"answer"}}

RULES:
- Extract every field the user gave a value for, not only the one being asked about.
- Only use field names listed in FIELDS NEEDED. Never invent a field or a value.
- Omit fields the user didn't mention. Never return null or empty values.
- If both first_name and last_name are listed and a full name is given, split it.
- For boolean fields, map "yes / I do / I have it" style language to true and "no / I don't" style language to false.
- Give numbers as numbers for numeric field types.
- For "choice" fields, only pick an option if the user's own words state or clearly restate one of the listed choices. Do NOT infer a choice from outside knowledge (e.g. do not assume a car brand implies a fuel type, do not assume "I'm registering a car" means the choice literally named "New Registration") unless the user's own wording actually says it.
- If you are not confident a value was actually given for a field, leave it out rather than guessing.
- If the message contains no extractable form information, return an empty extracted_data and intent "chat"."""

        predict_budget = min(60 + 25 * len(field_information), 350)

        response_schema = self._build_response_schema(field_information, fields)

        def call_ollama(format_value):
            return requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": format_value,
                    # Keep the model resident in memory for 30 minutes
                    # instead of Ollama's ~5 minute default. Gaps
                    # between messages during normal use/testing
                    # otherwise force a slow reload from disk on the
                    # next call, which is what a "timed out" error
                    # usually actually is.
                    "keep_alive": "30m",
                    "options": {
                        "temperature": 0,
                        "num_predict": predict_budget
                    }
                },
                timeout=self.request_timeout
            )

        try:
            if self.use_structured_output:
                try:
                    response = call_ollama(response_schema)
                    response.raise_for_status()
                except requests.exceptions.HTTPError:
                    print(
                        "[EXTRACTOR WARNING] Structured output request failed -- "
                        "falling back to loose JSON mode. If this persists, "
                        "your Ollama version may predate schema support (0.5+)."
                    )
                    response = call_ollama("json")
                    response.raise_for_status()
            else:
                response = call_ollama("json")
                response.raise_for_status()

            result = response.json()
            raw_response = result.get("response", "{}").strip()

            if self.debug:
                print("\n========== RAW LLM RESPONSE ==========")
                print(f"[chunk fields: {list(field_information.keys())}]")
                print(raw_response)
                print("=======================================\n")

            parsed = json.loads(raw_response)

            if not isinstance(parsed, dict):
                return {"extracted_data": {}, "confidence_scores": {}, "intent": "chat"}

            extracted_data = parsed.get("extracted_data", {})

            if not isinstance(extracted_data, dict):
                extracted_data = {}

            # SECURITY: only accept fields that were actually offered
            # to the model this call (field_information), not just
            # any field that happens to exist somewhere on the
            # schema. This is what stops an already-filled, correct
            # field from getting silently overwritten when the model
            # ignores "Only use field names listed in FIELDS NEEDED"
            # and returns something outside what it was actually
            # asked about -- which small models do often enough that
            # the instruction alone isn't a reliable guarantee.
            cleaned_data = {}
            for field, value in extracted_data.items():
                if field not in field_information:
                    continue
                if value in (None, ""):
                    continue

                # Hard guard for "choice" fields: only accept a value
                # if it (or a close variant) actually appears in the
                # user's own words.
                rules = fields.get(field, {})
                if isinstance(rules, dict) and rules.get("type") == "choice":
                    value_str = str(value).strip().lower()
                    message_lower = user_message.lower()
                    message_words = set(
                        w.strip(".,!?'\"") for w in message_lower.split()
                    )

                    grounded = value_str in message_lower or any(
                        len(word) >= 3
                        and (value_str.startswith(word) or word.startswith(value_str))
                        for word in message_words
                    )

                    if not grounded:
                        continue

                cleaned_data[field] = value

            intent = parsed.get("intent", "answer")
            if intent not in {"answer", "update", "chat"}:
                intent = "answer" if cleaned_data else "chat"

            return {
                "extracted_data": cleaned_data,
                "confidence_scores": {},
                "intent": intent
            }

        except requests.exceptions.Timeout:
            print("[EXTRACTOR ERROR] Ollama request timed out.")
            return {"extracted_data": {}, "confidence_scores": {}, "intent": "chat"}

        except requests.exceptions.ConnectionError:
            print("[EXTRACTOR ERROR] Could not connect to Ollama. Is `ollama serve` running?")
            return {"extracted_data": {}, "confidence_scores": {}, "intent": "chat"}

        except json.JSONDecodeError as e:
            print(f"[EXTRACTOR ERROR] Model returned invalid JSON: {e}")
            return {"extracted_data": {}, "confidence_scores": {}, "intent": "chat"}

        except Exception as e:
            print(f"[EXTRACTOR ERROR] {e}")
            return {"extracted_data": {}, "confidence_scores": {}, "intent": "chat"}
