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

        assert response.status_code == 200
        assert return_data['name'] == location_data['name']
        assert return_data['position'] == location_data['position']


@pytest.mark.django_db
class TestDeviceTypeViewset(object):
    root_url = '/api/devices/types/'

    def test_list(self, api_client):
        device_type = device_factories.DeviceTypeFactory()
        response = api_client.get(self.root_url)
        return_data = response.json()

        assert response.status_code == 200
        assert len(return_data) == 1

        assert return_data[0]['name'] == device_type.name
        assert str(device_type.pk) in return_data[0]['url']

    def test_detail(self, api_client):
        device_type = device_factories.DeviceTypeFactory()
        response = api_client.get(f'{self.root_url}{device_type.pk}/')
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['name'] == device_type.name
        assert str(device_type.pk) in return_data['url']

    def test_create(self, api_client):
        device_type_data = {'name': 'Test Type'}
        response = api_client.post(f'{self.root_url}', device_type_data, format='json')
        return_data = response.json()

        assert response.status_code == 201
        assert return_data['name'] == device_type_data['name']

    def test_update(self, api_client):
        device_type = device_factories.DeviceTypeFactory()
        device_type_data = {'name': 'Test Type'}
        response = api_client.put(
            f'{self.root_url}{device_type.pk}/', device_type_data, format='json'
        )
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['name'] == device_type_data['name']
        assert str(device_type.pk) in return_data['url']


@pytest.mark.django_db
class TestDeviceViewset(object):
    root_url = '/api/devices/'

    def test_list(self, api_client):
        device = device_factories.DeviceFactory()
        response = api_client.get(self.root_url)
        return_data = response.json()

        assert response.status_code == 200
        assert len(return_data) == 1

        assert return_data[0]['name'] == device.name

        assert str(device.pk) in return_data[0]['url']
        assert str(device.type.pk) in return_data[0]['type']
        assert str(device.location.pk) in return_data[0]['location']

    def test_detail(self, api_client):
        device = device_factories.DeviceFactory()
        response = api_client.get(f'{self.root_url}{device.pk}/')
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['name'] == device.name

        assert str(device.pk) in return_data['url']
        assert str(device.type.pk) in return_data['type']
        assert str(device.location.pk) in return_data['location']

    def test_create(self, api_client):
        device_type = device_factories.DeviceTypeFactory()
        location = device_factories.LocationFactory()
        device_data = {
            'name': 'Test Device',
            'description': 'Test Device Description',
            'type': device_type.pk,
            'location': location.pk,
            'ip_address': '192.168.0.2',
            'mac_address': 'EE:01:A0:01:60:BE',
            'hostname': 'test-device-002',
        }
        response = api_client.post(f'{self.root_url}', device_data, format='json')
        return_data = response.json()

        assert response.status_code == 201
        assert return_data['name'] == device_data['name']

        assert str(device_type.pk) in return_data['type']
        assert str(location.pk) in return_data['location']

    def test_update(self, api_client):
        device = device_factories.DeviceFactory()
        device_data = {
            'name': 'Test Device',
            'description': 'Test Device Description',
            'type': device.type.pk,
            'location': device.location.pk,
            'ip_address': device.ip_address,
            'mac_address': device.mac_address,
            'hostname': device.hostname,
        }
        response = api_client.put(
            f'{self.root_url}{device.pk}/', device_data, format='json'
        )
        return_data = response.json()

        assert response.status_code == 200, return_data
        assert return_data['name'] == device_data['name']

        assert str(device.pk) in return_data['url']
        assert str(device.type.pk) in return_data['type']
        assert str(device.location.pk) in return_data['location']
