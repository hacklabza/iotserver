import io
import json

import pytest
from django.core.management.base import OutputWrapper

from iotserver.apps.device.management.commands.mqtt import Command
from iotserver.apps.device.models import DeviceStatus
from iotserver.apps.device.tests import factories as device_factories


@pytest.fixture
def command():
    command = Command()
    command.stdout = OutputWrapper(io.StringIO())
    return command


@pytest.mark.django_db
class TestHandleStatusQueue:
    def test_creates_device_status_for_existing_device(self, command, mocker):
        device = device_factories.DeviceFactory()
        message = mocker.Mock(
            topic=f'iot-devices/{device.id}/status',
            payload=json.dumps({'sonoff-switch': True}).encode(),
        )

        command.handle_status_queue(message)

        status = DeviceStatus.objects.get(device=device)
        assert status.status == {'sonoff-switch': True}

    def test_ignores_message_for_unknown_device(self, command, mocker):
        message = mocker.Mock(
            topic='iot-devices/00000000-0000-0000-0000-000000000000/status',
            payload=b'{}',
        )

        command.handle_status_queue(message)

        assert DeviceStatus.objects.count() == 0
        assert 'does not exist' in command.stdout._out.getvalue()


class TestHandleLogQueue:
    def test_writes_log_message_to_stdout(self, command, mocker):
        message = mocker.Mock(
            topic='iot-devices/device-1/logs', payload=b'Device disconnected'
        )

        command.handle_log_queue(message)

        output = command.stdout._out.getvalue()
        assert 'device-1' in output
        assert 'Device disconnected' in output


class TestMqttOnConnect:
    def test_subscribes_to_all_device_topics(self, command, mocker):
        client = mocker.Mock()

        command.mqtt_on_connect(client, None, None, None, None)

        client.subscribe.assert_called_once_with('iot-devices/#')


class TestMqttOnMessage:
    def test_dispatches_status_messages(self, command, mocker):
        mock_handle_status = mocker.patch.object(command, 'handle_status_queue')
        message = mocker.Mock(topic='iot-devices/device-1/status')

        command.mqtt_on_message(None, None, message)

        mock_handle_status.assert_called_once_with(message)

    def test_dispatches_log_messages(self, command, mocker):
        mock_handle_log = mocker.patch.object(command, 'handle_log_queue')
        message = mocker.Mock(topic='iot-devices/device-1/logs')

        command.mqtt_on_message(None, None, message)

        mock_handle_log.assert_called_once_with(message)

    def test_ignores_unrelated_topics(self, command, mocker):
        mock_handle_status = mocker.patch.object(command, 'handle_status_queue')
        mock_handle_log = mocker.patch.object(command, 'handle_log_queue')
        message = mocker.Mock(topic='iot-devices/device-1/toggle')

        command.mqtt_on_message(None, None, message)

        mock_handle_status.assert_not_called()
        mock_handle_log.assert_not_called()


class TestHandle:
    def test_connects_and_starts_loop_forever(self, command, mocker):
        mock_client_cls = mocker.patch(
            'iotserver.apps.device.management.commands.mqtt.mqtt.Client'
        )
        mocker.patch(
            'iotserver.apps.device.management.commands.mqtt.settings.MQTT',
            {'host': 'broker.local', 'port': 1883},
        )

        command.handle()

        client = mock_client_cls.return_value
        assert client.on_connect == command.mqtt_on_connect
        assert client.on_message == command.mqtt_on_message
        client.connect.assert_called_once_with(host='broker.local', port=1883)
        client.loop_forever.assert_called_once()
