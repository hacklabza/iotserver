class PrettyJSONWidget:
    def format_value(self, value):
        import json
        try:
            parsed = json.loads(value)
            return json.dumps(parsed, indent=4, sort_keys=True)
        except (ValueError, TypeError):
            return value