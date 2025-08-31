import json

from django.forms import Textarea


class PrettyJSONWidget(Textarea):
    """A widget that pretty-prints JSON data."""
    def format_value(self, value):
        if value == "" or value is None:
            return None
        try:
            parsed = json.loads(value)
            return json.dumps(parsed, indent=4, sort_keys=True)
        except (TypeError, ValueError):
            return value