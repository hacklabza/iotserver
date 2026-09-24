import pytest

from iotserver.apps.device.management.commands.rules import Command
from iotserver.apps.device.tests import factories as device_factories


@pytest.mark.django_db
class TestReconcileWorkers:
    def test_starts_worker_for_new_active_device(self, mocker):
        device = device_factories.DeviceFactory(managed_firmware=False, active=True)
        mock_thread_cls = mocker.patch('threading.Thread')
        command = Command()
        workers = {}

        command._reconcile_workers(workers)

        assert device.id in workers
        mock_thread_cls.assert_called_once()
        _, kwargs = mock_thread_cls.call_args
        assert kwargs['args'][0] == device
        assert kwargs['daemon'] is True
        mock_thread_cls.return_value.start.assert_called_once()

    def test_ignores_managed_or_inactive_devices(self, mocker):
        device_factories.DeviceFactory(managed_firmware=True, active=True)
        device_factories.DeviceFactory(
            managed_firmware=False,
            active=False,
            ip_address='192.168.0.2',
            mac_address='0E:00:20:01:71:AF',
        )
        mock_thread_cls = mocker.patch('threading.Thread')
        command = Command()

        command._reconcile_workers({})

        mock_thread_cls.assert_not_called()

    def test_does_not_restart_an_already_running_device(self, mocker):
        device_factories.DeviceFactory(managed_firmware=False, active=True)
        mock_thread_cls = mocker.patch('threading.Thread')
        command = Command()
        workers = {}
        command._reconcile_workers(workers)
        mock_thread_cls.reset_mock()

        command._reconcile_workers(workers)

        mock_thread_cls.assert_not_called()

    def test_stops_worker_for_device_no_longer_matching(self, mocker):
        device = device_factories.DeviceFactory(managed_firmware=False, active=True)
        mocker.patch('threading.Thread')
        command = Command()
        workers = {}
        command._reconcile_workers(workers)
        stop_event, thread = workers[device.id]

        device.active = False
        device.save()
        command._reconcile_workers(workers)

        assert device.id not in workers
        assert stop_event.is_set()
        thread.join.assert_called_once()


class TestHandle:
    def test_polls_until_shutdown_event_is_set(self, mocker):
        command = Command()

        def stop_after_first_call(workers):
            command.shutdown_event.set()

        mock_reconcile = mocker.patch.object(
            command, '_reconcile_workers', side_effect=stop_after_first_call
        )

        command.handle(poll_interval=0)

        mock_reconcile.assert_called_once()
