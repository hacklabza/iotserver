import base64
import hashlib
import hmac
import json

import pytest

from iotserver.apps.device.integrations.sonoff import Sonoff


@pytest.fixture(autouse=True)
def mock_settings(mocker):
    mock = mocker.patch('iotserver.apps.device.integrations.sonoff.settings')
    mock.INTEGRATIONS = {
        'sonoff': {
            'auth_url': 'https://example.com/auth',
            'email': 'user@example.com',
            'password': 'password',
            'country_code': '+27',
            'app_id': 'app-id',
            'app_secret': 'app-secret',
            'device_url': 'https://example.com/device',
        }
    }
    return mock


@pytest.fixture
def sonoff():
    return Sonoff(device_id='device-id')


@pytest.fixture
def mock_requests(mocker):
    auth_response = mocker.Mock()
    auth_response.json.return_value = {'at': 'access-token'}
    device_response = mocker.Mock()

    mock = mocker.patch('iotserver.apps.device.integrations.sonoff.requests')
    mock.post.side_effect = [auth_response, device_response]
    mock.auth_response = auth_response
    mock.device_response = device_response
    return mock


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

    def test_authenticate(self, sonoff, mock_requests, mocker):
        mocker.patch.object(sonoff, '_generate_nonce', return_value='nonce123')
        sign_request = mocker.patch.object(
            sonoff, '_sign_request', return_value='signed'
        )
        mocker.patch(
            'iotserver.apps.device.integrations.sonoff.time.time', return_value=123.4
        )

        assert sonoff._authenticate() == 'access-token'
        expected_data = {
            'appid': 'app-id',
            'countryCode': '+27',
            'email': 'user@example.com',
            'password': 'password',
            'ts': 123.4,
            'version': 8,
            'nonce': 'nonce123',
        }
        sign_request.assert_called_once_with(expected_data)
        mock_requests.post.assert_called_once_with(
            url='https://example.com/auth',
            json=expected_data,
            headers={'Authorization': 'Sign signed'},
        )
        mock_requests.auth_response.raise_for_status.assert_called_once_with()

    def test_authentication_http_error_is_propagated(
        self, sonoff, mock_requests, mocker
    ):
        mocker.patch.object(sonoff, '_generate_nonce', return_value='nonce123')
        mock_requests.auth_response.raise_for_status.side_effect = RuntimeError(
            'authentication failed'
        )

        with pytest.raises(RuntimeError, match='authentication failed'):
            sonoff._authenticate()

    def test_missing_access_token_is_propagated(self, sonoff, mock_requests, mocker):
        mocker.patch.object(sonoff, '_generate_nonce', return_value='nonce123')
        mock_requests.auth_response.json.return_value = {}

        with pytest.raises(KeyError, match='at'):
            sonoff._authenticate()

    @pytest.mark.parametrize('state', ['on', 'off'])
    def test_toggle_device(self, sonoff, mock_requests, mocker, state):
        authenticate = mocker.patch.object(
            sonoff, '_authenticate', return_value='access-token'
        )
        sonoff.nonce = 'nonce123'
        mocker.patch(
            'iotserver.apps.device.integrations.sonoff.time.time', return_value=456.7
        )
        mock_requests.post.side_effect = None
        mock_requests.post.return_value = mock_requests.device_response

        assert sonoff.toggle_device(state) == state
        authenticate.assert_called_once_with()
        mock_requests.post.assert_called_once_with(
            url='https://example.com/device',
            json={
                'deviceid': 'device-id',
                'params': {'switch': state},
                'appid': 'app-id',
                'ts': 456.7,
                'version': 8,
                'nonce': 'nonce123',
            },
            headers={'Authorization': 'Bearer access-token'},
        )
        mock_requests.device_response.raise_for_status.assert_called_once_with()

    def test_toggle_http_error_is_propagated(self, sonoff, mock_requests, mocker):
        mocker.patch.object(sonoff, '_authenticate', return_value='access-token')
        mock_requests.post.side_effect = None
        mock_requests.post.return_value = mock_requests.device_response
        mock_requests.device_response.raise_for_status.side_effect = RuntimeError(
            'toggle failed'
        )

        with pytest.raises(RuntimeError, match='toggle failed'):
            sonoff.toggle_device('on')
