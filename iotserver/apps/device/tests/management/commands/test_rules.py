import pytest
from django.core.management import call_command

from iotserver.apps.device.tests import factories as device_factories


@pytest.mark.django_db
class TestRulesCommand:
    def test_spawns_one_thread_per_active_non_managed_device(self, mocker):
        matching_device = device_factories.DeviceFactory(
            managed_firmware=False,
            active=True,
            ip_address='192.168.0.1',
            mac_address='0E:00:20:01:71:AE',
        )
        device_factories.DeviceFactory(
            managed_firmware=True,
            active=True,
            ip_address='192.168.0.2',
            mac_address='0E:00:20:01:71:AF',
        )
        device_factories.DeviceFactory(
            managed_firmware=False,
            active=False,
            ip_address='192.168.0.3',
            mac_address='0E:00:20:01:71:B0',
        )

        mock_thread_cls = mocker.patch('threading.Thread')

        call_command('rules')

        assert mock_thread_cls.call_count == 1
        _, kwargs = mock_thread_cls.call_args
        assert kwargs['args'][0] == matching_device
        assert kwargs['daemon'] is True
        mock_thread_cls.return_value.start.assert_called_once()
        mock_thread_cls.return_value.join.assert_called_once()

    def test_exits_without_spawning_when_no_devices_match(self, mocker):
        device_factories.DeviceFactory(managed_firmware=True, active=True)

        mock_thread_cls = mocker.patch('threading.Thread')

        call_command('rules')

        mock_thread_cls.assert_not_called()
