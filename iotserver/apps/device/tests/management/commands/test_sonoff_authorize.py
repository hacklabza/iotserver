import pytest
from django.core.management import call_command

from iotserver.apps.device.integrations.sonoff import Sonoff


@pytest.mark.django_db
class TestSonoffAuthorizeCommand(object):
    def test_prints_authorize_url_without_code(self, mocker, capsys):
        mocker.patch.object(
            Sonoff, 'authorize_url', return_value='https://example.com/authorize'
        )

        call_command('sonoff_authorize')

        assert 'https://example.com/authorize' in capsys.readouterr().out

    def test_exchanges_code_when_provided(self, mocker, capsys):
        exchange_code = mocker.patch.object(Sonoff, 'exchange_code')

        call_command('sonoff_authorize', '--code', 'auth-code')

        exchange_code.assert_called_once_with('auth-code')
        assert 'connected successfully' in capsys.readouterr().out
