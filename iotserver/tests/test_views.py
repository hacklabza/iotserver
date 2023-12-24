import pytest
from rest_framework.test import APIClient

from iotserver.apps.device.tests import factories as device_factories


@pytest.fixture
def api_client():
    client = APIClient()
    return client


@pytest.mark.django_db
class TestHealthView(object):
    def setup_method(self):
        self.root_url = '/health/'
        self.device_health = device_factories.DeviceHealthFactory()

    def test_detail__no_device(self, api_client):
        response = api_client.get(self.root_url)
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['status'] == 'ok'

    def test_detail__device_id(self, api_client):
        response = api_client.get(f'{self.root_url}{self.device_health.device_id}/')
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['status'] == 'ok'
