import uuid

from django.core.management.base import BaseCommand

from iotserver.apps.device.integrations.sonoff import Sonoff


class Command(BaseCommand):
    help = (
        'Connect the Sonoff/eWeLink integration. Run with no arguments to print '
        'an authorization URL, open it in a browser and log in, then re-run '
        "with --code using the 'code' query parameter from the redirect URL."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--code',
            help="Authorization code from the redirect URL's 'code' parameter.",
        )

    def handle(self, *args, **options):
        code = options.get('code')

        if not code:
            url = Sonoff().authorize_url(uuid.uuid4().hex)
            self.stdout.write(
                'Open this URL in a browser and log in, then re-run this '
                "command with --code <code> using the redirect URL's 'code' "
                'parameter:\n'
            )
            self.stdout.write(url)
            return

        Sonoff().exchange_code(code)
        self.stdout.write(self.style.SUCCESS('Sonoff account connected successfully.'))
