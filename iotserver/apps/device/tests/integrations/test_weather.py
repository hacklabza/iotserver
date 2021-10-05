import pytest

from iotserver.apps.device.integrations.weather import Location, Weather


@pytest.fixture()
def mock_requests(mocker):
    return mocker.patch('iotserver.apps.device.integrations.weather.requests')


@pytest.fixture(autouse=True)
def mock_get_response(mocker, mock_requests):
    response = mocker.Mock()
    response.json.return_value = []
    response.status_code = 200
    mock_requests.get.return_value = response
    return response


@pytest.fixture
def location():
    return Location(latitude=-26.13946, longitude=28.36402)


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
            'https://api.openweathermap.org/data/2.5/onecall?lat=-26.13946&lon=28.36402'
            in url
        )

    def test_current_weather(self, mock_get_response, weather, weather_data):
        response = mock_get_response
        response.json.return_value = weather_data

        data = weather.current

        assert type(data) == dict
        for key in ['humidity', 'rain', 'temperature']:
            assert key in data

        assert not data['rain']
        assert data['humidity'] == 50
        assert data['temperature'] == 25.12

    def test_forecast_weather(self, mock_get_response, weather, weather_data):
        response = mock_get_response
        response.json.return_value = weather_data

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
