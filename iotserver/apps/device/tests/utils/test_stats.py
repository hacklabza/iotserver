import pytest

from iotserver.apps.device.tests import factories as device_factories


@pytest.mark.django_db
class TestAggregateStatuses(object):
    def setup_method(self, test_method):
        self.location = device_factories.DeviceFactory()

    def test_aggregate_statuses(self):
        statuses = [
            device_factories.DeviceStatusFactory(
                device=self.location,
                status={
                    'sensor-a': {'reading-a': 30, 'reading-b': 15},
                    'sensor-b': 20,
                    'sensor-c': True,
                },
            ),
            device_factories.DeviceStatusFactory(
                device=self.location,
                status={
                    'sensor-a': {'reading-a': 30, 'reading-b': 15},
                    'sensor-b': 40,
                    'sensor-c': False,
                },
            ),
        ]

        aggregate = self.location.aggregate_statuses

        assert aggregate == {
            'sensor-a': {
                'reading-a': {'minimum': 30, 'maximum': 30, 'average': 30.0},
                'reading-b': {'minimum': 15, 'maximum': 15, 'average': 15.0},
            },
            'sensor-b': {'minimum': 20, 'maximum': 40, 'average': 30.0},
        }
