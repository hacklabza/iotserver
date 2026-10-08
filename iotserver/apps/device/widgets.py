import json

from django.forms import Textarea
from django.utils.html import format_html
from django.utils.safestring import mark_safe

MASK_VALUE = '**********'
MASKED_KEYS = frozenset({'webrepl_password', 'password', 'auth_header'})


def _is_masked_key(key):
    return isinstance(key, str) and key.lower() in MASKED_KEYS


def _mask_secrets(value):
    """Recursively replace values of masked keys with MASK_VALUE."""
    if isinstance(value, dict):
        return {
            key: MASK_VALUE
            if _is_masked_key(key) and val not in (None, '')
            else _mask_secrets(val)
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_mask_secrets(item) for item in value]
    return value


def _restore_masked(submitted, original):
    """Recursively replace untouched MASK_VALUE placeholders with their original values."""
    if isinstance(submitted, dict):
        original_dict = original if isinstance(original, dict) else {}
        restored = {}
        for key, val in submitted.items():
            if _is_masked_key(key) and val == MASK_VALUE and key in original_dict:
                restored[key] = original_dict[key]
            else:
                restored[key] = _restore_masked(val, original_dict.get(key))
        return restored
    if isinstance(submitted, list):
        original_list = original if isinstance(original, list) else []
        return [
            _restore_masked(
                item, original_list[index] if index < len(original_list) else None
            )
            for index, item in enumerate(submitted)
        ]
    return submitted


class PrettyJSONWidget(Textarea):
    """A widget that pretty-prints JSON data and masks sensitive keys on display.

    Masked keys (see MASKED_KEYS) are never rendered in plain text. A hidden
    companion field carries the real, unmasked value across the request so
    that untouched masked fields are restored instead of being saved as the
    literal mask placeholder.
    """

    ORIGINAL_FIELD_SUFFIX = '__pretty_json_original'

    def original_field_name(self, name):
        return f'{name}{self.ORIGINAL_FIELD_SUFFIX}'

    def format_value(self, value):
        if value is None or value == '':
            return None
        # value may already be a parsed dict/list (e.g. a field default) rather than a string.
        if isinstance(value, (dict, list)):
            return json.dumps(_mask_secrets(value), indent=4, sort_keys=True)
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return value
        if isinstance(parsed, (dict, list)):
            parsed = _mask_secrets(parsed)
        return json.dumps(parsed, indent=4, sort_keys=True)

    def render(self, name, value, attrs=None, renderer=None):
        rendered = super().render(name, value, attrs, renderer)
        original = self._to_python(value)
        original_json = '' if original is None else json.dumps(original)
        hidden_input = format_html(
            '<input type="hidden" name="{}" value="{}">',
            self.original_field_name(name),
            original_json,
        )
        return mark_safe(f'{rendered}{hidden_input}')

    def value_from_datadict(self, data, files, name):
        submitted = super().value_from_datadict(data, files, name)
        original = self._to_python(data.get(self.original_field_name(name)))
        submitted_parsed = self._to_python(submitted)

        if original is None or not isinstance(submitted_parsed, (dict, list)):
            return submitted

        return json.dumps(_restore_masked(submitted_parsed, original))

    @staticmethod
    def _to_python(value):
        if value is None or value == '':
            return None
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return None
