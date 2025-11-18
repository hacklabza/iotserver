import pytest

from iotserver.apps.device.integrations.weather import Location, Weather


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

    return mock_response


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

    def test_current_weather(self, weather, weather_data, mock_requests):
        mock_requests.json.return_value = weather_data

        data = weather.current

        assert type(data) == dict
        for key in ['humidity', 'rain', 'temperature']:
            assert key in data

        assert not data['rain']
        assert data['humidity'] == 50
        assert data['temperature'] == 25.12

    def test_forecast_weather(self, weather, weather_data, mock_requests):
        mock_requests.json.return_value = weather_data

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
