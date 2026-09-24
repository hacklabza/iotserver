import signal
import threading

from django.core.management.base import BaseCommand

from iotserver.apps.device.models import Device
from iotserver.apps.device.utils import rules

# Seconds between checks for newly added/removed active non-managed-firmware devices.
DEVICE_POLL_INTERVAL = 30


class Command(BaseCommand):
    help = 'Run the rules engine for non-managed-firmware devices.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--poll-interval',
            type=int,
            default=DEVICE_POLL_INTERVAL,
            help='Seconds between checks for added/removed devices.',
        )

    def handle(self, *args, **options):
        """
        Continuously reconciles worker threads against active, non-managed-
        firmware devices, so devices added/removed/(de)activated while running
        are picked up without a restart, until interrupted.
        """
        self.shutdown_event = threading.Event()

        def handle_shutdown(signum, frame):
            self.stdout.write(self.style.WARNING('Shutting down rules engine...'))
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)

        workers = {}
        while not self.shutdown_event.is_set():
            self._reconcile_workers(workers)
            self.shutdown_event.wait(options['poll_interval'])

        for stop_event, _thread in workers.values():
            stop_event.set()
        for _stop_event, thread in workers.values():
            thread.join()

        self.stdout.write(self.style.SUCCESS('Rules engine stopped.'))

    def _reconcile_workers(self, workers):
        """
        Starts workers for newly active non-managed-firmware devices and stops
        workers for devices which no longer match, mutating `workers` in place
        (keyed by device id, valued by (stop_event, thread)).
        """
        current_device_ids = set()

        for device in Device.objects.filter(managed_firmware=False, active=True):
            current_device_ids.add(device.id)
            if device.id not in workers:
                stop_event = threading.Event()
                thread = threading.Thread(
                    target=rules.run_device, args=(device, stop_event), daemon=True
                )
                thread.start()
                workers[device.id] = (stop_event, thread)
                self.stdout.write(
                    self.style.SUCCESS(f'Started worker for device {device.id}.')
                )

        for device_id in [key for key in workers if key not in current_device_ids]:
            stop_event, thread = workers.pop(device_id)
            stop_event.set()
            thread.join()
            self.stdout.write(
                self.style.WARNING(f'Stopped worker for device {device_id}.')
            )
