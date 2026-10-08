import hashlib

import pytest
import requests

from iotserver.apps.device.integrations.rainpoint import RainPoint


@pytest.fixture
def client(mocker):
    settings = mocker.patch(
        'iotserver.apps.device.integrations.rainpoint.settings'
    )
    settings.INTEGRATIONS = {
        'rainpoint': {
            'base_url': 'https://example.com',
            'app_code': '2',
            'email': 'api@example.com',
            'password': 'password',
            'area_code': '27',
            'hub_id': '361481',
            'cache_timeout': 60,
        }
    }
    return RainPoint('361481')


@pytest.fixture
def mock_cache(mocker):
    cache = mocker.patch('iotserver.apps.device.integrations.rainpoint.cache')
    cache.get.return_value = None
    return cache


@pytest.fixture
def mock_request(mocker):
    mock = mocker.patch('iotserver.apps.device.integrations.rainpoint.requests')
    mock.post.return_value.json.return_value = {
        'code': 0,
        'data': {'token': 'token', 'tokenExpired': 3600},
    }
    mock.get.return_value.json.return_value = {
        'code': 0,
        'data': {'subDeviceStatus': []},
    }
    return mock


@pytest.mark.parametrize('custom_mapping', [False, True])
def test_statuses_uses_reading_map(mocker, mock_cache, custom_mapping):
    settings = mocker.patch(
        'iotserver.apps.device.integrations.rainpoint.settings'
    )
    settings.INTEGRATIONS = {
        'rainpoint': {
            'base_url': 'https://example.com',
            'app_code': '2',
            'cache_timeout': 60,
        }
    }
    rainpoint = RainPoint('361481')
    mocker.patch.object(rainpoint, '_authenticate', return_value='token')
    request = mocker.patch(
        'iotserver.apps.device.integrations.rainpoint.requests.get'
    )
    if custom_mapping:
        mocker.patch(
            'iotserver.apps.device.integrations.rainpoint.READING_MAP',
            {
                'custom_sensor': {
                    'address': 7,
                    'model_code': 262,
                    'fields': {'humidity_pct': 'custom_humidity'},
                }
            },
        )
    request.return_value.json.return_value = {
        'data': {
            'subDeviceStatus': [
                {'id': 'D01', 'value': '10#FD040F00'},
                {'id': 'D02', 'value': '10#85B602'},
                {'id': 'D03', 'value': '10#85BA028842'},
                {'id': 'D07', 'value': '10#85BA028827'},
            ]
        }
    }
    expected = (
        {'custom_humidity': 39}
        if custom_mapping
        else {
            'rainfall': 1.5,
            'pool_temperature': 20.8,
            'temperature': 21.0,
            'humidity': 66,
        }
    )

    assert rainpoint.statuses == expected
    request.assert_called_once_with(
        url='https://example.com/app/device/getDeviceStatus',
        params={'mid': '361481'},
        headers={'lang': 'en', 'appCode': '2', 'auth': 'token'},
    )
    mock_cache.set.assert_called_once_with(
        f'{rainpoint.cache_prefix}.statuses:361481', expected, timeout=60
    )


def test_statuses(client, mock_cache, mock_request):
    status = {
        'subDeviceStatus': [
            {
                'id': 'D01',
                'time': 1791341339073,
                'value': '10#E10000FD040000FD050000FD060000DC0197DE030000FF0FDB4B8E1A',
            },
            {
                'id': 'D02',
                'time': 1791444145150,
                'value': '10#E7B202B602DC01B80585B602FF0F9895901A',
            },
            {
                'id': 'D03',
                'time': 1791444360142,
                'value': '10#E73A02BA02DC01B80E85BA028842E9425CFF0F7B96901A',
            },
            {'id': 'D04', 'value': None},
            {'id': 'connected', 'value': '1'},
        ],
    }
    mock_request.get.return_value.json.return_value = {
        'code': 0,
        'data': status,
    }

    assert client.statuses == {
        'rainfall': 0.0,
        'pool_temperature': 20.8,
        'temperature': 21.0,
        'humidity': 66,
    }
    mock_request.post.assert_called_once_with(
        url='https://example.com/auth/basic/app/login',
        headers={'lang': 'en', 'appCode': '2'},
        json={
            'areaCode': '27',
            'phoneOrEmail': 'api@example.com',
            'password': hashlib.md5(b'password').hexdigest(),
            'deviceId': mock_request.post.call_args.kwargs['json']['deviceId'],
        },
    )
    mock_request.get.assert_called_once_with(
        url='https://example.com/app/device/getDeviceStatus',
        params={'mid': '361481'},
        headers={'lang': 'en', 'appCode': '2', 'auth': 'token'},
    )
    mock_request.post.return_value.raise_for_status.assert_called_once_with()
    mock_request.get.return_value.raise_for_status.assert_called_once_with()
    assert mock_cache.set.call_args.kwargs['timeout'] == 60


@pytest.mark.parametrize('app_code', ['1', '2'])
def test_configured_app_code(client, mock_cache, mock_request, app_code):
    client.config['app_code'] = app_code
    client = RainPoint('361481')
    client._authenticate()

    assert mock_request.post.call_args.kwargs['headers']['appCode'] == app_code
    assert client.request_headers == {'lang': 'en', 'appCode': app_code}


def test_cached_statuses(client, mock_cache, mock_request):
    statuses = {'rainfall': 0.0, 'temperature': 21.0}
    mock_cache.get.return_value = statuses
    assert client.statuses == statuses
    mock_cache.get.assert_called_once_with(
        f'{client.cache_prefix}.statuses:361481'
    )
    mock_request.get.assert_not_called()
    mock_request.post.assert_not_called()


