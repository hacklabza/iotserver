import json

import pytest

from iotserver.apps.device import models
from iotserver.apps.device.exceptions import DeviceUnreachableError
from iotserver.apps.device.tests import factories as device_factories


@pytest.mark.django_db
class TestLocationModel(object):
    def setup_method(self, test_method):
        self.location = device_factories.LocationFactory()

    def test_str(self):
        assert str(self.location) == self.location.name

    def test_resource_url(self):
        assert str(self.location.pk) in self.location.resource_url

    def test_coordinates(self):
        assert self.location.coordinates == {
            'latitude': self.location.position.y,
            'longitude': self.location.position.x,
        }


@pytest.mark.django_db
class TestDeviceTypeModel(object):
    def setup_method(self, test_method):
        self.device_type = device_factories.DeviceTypeFactory()

    def test_str(self):
        assert str(self.device_type) == self.device_type.name

    def test_resource_url(self):
        assert str(self.device_type.pk) in self.device_type.resource_url


@pytest.mark.django_db
class TestDeviceModel(object):
    def setup_method(self, test_method):
        self.device = device_factories.DeviceFactory()
        self.device_pin = device_factories.DevicePinFactory(devices=[self.device])
        self.device_statuses = [
            device_factories.DeviceStatusFactory(
                device=self.device,
                status={
                    'dht-sensor': {'humidity': 10, 'temperature': 10},
                    'light-sensor': 10,
                },
            ),
            device_factories.DeviceStatusFactory(
                device=self.device,
                status={
                    'dht-sensor': {'humidity': 20, 'temperature': 20},
                    'light-sensor': 20,
                },
            ),
            device_factories.DeviceStatusFactory(
                device=self.device,
                status={
                    'dht-sensor': {'humidity': 12, 'temperature': 12},
                    'light-sensor': 12,
                },
            ),
        ]
        self.device_status = self.device_statuses[2]

    def test_str(self):
        assert str(self.device) == self.device.name

    def test_resource_url(self):
        assert str(self.device.id) in self.device.resource_url

    def test_full_config(self):
        assert self.device.full_config == {
            **self.device.config,
            **{'pins': [self.device_pin.config]},
        }

    def test_last_status(self):
        assert self.device.last_status.pk == self.device_status.pk
        assert self.device.last_status == self.device_statuses[2]

    def test_aggregate_statuses(self):
        assert self.device.aggregate_statuses == {
            'dht-sensor': {
                'humidity': {'minimum': 10, 'maximum': 20, 'average': 14.0},
                'temperature': {'minimum': 10, 'maximum': 20, 'average': 14.0},
            },
            'light-sensor': {'minimum': 10, 'maximum': 20, 'average': 14.0},
        }

    def test_mqtt_toggle(self, mocker):
        mock_mqtt_toggle = mocker.patch('iotserver.apps.device.models.mqtt.toggle')
        mock_mqtt_toggle.return_value = None
        self.device.mqtt_toggle('on')
        mock_mqtt_toggle.assert_called_once_with(self.device.id, '1')

    def test_handle_device_default_config(self, settings, mocker):
        settings.AUTO_SYNC_DEVICE = True
        self.device.managed_firmware = True
        self.device.active = True
        self.device.config = None

        mock_web_socket = mocker.Mock()
        mock_get_websocket = mocker.patch(
            'iotserver.apps.device.models.webrepl.get_websocket',
            return_value=(mocker.Mock(), mock_web_socket),
        )

        def fake_get_file(web_socket, path, remote_path):
            with open(path, 'w') as input_file:
                input_file.write(json.dumps({'main': {}, 'pins': []}))

        mocker.patch(
            'iotserver.apps.device.models.webrepl.get_file', side_effect=fake_get_file
        )

        models.handle_device_default_config(sender=models.Device, instance=self.device)

        mock_get_websocket.assert_called_once_with(
            self.device.ip_address, settings.WEBREPL_PORT, settings.WEBREPL_PASSWORD
        )
        assert self.device.config == {'main': {'identifier': str(self.device.id)}}

    def test_handle_device_default_config_unreachable(self, settings, mocker):
        settings.AUTO_SYNC_DEVICE = True
        self.device.managed_firmware = True
        self.device.active = True
        self.device.config = None

        mocker.patch(
            'iotserver.apps.device.models.webrepl.get_websocket',
            side_effect=OSError,
        )

        with pytest.raises(DeviceUnreachableError):
            models.handle_device_default_config(
                sender=models.Device, instance=self.device
            )

    def test_handle_device_default_config_unmanaged(self, settings):
        settings.AUTO_SYNC_DEVICE = True
        self.device.managed_firmware = False
        self.device.config = None

        models.handle_device_default_config(sender=models.Device, instance=self.device)

        expected_config = json.loads(
            json.dumps(settings.DEVICE_DEFAULT_CONFIG).replace(
                '{identifier}', str(self.device.id)
            )
        )
        assert self.device.config == expected_config

    def test_handle_device_config_update(self, settings, mocker):
        settings.AUTO_SYNC_DEVICE = True
        self.device.managed_firmware = True
        self.device.config = {'main': {}}

        mock_web_socket = mocker.Mock()
        mock_get_websocket = mocker.patch(
            'iotserver.apps.device.models.webrepl.get_websocket',
            return_value=(mocker.Mock(), mock_web_socket),
        )
        mock_put_file = mocker.patch('iotserver.apps.device.models.webrepl.put_file')

        models.handle_device_config_update(sender=models.Device, instance=self.device)

        mock_get_websocket.assert_called_once_with(
            self.device.ip_address, settings.WEBREPL_PORT, settings.WEBREPL_PASSWORD
        )
        mock_put_file.assert_called_once_with(
            mock_web_socket,
            f'/tmp/config.{self.device.id}.json',
            'config/config.json',
        )

    def test_handle_device_config_update_unreachable(self, settings, mocker):
        settings.AUTO_SYNC_DEVICE = True
        self.device.managed_firmware = True
        self.device.config = {'main': {}}

        mocker.patch(
            'iotserver.apps.device.models.webrepl.get_websocket',
            side_effect=OSError,
        )

        with pytest.raises(DeviceUnreachableError):
            models.handle_device_config_update(
                sender=models.Device, instance=self.device
            )


