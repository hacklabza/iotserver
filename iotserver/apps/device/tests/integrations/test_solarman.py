import hashlib

import pytest

from iotserver.apps.device.integrations.solarman import Solarman


@pytest.fixture(autouse=True)
def mock_settings(mocker):
    mock = mocker.patch('iotserver.apps.device.integrations.solarman.settings')
    mock.INTEGRATIONS = {
        'solarman': {
            'base_url': 'https://example.com',
            'email': 'user@example.com',
            'password': 'password',
            'app_id': 'app-id',
            'app_secret': 'app-secret',
            'cache_timeout': 300,
        }
    }
    return mock


@pytest.fixture(autouse=True)
def mock_cache(mocker):
    """Mock Django cache to return None (cache miss)"""
    mock = mocker.patch('iotserver.apps.device.integrations.solarman.cache')
    mock.get.return_value = None
    return mock


@pytest.fixture
def solarman():
    return Solarman(station_id=3208097)


@pytest.fixture
def mock_requests(mocker):
    auth_response = mocker.Mock()
    auth_response.json.return_value = {'access_token': 'access-token'}
    real_time_response = mocker.Mock()

    mock = mocker.patch('iotserver.apps.device.integrations.solarman.requests')
    mock.post.side_effect = [auth_response, real_time_response]
    mock.auth_response = auth_response
    mock.real_time_response = real_time_response
    return mock


class TestSolarmanIntegration(object):
    def test_hash_password(self, solarman):
        assert (
            solarman._hash_password() == hashlib.sha256(b'password').hexdigest()
        )

    def test_authenticate(self, solarman, mock_requests):
        assert solarman._authenticate() == 'access-token'
        mock_requests.post.assert_called_once_with(
            url='https://example.com/account/v1.0/token?appId=app-id&language=en',
            json={
                'appSecret': 'app-secret',
                'email': 'user@example.com',
                'password': hashlib.sha256(b'password').hexdigest(),
            },
        )
        mock_requests.auth_response.raise_for_status.assert_called_once_with()

    def test_authentication_http_error_is_propagated(
        self, solarman, mock_requests
    ):
        mock_requests.auth_response.raise_for_status.side_effect = RuntimeError(
            'authentication failed'
        )

        with pytest.raises(RuntimeError, match='authentication failed'):
            solarman._authenticate()

    def test_missing_access_token_is_propagated(self, solarman, mock_requests):
        mock_requests.auth_response.json.return_value = {}

        with pytest.raises(KeyError, match='access_token'):
            solarman._authenticate()

    def test_real_time(self, solarman, mock_requests, mocker):
        authenticate = mocker.patch.object(
            solarman, '_authenticate', return_value='access-token'
        )
        mock_requests.post.side_effect = None
        mock_requests.post.return_value = mock_requests.real_time_response
        mock_requests.real_time_response.json.return_value = {
            'generationPower': 1200.0,
            'batterySoc': 71.0,
            'usePower': 932.0,
        }

        assert solarman.real_time == {
            'solar_input': 1200.0,
            'battery_soc': 71.0,
            'current_consumption': 932.0,
        }
        authenticate.assert_called_once_with()
        mock_requests.post.assert_called_once_with(
            url='https://example.com/station/v1.0/realTime',
            json={'stationId': 3208097},
            headers={'Authorization': 'Bearer access-token'},
        )
        mock_requests.real_time_response.raise_for_status.assert_called_once_with()

    def test_real_time_http_error_is_propagated(
        self, solarman, mock_requests, mocker
    ):
        mocker.patch.object(
            solarman, '_authenticate', return_value='access-token'
        )
        mock_requests.post.side_effect = None
        mock_requests.post.return_value = mock_requests.real_time_response
        mock_requests.real_time_response.raise_for_status.side_effect = (
            RuntimeError('real time fetch failed')
        )

        with pytest.raises(RuntimeError, match='real time fetch failed'):
            _ = solarman.real_time

    def test_real_time_is_cached(
        self, solarman, mock_requests, mock_cache, mocker
    ):
        mocker.patch.object(
            solarman, '_authenticate', return_value='access-token'
        )
        mock_requests.post.side_effect = None
        mock_requests.post.return_value = mock_requests.real_time_response
        mock_requests.real_time_response.json.return_value = {
            'generationPower': 1200.0,
            'batterySoc': 71.0,
            'usePower': 932.0,
        }
        expected = {
            'solar_input': 1200.0,
            'battery_soc': 71.0,
            'current_consumption': 932.0,
        }

        assert solarman.real_time == expected

        cache_key = f'{solarman.cache_prefix}.real_time:3208097'
        assert solarman.cache_prefix == (
            'iotserver.apps.device.integrations.solarman.Solarman'
        )
        mock_cache.get.assert_called_once_with(cache_key)
        mock_cache.set.assert_called_once_with(cache_key, expected, timeout=300)

    def test_real_time_custom_cache_timeout(
        self, mock_requests, mock_cache, mocker
    ):
        solarman = Solarman(station_id=3208097, cache_timeout=30)
        mocker.patch.object(
            solarman, '_authenticate', return_value='access-token'
        )
        mock_requests.post.side_effect = None
        mock_requests.post.return_value = mock_requests.real_time_response
        mock_requests.real_time_response.json.return_value = {
            'generationPower': 1200.0,
            'batterySoc': 71.0,
            'usePower': 932.0,
        }

        _ = solarman.real_time

        assert mock_cache.set.call_args.kwargs['timeout'] == 30

    def test_real_time_cache_hit(
        self, solarman, mock_requests, mock_cache, mocker
    ):
        authenticate = mocker.patch.object(solarman, '_authenticate')
        cached = {
            'solar_input': 1.0,
            'battery_soc': 2.0,
            'current_consumption': 3.0,
        }
        mock_cache.get.return_value = cached

        assert solarman.real_time == cached
        authenticate.assert_not_called()
        mock_requests.post.assert_not_called()
        mock_cache.set.assert_not_called()

    def test_real_time_http_error_is_not_cached(
        self, solarman, mock_requests, mock_cache, mocker
    ):
        mocker.patch.object(
            solarman, '_authenticate', return_value='access-token'
        )
        mock_requests.post.side_effect = None
        mock_requests.post.return_value = mock_requests.real_time_response
        mock_requests.real_time_response.raise_for_status.side_effect = (
            RuntimeError
        )

        with pytest.raises(RuntimeError):
            _ = solarman.real_time
        mock_cache.set.assert_not_called()