def test_cached_authentication_token(client, mock_cache, mock_request):
    mock_cache.get.return_value = 'old-token'
    assert client._authenticate() == 'old-token'
    mock_request.post.assert_not_called()


def test_authentication_token_cache_lifetime(client, mock_cache, mock_request):
    mock_request.post.return_value.json.return_value = {
        'code': 0,
        'data': {'token': 'new', 'tokenExpired': 3600},
    }
    assert client._authenticate() == 'new'
    mock_cache.set.assert_called_once_with(
        f'{client.cache_prefix}.auth', 'new', timeout=3600
    )


@pytest.mark.parametrize('method', ['GET', 'POST'])
def test_http_error_not_cached(
    client, mock_cache, mock_request, mocker, method
):
    response = (
        mock_request.get.return_value
        if method == 'GET'
        else mock_request.post.return_value
    )
    response.raise_for_status.side_effect = requests.HTTPError
    if method == 'GET':
        mocker.patch.object(client, '_authenticate', return_value='token')
    with pytest.raises(requests.HTTPError):
        if method == 'GET':
            _ = client.statuses
        else:
            client._authenticate()
    mock_cache.set.assert_not_called()


@pytest.mark.parametrize(
    'model_code, payload, expected',
    [
        (
            87,
            '10#E10000FD040000FD050000FD060000DC0197DE030000FF0FDB4B8E1A',
            {'rainfall_mm_hour': 0.0},
        ),
        (
            262,
            '10#E73A02BA02DC01B80E85BA028842E9425CFF0F7B96901A',
            {
                'temperature_c': 21.0,
                'humidity_pct': 66,
            },
        ),
        (
            268,
            '10#E7B202B602DC01B80585B602FF0F9895901A',
            {'temperature_c': 20.8},
        ),
    ],
)
def test_decode_sensor_sample(client, model_code, payload, expected):
    assert client._decode_sensor(payload, model_code) == expected


@pytest.mark.parametrize('model_code', [87, 262, 268, 999])
def test_decode_sensor_ignores_unused_datapoints(client, model_code):
    assert (
        client._decode_sensor('10#DC01E700000000E9000097DE030000', model_code)
        == {}
    )


@pytest.mark.parametrize('value', [None, '', 'offline'])
def test_decode_sensor_missing(client, value):
    assert client._decode_sensor(value, 262) == {}


@pytest.mark.parametrize('value', ['10#FD', '10#85BA', '10#not-hex'])
def test_decode_sensor_malformed(client, value):
    with pytest.raises(ValueError):
        client._decode_sensor(value, 262)


def test_decode_sensor_signed_temperature(client):
    assert client._decode_sensor('10#85CEFF', 262) == {'temperature_c': -20.6}


def test_decode_sensor_extended_stream(client):
    assert client._decode_sensor('11#0085BA02', 262) == {'temperature_c': 21.0}


def test_custom_cache_timeout(client, mock_cache, mock_request):
    client = RainPoint('361481', cache_timeout=30)
    assert client.statuses == {}
    assert mock_cache.set.call_args.kwargs['timeout'] == 30


@pytest.mark.parametrize('cache_timeout', [None, 0])
def test_default_cache_timeout(client, mock_cache, mock_request, cache_timeout):
    client = RainPoint('361481', cache_timeout=cache_timeout)
    cached_statuses = {'temperature': 21.0}
    mock_cache.get.return_value = cached_statuses

    assert client.cache_timeout == client.config['cache_timeout'] == 60
    assert client.statuses == cached_statuses
    mock_request.get.assert_not_called()
    mock_request.post.assert_not_called()
    mock_cache.set.assert_not_called()


def test_zero_cache_timeout_from_settings(client):
    client.config['cache_timeout'] = 0
    assert RainPoint('361481').cache_timeout == 0


@pytest.mark.parametrize('status', [None, {}, {'subDeviceStatus': []}])
def test_missing_sensor_readings(client, mock_cache, mock_request, status):
    mock_request.get.return_value.json.return_value = {
        'code': 0,
        'data': status,
    }
    assert client.statuses == {}


def test_custom_device_address(client, mock_cache, mock_request, mocker):
    mocker.patch.dict(
        'iotserver.apps.device.integrations.rainpoint.READING_MAP',
        {
            'temperature_sensor': {
                'address': 7,
                'model_code': 262,
                'fields': {'temperature_c': 'temperature'},
            }
        },
    )
    mock_request.get.return_value.json.return_value = {
        'code': 0,
        'data': {'subDeviceStatus': [{'id': 'D07', 'value': '10#85BA02'}]},
    }
    assert client.statuses == {'temperature': 21.0}


@pytest.mark.parametrize(
    'status_id, value, expected',
    [
        ('D01', '10#FD040F00', {'rainfall': 1.5}),
        ('D03', '10#8540018800', {'temperature': 0.0, 'humidity': 0}),
    ],
)
def test_requested_readings(
    client, mock_cache, mock_request, mocker, status_id, value, expected
):
    mocker.patch.object(client, '_authenticate', return_value='token')
    mock_request.get.return_value.json.return_value = {
        'code': 0,
        'data': {'subDeviceStatus': [{'id': status_id, 'value': value}]},
    }
    assert client.statuses == expected


def test_status_cache_is_scoped_to_hub(client, mock_cache):
    mock_cache.get.return_value = {}
    _ = client.statuses
    first_key = mock_cache.get.call_args.args[0]
    client.hub_id = 'other'
    _ = client.statuses
    second_key = mock_cache.get.call_args.args[0]
    assert first_key != second_key