@pytest.mark.django_db
class TestDevicePinModel(object):
    def setup_method(self, test_method):
        self.device_pin = device_factories.DevicePinFactory()

    def test_str(self):
        assert str(self.device_pin) == self.device_pin.name

    def test_resource_url(self):
        assert str(self.device_pin.id) in self.device_pin.resource_url

    def test_config(self):
        assert self.device_pin.config == {
            'pin_number': self.device_pin.pin_number,
            'name': self.device_pin.name,
            'identifier': self.device_pin.identifier,
            'interval': self.device_pin.interval,
            'analog': self.device_pin.analog,
            'read': self.device_pin.read,
            'i2c': self.device_pin.i2c,
            'rule': self.device_pin.rule,
        }


@pytest.mark.django_db
class TestDeviceStatusModel(object):
    def setup_method(self, test_method):
        self.device_status = device_factories.DeviceStatusFactory()

    def test_str(self):
        assert str(self.device_status) == self.device_status.device.name

    def test_resource_url(self):
        assert str(self.device_status.id) in self.device_status.resource_url


@pytest.mark.django_db
class TestDeviceHealthModel(object):
    def setup_method(self, test_method):
        self.device_health = device_factories.DeviceHealthFactory()

    def test_str(self):
        assert str(self.device_health) == self.device_health.device.name

    def test_resource_url(self):
        assert str(self.device_health.id) in self.device_health.resource_url

    def test_status(self):
        assert self.device_health.status
