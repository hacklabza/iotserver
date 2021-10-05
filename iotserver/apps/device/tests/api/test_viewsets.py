import json

import pytest
from rest_framework.test import APIClient

from iotserver.apps.device.tests import factories as device_factories
from iotserver.apps.user.tests import factories as user_factories


@pytest.fixture
def api_client():
    token = user_factories.TokenFactory()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.mark.django_db
class TestLocationViewset(object):
    root_url = '/api/devices/locations/'

    def test_list(self, api_client):
        location = device_factories.LocationFactory()
        response = api_client.get(self.root_url)
        return_data = response.json()

        assert response.status_code == 200
        assert len(return_data) == 1

        assert return_data[0]['id'] == location.id
        assert return_data[0]['name'] == location.name
        assert return_data[0]['position'] == json.loads(location.position.geojson)

    def test_detail(self, api_client):
        location = device_factories.LocationFactory()
        response = api_client.get(f'{self.root_url}{location.pk}/')
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['id'] == location.id
        assert return_data['name'] == location.name
        assert return_data['position'] == json.loads(location.position.geojson)

    def test_create(self, api_client):
        location_data = {
            'name': 'Test Location',
            'position': {'type': 'Point', 'coordinates': [28.36402, -26.13946]},
        }
        response = api_client.post(f'{self.root_url}', location_data, format='json')
        return_data = response.json()

        assert response.status_code == 201
        assert return_data['name'] == location_data['name']
        assert return_data['position'] == location_data['position']

    def test_update(self, api_client):
        location = device_factories.LocationFactory()
        location_data = {
            'name': location.name,
            'position': {'type': 'Point', 'coordinates': [27.28812, -25.09912]},
        }
        response = api_client.put(
            f'{self.root_url}{location.pk}/', location_data, format='json'
        )
        return_data = response.json()

        assert response.status_code == 200, response.json()
        assert return_data['name'] == location_data['name']
        assert return_data['position'] == location_data['position']
