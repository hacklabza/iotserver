import signal
import threading

from django.core.management.base import BaseCommand

from iotserver.apps.device.models import Device
from iotserver.apps.device.utils import rules


class Command(BaseCommand):
    help = 'Run the rules engine for non-managed-firmware devices.'

    def handle(self, *args, **options):
        """
        Spawn one worker thread per active, non-managed-firmware device and run
        until interrupted.
        """
        stop_event = threading.Event()

        devices = Device.objects.filter(managed_firmware=False, active=True)
        threads = [
            threading.Thread(
                target=rules.run_device, args=(device, stop_event), daemon=True
            )
            for device in devices
        ]

        if not threads:
            self.stdout.write(
                self.style.WARNING('No active non-managed-firmware devices found.')
            )
            return

        def handle_shutdown(signum, frame):
            self.stdout.write(self.style.WARNING('Shutting down rules engine...'))
            stop_event.set()

        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)

        for thread in threads:
            thread.start()

        self.stdout.write(
            self.style.SUCCESS(f'Rules engine started for {len(threads)} device(s).')
        )

        for thread in threads:
            thread.join()

        self.stdout.write(self.style.SUCCESS('Rules engine stopped.'))
