import pytest

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
        self.device_status = device_factories.DeviceStatusFactory(device=self.device)

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

    def test_mqtt_toggle(self, mocker):
        mock_mqtt_toggle = mocker.patch('iotserver.apps.device.models.mqtt.toggle')
        mock_mqtt_toggle.return_value = None
        self.device.mqtt_toggle('on')
        mock_mqtt_toggle.assert_called_once_with(self.device.id, '1')


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
