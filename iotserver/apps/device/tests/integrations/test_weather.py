import pytest

from iotserver.apps.device.integrations.weather import Location, Weather


@pytest.fixture(autouse=True)
def mock_settings(mocker):
    mock = mocker.patch('iotserver.apps.device.integrations.weather.settings')
    mock.INTEGRATIONS = {
        'weather': {
            'url': 'https://api.openweathermap.org/data/3.0/onecall',
            'api_key': 'openweather-key',
        }
    }
    return mock


@pytest.fixture(autouse=True)
def mock_cache(mocker):
    """Mock Django cache to return None (cache miss)"""
    mock = mocker.patch('iotserver.apps.device.integrations.weather.cache')
    mock.get.return_value = None
    return mock


@pytest.fixture
def mock_requests(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = []
    mock_response.status_code = 200

    mock_requests_module = mocker.patch('iotserver.apps.device.integrations.weather.requests')
    mock_requests_module.get.return_value = mock_response
    mock_requests_module.response = mock_response

    return mock_requests_module


@pytest.fixture
def location():
    return Location(latitude=-26.12345, longitude=28.54321)


@pytest.fixture
def weather(location):
    return Weather(location=location)


@pytest.fixture
def weather_data():
    return {
        'current': {
            'humidity': 50,
            'temp': 25.12,
            'weather': [{'main': 'Cloud'}],
        },
        'daily': [
            {
                'dt': 1633392000,
                'humidity': 60,
                'rain': 0.3,
                'temp': {'max': 18.51, 'min': 9.35},
            },
            {
                'dt': 1633478400,
                'humidity': 70,
                'rain': 0.15,
                'temp': {'max': 23.19, 'min': 13.02},
            },
        ],
    }


class TestWeatherIntegration(object):
    def test_build_url(self, weather):
        url = weather._build_url()
        assert (
            'https://api.openweathermap.org/data/3.0/onecall?lat=-26.12345&lon=28.54321'
            in url
        )

    def test_get_weather_data_from_cache(
        self, weather, weather_data, mock_cache, mock_requests
    ):
        mock_cache.get.return_value = weather_data

        assert weather._get_weather_data() == weather_data
        mock_requests.get.assert_not_called()

    def test_get_weather_data_from_api(
        self, weather, weather_data, mock_cache, mock_requests
    ):
        mock_requests.response.json.return_value = weather_data

        assert weather._get_weather_data() == weather_data
        mock_requests.get.assert_called_once_with(weather._build_url())
        mock_requests.response.raise_for_status.assert_called_once_with()
        mock_cache.set.assert_called_once_with(
            f'{weather.cache_prefix}._get_weather_data:{weather.location}', weather_data
        )

    def test_empty_weather_data_is_not_cached(self, weather, mock_cache, mock_requests):
        assert weather._get_weather_data() is None
        mock_cache.set.assert_not_called()

    def test_http_errors_are_propagated(self, weather, mock_requests):
        mock_requests.response.raise_for_status.side_effect = RuntimeError('API failure')

        with pytest.raises(RuntimeError, match='API failure'):
            weather._get_weather_data()

    def test_current_weather(self, weather, weather_data, mock_requests):
        mock_requests.response.json.return_value = weather_data

        data = weather.current

        assert type(data) == dict
        for key in ['humidity', 'rain', 'temperature']:
            assert key in data

        assert not data['rain']
        assert data['humidity'] == 50
        assert data['temperature'] == 25.12

    def test_current_weather_detects_rain(self, weather, weather_data, mock_requests):
        weather_data['current']['weather'][0]['main'] = 'Rain'
        mock_requests.response.json.return_value = weather_data

        assert weather.current['rain']

    @pytest.mark.parametrize('current_data', [{}, {'weather': []}])
    def test_malformed_current_weather_returns_none(
        self, weather, weather_data, mock_requests, current_data
    ):
        weather_data['current'] = current_data
        mock_requests.response.json.return_value = weather_data

        assert weather.current is None

    def test_current_weather_returns_none_for_empty_response(self, weather, mock_requests):
        assert weather.current is None

    def test_forecast_weather(self, weather, weather_data, mock_requests):
        mock_requests.response.json.return_value = weather_data

        data = weather.forecast

        assert type(data) == list
        assert len(data) == 2
        for key in ['date', 'humidity', 'rain', 'temperature']:
            for item in data:
                assert key in item

        assert data[0]['date'] == '2021-10-05'
        assert data[0]['rain']
        assert data[0]['humidity'] == 60
        assert data[0]['temperature'] == {'maximum': 18.51, 'minimum': 9.35}

        assert data[1]['date'] == '2021-10-06'
        assert not data[1]['rain']

    def test_forecast_uses_defaults_for_optional_fields(
        self, weather, weather_data, mock_requests
    ):
        weather_data['daily'] = [
            {'dt': 1633392000, 'temp': {'max': 18.51, 'min': 9.35}}
        ]
        mock_requests.response.json.return_value = weather_data

        assert weather.forecast[0]['humidity'] is None
        assert not weather.forecast[0]['rain']

    def test_malformed_forecast_returns_none(self, weather, weather_data, mock_requests):
        weather_data['daily'][0]['temp'] = {}
        mock_requests.response.json.return_value = weather_data

        assert weather.forecast is None

    def test_forecast_returns_none_for_empty_response(self, weather, mock_requests):
        assert weather.forecast is None
