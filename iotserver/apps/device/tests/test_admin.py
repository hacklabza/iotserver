import pytest
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from iotserver.apps.device.admin import DeviceModelAdmin
from iotserver.apps.device.exceptions import DeviceUnreachableError
from iotserver.apps.device.models import Device
from iotserver.apps.device.tests import factories as device_factories


@pytest.mark.django_db
class TestDeviceModelAdmin(object):
    def setup_method(self, test_method):
        self.device = device_factories.DeviceFactory()
        self.request = RequestFactory().post('/')
        self.request.session = {}
        self.request._messages = FallbackStorage(self.request)
        self.admin = DeviceModelAdmin(Device, None)

    def test_save_model_success(self, mocker):
        mock_save_model = mocker.patch('django.contrib.admin.ModelAdmin.save_model')

        self.admin.save_model(self.request, self.device, form=None, change=True)

        mock_save_model.assert_called_once_with(self.request, self.device, None, True)
        assert list(messages.get_messages(self.request)) == []

    def test_save_model_device_unreachable(self, mocker):
        mocker.patch(
            'django.contrib.admin.ModelAdmin.save_model',
            side_effect=DeviceUnreachableError('Device is unreachable.'),
        )

        self.admin.save_model(self.request, self.device, form=None, change=True)

        stored_messages = list(messages.get_messages(self.request))
        assert len(stored_messages) == 1
        assert stored_messages[0].level == messages.WARNING
        assert str(stored_messages[0]) == 'Device is unreachable.'
