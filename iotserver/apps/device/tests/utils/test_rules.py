import hashlib
import json
import threading

import pytest

from iotserver.apps.device.utils import rules


class TestFindXpathValue:
    def test_returns_top_level_value(self):
        assert rules.find_xpath_value({'a': 1}, ['a']) == 1

    def test_returns_nested_value(self):
        # xpaths are passed in already reversed, e.g. 'a.b' -> ['b', 'a']
        assert rules.find_xpath_value({'a': {'b': 2}}, ['b', 'a']) == 2

    def test_returns_none_for_missing_key(self):
        assert rules.find_xpath_value({'a': 1}, ['missing']) is None

    def test_returns_none_when_intermediate_is_not_subscriptable(self):
        assert rules.find_xpath_value({'a': 1}, ['b', 'a']) is None


class TestEvaluateCondition:
    @pytest.mark.parametrize(
        'operator,input,value,expected',
        [
            ('eq', True, True, True),
            ('eq', True, False, False),
            ('gt', 5, 3, True),
            ('gt', 2, 3, False),
            ('lt', 2, 3, True),
        ],
    )
    def test_evaluate(self, operator, input, value, expected):
        assert rules.evaluate_condition(input, operator, value) is expected

    def test_returns_false_on_type_error(self):
        assert rules.evaluate_condition(None, 'gt', 3) is False


def test_handle_conditions_returns_must_and_should_booleans():
    rule_values = {
        'timer': True,
        'weather-service-current': {'rain': False},
        'mqtt-toggle': True,
    }
    input_value = {
        'conditions': {
            'must': {
                'timer': {'operator': 'eq', 'value': True},
                'weather-service-current.rain': {'operator': 'eq', 'value': False},
            },
            'should': {
                'mqtt-toggle': {'operator': 'eq', 'value': True},
            },
        }
    }

    assert rules.handle_conditions(rule_values, input_value) == {
        'must': [True, True],
        'should': [True],
    }


