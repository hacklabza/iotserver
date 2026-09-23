import json

from iotserver.apps.device.widgets import MASK_VALUE, PrettyJSONWidget


class TestPrettyJSONWidget(object):
    def setup_method(self, test_method):
        self.widget = PrettyJSONWidget()

    # -- format_value -----------------------------------------------------

    def test_format_value_none(self):
        assert self.widget.format_value(None) is None

    def test_format_value_empty_string(self):
        assert self.widget.format_value("") is None

    def test_format_value_json_string(self):
        value = json.dumps({'b': 1, 'a': 2})

        result = self.widget.format_value(value)

        assert result == json.dumps({'a': 2, 'b': 1}, indent=4, sort_keys=True)

    def test_format_value_dict(self):
        result = self.widget.format_value({'b': 1, 'a': 2})

        assert result == json.dumps({'a': 2, 'b': 1}, indent=4, sort_keys=True)

    def test_format_value_list(self):
        result = self.widget.format_value([3, 1, 2])

        assert result == json.dumps([3, 1, 2], indent=4, sort_keys=True)

    def test_format_value_invalid_json_string_returned_unchanged(self):
        value = '{not valid json'

        assert self.widget.format_value(value) == value

    def test_format_value_non_json_scalar_returned_unchanged(self):
        assert self.widget.format_value(123) == 123

    def test_format_value_masks_top_level_secret_keys(self):
        value = {
            'password': 'hunter2',
            'webrepl_password': 'secret',
            'auth_header': 'Bearer xyz',
        }

        result = json.loads(self.widget.format_value(value))

        assert result == {
            'password': MASK_VALUE,
            'webrepl_password': MASK_VALUE,
            'auth_header': MASK_VALUE,
        }

    def test_format_value_masks_nested_secret_keys(self):
        value = {'wifi': {'ssid': 'home', 'password': 'hunter2'}, 'name': 'device'}

        result = json.loads(self.widget.format_value(value))

        assert result == {
            'wifi': {'ssid': 'home', 'password': MASK_VALUE},
            'name': 'device',
        }

    def test_format_value_masks_secret_keys_in_list_of_dicts(self):
        value = {
            'endpoints': [{'auth_header': 'Bearer xyz'}, {'auth_header': 'Bearer abc'}]
        }

        result = json.loads(self.widget.format_value(value))

        assert result == {
            'endpoints': [{'auth_header': MASK_VALUE}, {'auth_header': MASK_VALUE}]
        }

    def test_format_value_does_not_mask_empty_secret_value(self):
        result = json.loads(self.widget.format_value({'password': ''}))

        assert result == {'password': ''}

    def test_format_value_is_case_insensitive_for_secret_keys(self):
        result = json.loads(self.widget.format_value({'Password': 'hunter2'}))

        assert result == {'Password': MASK_VALUE}

    # -- render -------------------------------------------------------------

    def test_render_includes_masked_visible_value(self):
        html = self.widget.render('config', {'password': 'hunter2'})
        visible_textarea = html.split('__pretty_json_original')[0]

        assert MASK_VALUE in visible_textarea
        assert 'hunter2' not in visible_textarea

    def test_render_includes_hidden_original_value(self):
        html = self.widget.render('config', {'password': 'hunter2'})

        assert 'name="config__pretty_json_original"' in html
        assert 'hunter2' in html

    def test_render_hidden_original_empty_for_none_value(self):
        html = self.widget.render('config', None)

        assert 'name="config__pretty_json_original" value=""' in html

    # -- value_from_datadict --------------------------------------------

    def test_value_from_datadict_restores_untouched_masked_value(self):
        original = {'ssid': 'home', 'password': 'hunter2'}
        data = {
            'config': json.dumps({'ssid': 'home', 'password': MASK_VALUE}),
            'config__pretty_json_original': json.dumps(original),
        }

        result = json.loads(self.widget.value_from_datadict(data, {}, 'config'))

        assert result == original

    def test_value_from_datadict_keeps_new_secret_value(self):
        original = {'ssid': 'home', 'password': 'hunter2'}
        data = {
            'config': json.dumps({'ssid': 'home', 'password': 'new-password'}),
            'config__pretty_json_original': json.dumps(original),
        }

        result = json.loads(self.widget.value_from_datadict(data, {}, 'config'))

        assert result == {'ssid': 'home', 'password': 'new-password'}

    def test_value_from_datadict_restores_nested_untouched_masked_value(self):
        original = {'wifi': {'ssid': 'home', 'password': 'hunter2'}}
        data = {
            'config': json.dumps({'wifi': {'ssid': 'home', 'password': MASK_VALUE}}),
            'config__pretty_json_original': json.dumps(original),
        }

        result = json.loads(self.widget.value_from_datadict(data, {}, 'config'))

        assert result == original

    def test_value_from_datadict_without_original_returns_submitted_unchanged(self):
        data = {'config': json.dumps({'password': MASK_VALUE})}

        result = self.widget.value_from_datadict(data, {}, 'config')

        assert result == data['config']

    def test_value_from_datadict_non_structured_submission_returned_unchanged(self):
        data = {
            'config': 'not json',
            'config__pretty_json_original': json.dumps({'password': 'hunter2'}),
        }

        result = self.widget.value_from_datadict(data, {}, 'config')

        assert result == 'not json'
