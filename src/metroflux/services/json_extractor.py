import json


class JsonExtractor:
    def extract_field(self, data, field):
        try:
            return data[field]
        except Exception as e:
            raise Exception(f"Field '{field}' not found or not valid JSON: {e}")

    def extract_json(self, text):
        start = "```json"
        end = "```"
        if start in text and end in text:
            raw_json = text.split(start)[1].split(end)[0].strip()
            try:
                return json.loads(raw_json)
            except json.JSONDecodeError as e:
                raise Exception(f"Invalid JSON format: {e}")

        raise Exception(
            "JSON block not found. Expected to wrap output in: ```json ... ```"
        )