class TestValueToBool:
    @pytest.mark.parametrize(
        'value,expected',
        [
            ('true', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('false', False),
            ('0', False),
            (1, True),
            (0, False),
            (None, False),
            (True, True),
        ],
    )
    def test_value_to_bool(self, value, expected):
        assert rules.value_to_bool(value) is expected


class TestTimer:
    def test_within_range_same_day(self, mocker):
        mock_localtime = mocker.patch(
            'iotserver.apps.device.utils.rules.timezone.localtime'
        )
        mock_localtime.return_value.strftime.return_value = '1200'

        assert rules.timer(start_time='09:00', end_time='17:00') is True

    def test_outside_range_same_day(self, mocker):
        mock_localtime = mocker.patch(
            'iotserver.apps.device.utils.rules.timezone.localtime'
        )
        mock_localtime.return_value.strftime.return_value = '2000'

        assert rules.timer(start_time='09:00', end_time='17:00') is False

    def test_within_overnight_range(self, mocker):
        mock_localtime = mocker.patch(
            'iotserver.apps.device.utils.rules.timezone.localtime'
        )
        mock_localtime.return_value.strftime.return_value = '2300'

        assert rules.timer(start_time='18:00', end_time='05:00') is True

    def test_outside_overnight_range(self, mocker):
        mock_localtime = mocker.patch(
            'iotserver.apps.device.utils.rules.timezone.localtime'
        )
        mock_localtime.return_value.strftime.return_value = '1200'

        assert rules.timer(start_time='18:00', end_time='05:00') is False


class TestService:
    def test_returns_json_with_auth_header(self, mocker):
        mock_requests = mocker.patch('iotserver.apps.device.utils.rules.requests')
        mock_requests.get.return_value.json.return_value = {'temperature': 20}

        result = rules.service(url='http://example.com', auth_header='abc123')

        mock_requests.get.assert_called_once_with(
            'http://example.com', headers={'Authorization': 'Token abc123'}
        )
        mock_requests.get.return_value.raise_for_status.assert_called_once()
        assert result == {'temperature': 20}

    def test_omits_headers_without_auth_header(self, mocker):
        mock_requests = mocker.patch('iotserver.apps.device.utils.rules.requests')

        rules.service(url='http://example.com')

        mock_requests.get.assert_called_once_with('http://example.com', headers=None)


class TestMqttToggle:
    def test_returns_true_for_retained_truthy_value(self):
        assert rules.mqtt_toggle(topic='t', mqtt_values={'t': '1'}) is True

    def test_returns_false_for_missing_topic(self):
        assert rules.mqtt_toggle(topic='t', mqtt_values={}) is False


class TestSonoffToggle:
    def test_toggles_on(self, mocker):
        mock_sonoff_cls = mocker.patch('iotserver.apps.device.utils.rules.Sonoff')
        mock_sonoff_cls.return_value.toggle_device.return_value = 'on'

        result = rules.sonoff_toggle(on=True, device_id='abc123')

        mock_sonoff_cls.assert_called_once_with('abc123')
        mock_sonoff_cls.return_value.toggle_device.assert_called_once_with('on')
        assert result is True

    def test_toggles_off(self, mocker):
        mock_sonoff_cls = mocker.patch('iotserver.apps.device.utils.rules.Sonoff')
        mock_sonoff_cls.return_value.toggle_device.return_value = 'off'

        result = rules.sonoff_toggle(on=False, device_id='abc123')

        mock_sonoff_cls.return_value.toggle_device.assert_called_once_with('off')
        assert result is False


def test_rule_actions_dispatch_table():
    assert rules.RULE_ACTIONS == {
        'timer': rules.timer,
        'service': rules.service,
        'mqtt_toggle': rules.mqtt_toggle,
        'sonoff_toggle': rules.sonoff_toggle,
    }


class TestBuildMqttClient:
    @pytest.fixture
    def mock_client_cls(self, mocker):
        return mocker.patch('iotserver.apps.device.utils.rules.mqtt.Client')

    def test_connects_and_starts_loop_with_default_port(self, mock_client_cls):
        client = rules._build_mqtt_client(
            {'client_id': 'device-1', 'host': 'broker.local'}, None, None
        )

        mock_client_cls.assert_called_once_with(
            rules.mqtt.CallbackAPIVersion.VERSION2, client_id='device-1'
        )
        client.connect.assert_called_once_with(host='broker.local', port=1883)
        client.loop_start.assert_called_once()

    def test_uses_configured_port(self, mock_client_cls):
        client = rules._build_mqtt_client(
            {'client_id': 'd', 'host': 'h', 'port': 8883}, None, None
        )

        client.connect.assert_called_once_with(host='h', port=8883)

    def test_sets_credentials_when_configured(self, mock_client_cls):
        client = rules._build_mqtt_client(
            {'client_id': 'd', 'host': 'h', 'username': 'user', 'password': 'pass'},
            None,
            None,
        )

        client.username_pw_set.assert_called_once_with('user', 'pass')

    def test_skips_credentials_when_not_configured(self, mock_client_cls):
        client = rules._build_mqtt_client({'client_id': 'd', 'host': 'h'}, None, None)

        client.username_pw_set.assert_not_called()

    def test_enables_tls_when_configured(self, mock_client_cls):
        client = rules._build_mqtt_client(
            {'client_id': 'd', 'host': 'h', 'ssl_enabled': True}, None, None
        )

        client.tls_set.assert_called_once()

    def test_sets_lastwill_when_configured(self, mock_client_cls):
        client = rules._build_mqtt_client(
            {
                'client_id': 'd',
                'host': 'h',
                'lastwill': {'topic': 'iot-devices/d/logs', 'message': 'disconnected'},
            },
            None,
            None,
        )

        client.will_set.assert_called_once_with(
            topic='iot-devices/d/logs', payload='disconnected'
        )


class TestResolveRuleParams:
    def test_passes_through_plain_values(self):
        rule = {
            'action': 'timer',
            'input': {'start_time': '18:00', 'end_time': '05:00'},
        }

        assert rules._resolve_rule_params(rule, {}, {}) == {
            'start_time': '18:00',
            'end_time': '05:00',
        }

    def test_evaluates_conditions(self):
        rule = {
            'action': 'sonoff_toggle',
            'input': {
                'device_id': 'abc123',
                'on': {
                    'conditions': {
                        'must': {'timer': {'operator': 'eq', 'value': True}},
                        'should': {},
                    }
                },
            },
        }

        result = rules._resolve_rule_params(rule, {'timer': True}, {})

        assert result == {'device_id': 'abc123', 'on': True}

    def test_evaluates_should_only_conditions(self):
        rule = {
            'action': 'sonoff_toggle',
            'input': {
                'device_id': 'abc123',
                'on': {
                    'conditions': {
                        'should': {'mqtt-toggle': {'operator': 'eq', 'value': True}}
                    }
                },
            },
        }

        result = rules._resolve_rule_params(rule, {'mqtt-toggle': False}, {})

        assert result == {'device_id': 'abc123', 'on': False}

    def test_injects_mqtt_values_for_mqtt_toggle_action(self):
        rule = {'action': 'mqtt_toggle', 'input': {'topic': 'iot-devices/x/toggle'}}
        mqtt_values = {'iot-devices/x/toggle': '1'}

        result = rules._resolve_rule_params(rule, {}, mqtt_values)

        assert result == {'topic': 'iot-devices/x/toggle', 'mqtt_values': mqtt_values}


class TestPublishStatus:
    def test_publishes_when_status_has_changed(self, mocker):
        client = mocker.Mock()

        status_hash = rules._publish_status(client, 'device-1', {'a': 1}, None)

        payload = json.dumps({'a': 1}, sort_keys=True)
        client.publish.assert_called_once_with('iot-devices/device-1/status', payload)
        assert status_hash == hashlib.sha1(payload.encode()).digest()

    def test_skips_publish_when_status_unchanged(self, mocker):
        client = mocker.Mock()
        payload = json.dumps({'a': 1}, sort_keys=True)
        previous_hash = hashlib.sha1(payload.encode()).digest()

        result_hash = rules._publish_status(client, 'device-1', {'a': 1}, previous_hash)

        client.publish.assert_not_called()
        assert result_hash == previous_hash


class TestPublishLog:
    def test_publishes_when_at_or_above_threshold(self, mocker):
        mock_logger = mocker.patch('iotserver.apps.device.utils.rules.logger')
        client = mocker.Mock()

        rules._publish_log(client, 'device-1', {'level': 'warning'}, 'error', 'boom')

        mock_logger.error.assert_called_once_with('boom')
        client.publish.assert_called_once_with('iot-devices/device-1/logs', 'boom')

    def test_suppresses_publish_below_threshold(self, mocker):
        mock_logger = mocker.patch('iotserver.apps.device.utils.rules.logger')
        client = mocker.Mock()

        rules._publish_log(client, 'device-1', {'level': 'warning'}, 'debug', 'noisy')

        mock_logger.debug.assert_called_once_with('noisy')
        client.publish.assert_not_called()


class TestRunDevice:
    def _device(self, mocker, **config_overrides):
        config = {
            'main': {'process_interval': 0},
            'health': {'url': 'http://example.com/health/'},
            'mqtt': {'client_id': 'device-1', 'host': 'broker.local'},
            'logging': {'level': 'warning'},
            'pins': [],
        }
        config.update(config_overrides)
        return mocker.Mock(id='device-1', full_config=config)

    def test_runs_health_check_dispatches_rule_and_publishes_status(self, mocker):
        stop_event = threading.Event()
        mock_client = mocker.Mock()
        mocker.patch(
            'iotserver.apps.device.utils.rules._build_mqtt_client',
            return_value=mock_client,
        )
        mock_requests_get = mocker.patch(
            'iotserver.apps.device.utils.rules.requests.get'
        )
        mock_action = mocker.Mock(return_value=True)
        mocker.patch.dict(
            'iotserver.apps.device.utils.rules.RULE_ACTIONS', {'timer': mock_action}
        )
        mock_publish_status = mocker.patch(
            'iotserver.apps.device.utils.rules._publish_status',
            side_effect=lambda *a, **k: stop_event.set(),
        )

        device = self._device(
            mocker,
            pins=[
                {
                    'identifier': 'day-timer',
                    'interval': 1,
                    'rule': {
                        'action': 'timer',
                        'input': {'start_time': '18:00', 'end_time': '05:00'},
                    },
                }
            ],
        )

        rules.run_device(device, stop_event)

        mock_requests_get.assert_called_once_with(
            'http://example.com/health/', timeout=10
        )
        mock_action.assert_called_once_with(start_time='18:00', end_time='05:00')
        mock_publish_status.assert_called_once()
        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()

    def test_catches_iteration_errors_and_keeps_looping(self, mocker):
        stop_event = threading.Event()
        mock_client = mocker.Mock()
        mocker.patch(
            'iotserver.apps.device.utils.rules._build_mqtt_client',
            return_value=mock_client,
        )
        mocker.patch(
            'iotserver.apps.device.utils.rules.requests.get',
            side_effect=[Exception('boom'), None],
        )
        mock_publish_log = mocker.patch(
            'iotserver.apps.device.utils.rules._publish_log'
        )
        mocker.patch(
            'iotserver.apps.device.utils.rules._publish_status',
            side_effect=lambda *a, **k: stop_event.set(),
        )

        device = self._device(mocker)

        rules.run_device(device, stop_event)

        mock_publish_log.assert_called_once()
        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()

    def test_subscribes_to_mqtt_toggle_topics_on_connect(self, mocker):
        stop_event = threading.Event()
        mock_client = mocker.Mock()
        mock_build_client = mocker.patch(
            'iotserver.apps.device.utils.rules._build_mqtt_client',
            return_value=mock_client,
        )
        mocker.patch('iotserver.apps.device.utils.rules.requests.get')
        mocker.patch(
            'iotserver.apps.device.utils.rules._publish_status',
            side_effect=lambda *a, **k: stop_event.set(),
        )

        device = self._device(
            mocker,
            pins=[
                {
                    'identifier': 'mqtt-toggle',
                    'interval': 1,
                    'rule': {
                        'action': 'mqtt_toggle',
                        'input': {'topic': 'iot-devices/device-1/toggle'},
                    },
                }
            ],
        )

        rules.run_device(device, stop_event)

        _, on_connect, _on_message = mock_build_client.call_args[0]
        on_connect(mock_client, None, None, None, None)

        mock_client.subscribe.assert_called_once_with('iot-devices/device-1/toggle')
