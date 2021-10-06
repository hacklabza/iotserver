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

    def test_str(self):
        assert str(self.device) == self.device.name

    def test_resource_url(self):
        assert str(self.device.id) in self.device.resource_url


@pytest.mark.django_db
class TestDevicePinModel(object):
    def setup_method(self, test_method):
        self.device_pin = device_factories.DevicePinFactory()

    def test_str(self):
        assert str(self.device_pin) == self.device_pin.name

    def test_resource_url(self):
        assert str(self.device_pin.id) in self.device_pin.resource_url


@pytest.mark.django_db
class TestDeviceStatusModel(object):
    def setup_method(self, test_method):
        self.device_status = device_factories.DeviceStatusFactory()

    def test_str(self):
        assert str(self.device_status) == self.device_status.device.name

    def test_resource_url(self):
        assert str(self.device_status.id) in self.device_status.resource_url
