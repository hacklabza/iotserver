import pytest

from iotserver.apps.device.integrations.olarm import Olarm


@pytest.fixture(autouse=True)
def mock_settings(mocker):
    mock = mocker.patch('iotserver.apps.device.integrations.olarm.settings')
    mock.INTEGRATIONS = {
        'olarm': {
            'base_url': 'https://example.com',
            'api_key': 'api-key',
            'device_id': 'device-id',
            'cache_timeout': 60,
        }
    }
    return mock


@pytest.fixture(autouse=True)
def mock_cache(mocker):
    """Mock Django cache to return None (cache miss)"""
    mock = mocker.patch('iotserver.apps.device.integrations.olarm.cache')
    mock.get.return_value = None
    return mock


@pytest.fixture
def olarm():
    return Olarm()


@pytest.fixture
def mock_requests(mocker):
    mock = mocker.patch('iotserver.apps.device.integrations.olarm.requests')
    mock.get.return_value.json.return_value = {'data': []}
    return mock


def set_events(mock_requests, events):
    mock_requests.get.return_value.json.return_value = {'data': events}


def area_event(event_time, state):
    return {'eventTime': event_time, 'eventAction': 'area', 'eventState': state}


class TestOlarmIntegration(object):
    def test_init_uses_device_id_from_settings(self, olarm):
        assert olarm.device_id == 'device-id'

    def test_events(self, olarm, mock_requests):
        events = [{'eventTime': 1, 'eventAction': 'disarm'}]
        set_events(mock_requests, events)

        assert olarm.events == events
        mock_requests.get.assert_called_once_with(
            url='https://example.com/api/v4/devices/device-id/events',
            headers={'Authorization': 'Bearer api-key'},
            timeout=10,
        )
        mock_requests.get.return_value.raise_for_status.assert_called_once_with()

    def test_events_are_cached(self, olarm, mock_requests, mock_cache):
        events = [area_event(1, 'arm')]
        set_events(mock_requests, events)

        assert olarm.events == events

        cache_key = (
            'iotserver.apps.device.integrations.olarm.Olarm.events:device-id'
        )
        mock_cache.get.assert_called_once_with(cache_key)
        mock_cache.set.assert_called_once_with(cache_key, events, timeout=60)

    def test_events_cache_hit(self, olarm, mock_requests, mock_cache):
        events = [area_event(1, 'alarm')]
        mock_cache.get.return_value = events

        assert olarm.events == events
        mock_requests.get.assert_not_called()
        mock_cache.set.assert_not_called()

    def test_events_http_error_is_not_cached(
        self, olarm, mock_requests, mock_cache
    ):
        mock_requests.get.return_value.raise_for_status.side_effect = (
            RuntimeError
        )

        with pytest.raises(RuntimeError):
            _ = olarm.events
        mock_cache.set.assert_not_called()

    def test_events_missing_data_returns_empty_list(self, olarm, mock_requests):
        mock_requests.get.return_value.json.return_value = {}

        assert olarm.events == []

    def test_events_http_error_is_propagated(self, olarm, mock_requests):
        mock_requests.get.return_value.raise_for_status.side_effect = (
            RuntimeError('events fetch failed')
        )

        with pytest.raises(RuntimeError, match='events fetch failed'):
            _ = olarm.events

    def test_latest_event(self, olarm, mock_requests):
        set_events(
            mock_requests,
            [
                area_event(100, 'arm'),
                area_event(300, 'alarm'),
                area_event(200, 'disarm'),
            ],
        )

        assert olarm.latest_event == area_event(300, 'alarm')

    def test_latest_event_ignores_non_area_events(self, olarm, mock_requests):
        set_events(
            mock_requests,
            [
                area_event(100, 'arm'),
                {
                    'eventTime': 200,
                    'eventAction': 'zone',
                    'eventState': 'active',
                },
            ],
        )

        assert olarm.latest_event == area_event(100, 'arm')

    def test_latest_event_no_events(self, olarm, mock_requests):
        assert olarm.latest_event is None

    def test_latest_event_no_area_events(self, olarm, mock_requests):
        set_events(
            mock_requests,
            [{'eventTime': 200, 'eventAction': 'zone', 'eventState': 'active'}],
        )

        assert olarm.latest_event is None

    @pytest.mark.parametrize('state', ['alarm', 'fire', 'emergency'])
    def test_activated_when_latest_event_is_alarm(
        self, olarm, mock_requests, state
    ):
        set_events(
            mock_requests, [area_event(100, 'arm'), area_event(200, state)]
        )

        assert olarm.activated is True

    @pytest.mark.parametrize(
        'state',
        ['arm', 'disarm', 'stay', 'sleep', 'notready', 'countdown', None],
    )
    def test_not_activated_when_latest_event_is_not_alarm(
        self, olarm, mock_requests, state
    ):
        set_events(
            mock_requests, [area_event(100, 'alarm'), area_event(200, state)]
        )

        assert olarm.activated is False

    def test_not_activated_when_no_events(self, olarm, mock_requests):
        assert olarm.activated is False
