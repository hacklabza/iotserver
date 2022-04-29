import json

import factory
import pytest
from django.db.models import signals
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

    def setup_method(self, test_method):
        self.location = device_factories.LocationFactory()

    def test_list(self, api_client):
        response = api_client.get(self.root_url)
        return_data = response.json()

        assert response.status_code == 200
        assert len(return_data) == 1

        assert return_data[0]['id'] == self.location.id
        assert return_data[0]['name'] == self.location.name
        assert return_data[0]['position'] == json.loads(self.location.position.geojson)

    def test_detail(self, api_client):
        response = api_client.get(f'{self.root_url}{self.location.pk}/')
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['id'] == self.location.id
        assert return_data['name'] == self.location.name
        assert return_data['position'] == json.loads(self.location.position.geojson)

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
        location_data = {
            'name': self.location.name,
            'position': {'type': 'Point', 'coordinates': [27.28812, -25.09912]},
        }
        response = api_client.put(
            f'{self.root_url}{self.location.pk}/', location_data, format='json'
        )
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['name'] == location_data['name']
        assert return_data['position'] == location_data['position']


@pytest.mark.django_db
class TestDeviceTypeViewset(object):
    root_url = '/api/devices/types/'

    def setup_method(self, test_method):
        self.device_type = device_factories.DeviceTypeFactory()

    def test_list(self, api_client):

        response = api_client.get(self.root_url)
        return_data = response.json()

        assert response.status_code == 200
        assert len(return_data) == 1

        assert return_data[0]['name'] == self.device_type.name
        assert str(self.device_type.pk) in return_data[0]['url']

    def test_detail(self, api_client):
        response = api_client.get(f'{self.root_url}{self.device_type.pk}/')
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['name'] == self.device_type.name
        assert str(self.device_type.pk) in return_data['url']

    def test_create(self, api_client):
        device_type_data = {'name': 'Test Type'}
        response = api_client.post(f'{self.root_url}', device_type_data, format='json')
        return_data = response.json()

        assert response.status_code == 201
        assert return_data['name'] == device_type_data['name']

    def test_update(self, api_client):
        device_type_data = {'name': 'Test Type'}
        response = api_client.put(
            f'{self.root_url}{self.device_type.pk}/', device_type_data, format='json'
        )
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['name'] == device_type_data['name']
        assert str(self.device_type.pk) in return_data['url']


@pytest.mark.django_db
@factory.django.mute_signals(signals.post_save, signals.pre_save)
class TestDeviceViewset(object):
    root_url = '/api/devices/'

    def setup_method(self, test_method):
        self.device = device_factories.DeviceFactory()

    def test_list(self, api_client):
        response = api_client.get(self.root_url)
        return_data = response.json()

        assert response.status_code == 200
        assert len(return_data) == 1

        assert return_data[0]['name'] == self.device.name

        assert str(self.device.pk) in return_data[0]['url']
        assert str(self.device.type.pk) in return_data[0]['type']
        assert str(self.device.location.pk) in return_data[0]['location']

    def test_detail(self, api_client):
        response = api_client.get(f'{self.root_url}{self.device.pk}/')
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['name'] == self.device.name

        assert str(self.device.pk) in return_data['url']
        assert str(self.device.type.pk) in return_data['type']
        assert str(self.device.location.pk) in return_data['location']

    def test_create(self, api_client):
        device_type = device_factories.DeviceTypeFactory()
        location = device_factories.LocationFactory()

        device_data = {
            'name': 'Test Device',
            'description': 'Test Device Description',
            'type': device_type.resource_url,
            'location': location.resource_url,
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
        device_type = device_factories.DeviceTypeFactory()
        location = device_factories.LocationFactory()

        device_data = {
            'name': 'Test Device',
            'description': 'Test Device Description',
            'type': device_type.resource_url,
            'location': location.resource_url,
            'ip_address': self.device.ip_address,
            'mac_address': self.device.mac_address,
            'hostname': self.device.hostname,
        }
        response = api_client.put(
            f'{self.root_url}{self.device.pk}/', device_data, format='json'
        )
        return_data = response.json()

        assert response.status_code == 200, return_data
        assert return_data['name'] == device_data['name']

        assert str(self.device.pk) in return_data['url']
        assert str(device_type.pk) in return_data['type']
        assert str(location.pk) in return_data['location']


@pytest.mark.django_db
class TestDevicePinViewset(object):
    root_url = '/api/devices/pins/'

    def setup_method(self, test_method):
        self.device_pins = device_factories.DevicePinFactory()

    def test_list(self, api_client):
        response = api_client.get(self.root_url)
        return_data = response.json()

        assert response.status_code == 200
        assert len(return_data) == 1

        assert return_data[0]['name'] == self.device_pins.name
        assert return_data[0]['identifier'] == self.device_pins.identifier

        assert str(self.device_pins.pk) in return_data[0]['url']
        assert str(self.device_pins.device.pk) in return_data[0]['device']

    def test_detail(self, api_client):
        response = api_client.get(f'{self.root_url}{self.device_pins.pk}/')
        return_data = response.json()

        assert response.status_code == 200

        assert return_data['name'] == self.device_pins.name
        assert return_data['identifier'] == self.device_pins.identifier

        assert str(self.device_pins.pk) in return_data['url']
        assert str(self.device_pins.device.pk) in return_data['device']

    def test_create(self, api_client):
        device = device_factories.DeviceFactory()

        device_pin_data = {
            'device': device.resource_url,
            'name': 'Test Pin',
            'pin_number': 1,
            'analog': True,
            'read': False,
            'rule': {},
        }
        response = api_client.post(f'{self.root_url}', device_pin_data, format='json')

        return_data = response.json()

        assert response.status_code == 201

        assert return_data['name'] == device_pin_data['name']
        assert return_data['identifier'] == 'test-pin'

        assert str(device.id) in return_data['device']

    def test_update(self, api_client):
        device = device_factories.DeviceFactory()

        device_pin_data = {
            'device': device.resource_url,
            'name': 'Test Pin 2',
            'pin_number': self.device_pins.pin_number,
            'analog': self.device_pins.analog,
            'read': self.device_pins.read,
            'rule': {},
        }
        response = api_client.put(
            f'{self.root_url}{self.device_pins.pk}/', device_pin_data, format='json'
        )
        return_data = response.json()

        assert response.status_code == 200

        assert return_data['name'] == device_pin_data['name']
        assert return_data['identifier'] == 'test-pin-2'

        assert str(device.id) in return_data['device']
