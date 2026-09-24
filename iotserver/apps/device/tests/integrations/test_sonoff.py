import base64
import hashlib
import hmac
import json
from datetime import timedelta

import pytest
from django.utils import timezone

from iotserver.apps.device.integrations.sonoff import Sonoff, SonoffNotAuthorizedError
from iotserver.apps.device.models import SonoffToken


@pytest.fixture(autouse=True)
def mock_settings(mocker):
    mock = mocker.patch('iotserver.apps.device.integrations.sonoff.settings')
    mock.INTEGRATIONS = {
        'sonoff': {
            'app_id': 'app-id',
            'app_secret': 'app-secret',
            'region': 'eu',
            'redirect_url': 'https://example.com/callback/',
            'authorize_url': 'https://example.com/authorize',
            'token_url': 'https://example.com/v2/user/oauth/token',
            'refresh_url': 'https://example.com/v2/user/refresh',
            'device_url': 'https://example.com/v2/device/thing/status',
        }
    }
    return mock


@pytest.fixture
def sonoff():
    return Sonoff(device_id='device-id')


@pytest.fixture
def mock_requests(mocker):
    response = mocker.Mock()
    response.json.return_value = {'error': 0, 'msg': '', 'data': {}}

    mock = mocker.patch('iotserver.apps.device.integrations.sonoff.requests')
    mock.post.return_value = response
    mock.response = response
    return mock


