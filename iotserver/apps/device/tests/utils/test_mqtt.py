import pytest

from iotserver.apps.device.utils import mqtt


@pytest.fixture
def publish_single(mocker):
    return mocker.patch('iotserver.apps.device.utils.mqtt.mqtt_publish.single')


def test_toggle_uses_django_settings(mocker, publish_single):
    mocker.patch.object(mqtt.settings, 'MQTT', {'host': 'mqtt', 'port': 1883})

    mqtt.toggle('device-id', 1)

    publish_single.assert_called_once_with(
        'iot-devices/device-id/toggle',
        1,
        hostname='mqtt',
        port=1883,
        retain=True,
    )


def test_toggle_uses_supplied_settings(publish_single):
    mqtt.toggle('device-id', 0, {'host': 'example.com', 'port': 1884})

    publish_single.assert_called_once_with(
        'iot-devices/device-id/toggle',
        0,
        hostname='example.com',
        port=1884,
        retain=True,
    )