@pytest.mark.django_db
class TestSonoffIntegration(object):
    def test_sign_request(self, sonoff):
        data = {'deviceid': 'device-id', 'params': {'switch': 'on'}}
        expected = base64.b64encode(
            hmac.new(
                b'app-secret', json.dumps(data).encode('utf-8'), hashlib.sha256
            ).digest()
        ).decode()

        assert sonoff._sign_request(data) == expected

    def test_generate_nonce(self, sonoff, mocker):
        choice = mocker.patch(
            'iotserver.apps.device.integrations.sonoff.random.choice',
            side_effect='AbCdEfGh',
        )

        assert sonoff._generate_nonce() == 'AbCdEfGh'
        assert choice.call_count == 8

    def test_authorize_url(self, sonoff, mocker):
        mocker.patch.object(sonoff, '_generate_nonce', return_value='nonce123')
        mocker.patch(
            'iotserver.apps.device.integrations.sonoff.timezone.now',
            return_value=timezone.datetime(
                2024, 1, 1, tzinfo=timezone.get_current_timezone()
            ),
        )

        url = sonoff.authorize_url('state-123')

        assert url.startswith('https://example.com/authorize?')
        assert 'clientId=app-id' in url
        assert 'state=state-123' in url
        assert 'redirectUrl=' in url

    def test_exchange_code(self, sonoff, mock_requests, mocker):
        mocker.patch.object(sonoff, '_generate_nonce', return_value='nonce123')
        sign_request = mocker.patch.object(
            sonoff, '_sign_request', return_value='signed'
        )
        mock_requests.response.json.return_value = {
            'error': 0,
            'msg': '',
            'data': {
                'accessToken': 'access-token',
                'atExpiredTime': 1704110400000,
                'refreshToken': 'refresh-token',
                'rtExpiredTime': 1706788800000,
            },
        }

        sonoff.exchange_code('auth-code')

        expected_data = {
            'code': 'auth-code',
            'redirectUrl': 'https://example.com/callback/',
            'grantType': 'authorization_code',
        }
        sign_request.assert_called_once_with(expected_data)
        mock_requests.post.assert_called_once_with(
            url='https://example.com/v2/user/oauth/token',
            json=expected_data,
            headers={
                'X-CK-Appid': 'app-id',
                'X-CK-Nonce': 'nonce123',
                'Authorization': 'Sign signed',
                'Content-Type': 'application/json',
            },
        )
        token = SonoffToken.objects.get()
        assert token.access_token == 'access-token'
        assert token.refresh_token == 'refresh-token'
        assert token.region == 'eu'

    def test_exchange_code_error_response_is_raised(self, sonoff, mock_requests):
        mock_requests.response.json.return_value = {
            'error': 10001,
            'msg': 'invalid code',
            'data': {},
        }

        with pytest.raises(RuntimeError, match='invalid code'):
            sonoff.exchange_code('auth-code')

    def test_toggle_device_not_authorized(self, sonoff):
        with pytest.raises(SonoffNotAuthorizedError):
            sonoff.toggle_device('on')

    @pytest.mark.parametrize('state', ['on', 'off'])
    def test_toggle_device(self, sonoff, mock_requests, mocker, state):
        SonoffToken.objects.create(
            access_token='access-token',
            refresh_token='refresh-token',
            access_token_expires_at=timezone.now() + timedelta(days=1),
            refresh_token_expires_at=timezone.now() + timedelta(days=30),
            region='eu',
        )
        mocker.patch.object(sonoff, '_generate_nonce', return_value='nonce123')

        assert sonoff.toggle_device(state) == state
        mock_requests.post.assert_called_once_with(
            url='https://example.com/v2/device/thing/status',
            json={
                'type': 1,
                'id': 'device-id',
                'params': {'switch': state},
            },
            headers={
                'X-CK-Appid': 'app-id',
                'X-CK-Nonce': 'nonce123',
                'Authorization': 'Bearer access-token',
                'Content-Type': 'application/json',
            },
        )
        mock_requests.response.raise_for_status.assert_called_once_with()

    def test_toggle_device_refreshes_expired_token(self, sonoff, mock_requests, mocker):
        SonoffToken.objects.create(
            access_token='old-access-token',
            refresh_token='old-refresh-token',
            access_token_expires_at=timezone.now() - timedelta(minutes=1),
            refresh_token_expires_at=timezone.now() + timedelta(days=30),
            region='eu',
        )
        mocker.patch.object(sonoff, '_generate_nonce', return_value='nonce123')
        mocker.patch.object(sonoff, '_sign_request', return_value='signed')

        refresh_response = mocker.Mock()
        refresh_response.json.return_value = {
            'error': 0,
            'msg': '',
            'data': {'at': 'new-access-token', 'rt': 'new-refresh-token'},
        }
        device_response = mocker.Mock()
        device_response.json.return_value = {'error': 0, 'msg': '', 'data': {}}
        mock_requests.post.side_effect = [refresh_response, device_response]

        assert sonoff.toggle_device('on') == 'on'

        token = SonoffToken.objects.get()
        assert token.access_token == 'new-access-token'
        assert token.refresh_token == 'new-refresh-token'

        device_call = mock_requests.post.call_args_list[1]
        assert (
            device_call.kwargs['headers']['Authorization'] == 'Bearer new-access-token'
        )

    def test_toggle_http_error_is_propagated(self, sonoff, mock_requests):
        SonoffToken.objects.create(
            access_token='access-token',
            refresh_token='refresh-token',
            access_token_expires_at=timezone.now() + timedelta(days=1),
            refresh_token_expires_at=timezone.now() + timedelta(days=30),
            region='eu',
        )
        mock_requests.response.raise_for_status.side_effect = RuntimeError(
            'toggle failed'
        )

        with pytest.raises(RuntimeError, match='toggle failed'):
            sonoff.toggle_device('on')

    def test_toggle_error_response_is_raised(self, sonoff, mock_requests):
        SonoffToken.objects.create(
            access_token='access-token',
            refresh_token='refresh-token',
            access_token_expires_at=timezone.now() + timedelta(days=1),
            refresh_token_expires_at=timezone.now() + timedelta(days=30),
            region='eu',
        )
        mock_requests.response.json.return_value = {
            'error': 30022,
            'msg': 'device is offline',
            'data': {},
        }

        with pytest.raises(RuntimeError, match='device is offline'):
            sonoff.toggle_device('on')
