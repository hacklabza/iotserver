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
        assert return_data['count'] == 1

        assert return_data['results'][0]['id'] == self.location.id
        assert return_data['results'][0]['name'] == self.location.name
        assert return_data['results'][0]['position'] == json.loads(
            self.location.position.geojson
        )

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
        assert return_data['count'] == 1

        assert return_data['results'][0]['name'] == self.device_type.name
        assert self.device_type.pk == return_data['results'][0]['id']

    def test_detail(self, api_client):
        response = api_client.get(f'{self.root_url}{self.device_type.pk}/')
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['name'] == self.device_type.name
        assert self.device_type.pk == return_data['id']

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
        assert self.device_type.pk == return_data['id']


@pytest.mark.django_db
class TestDeviceViewset(object):
    root_url = '/api/devices/'

    def setup_method(self, test_method):
        self.device = device_factories.DeviceFactory()
        self.device_health = device_factories.DeviceHealthFactory(device=self.device)
        self.device_type = device_factories.DeviceTypeFactory()
        self.location = device_factories.LocationFactory()

    def test_list(self, api_client):
        response = api_client.get(self.root_url)
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['count'] == 1

        assert return_data['results'][0]['name'] == self.device.name

        assert str(self.device.pk) == return_data['results'][0]['id']
        assert self.device.type.pk == return_data['results'][0]['type']['id']
        assert self.device.location.pk == return_data['results'][0]['location']['id']
        assert (
            self.device_health.status == return_data['results'][0]['health']['status']
        )

    def test_detail(self, api_client):
        response = api_client.get(f'{self.root_url}{self.device.pk}/')
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['name'] == self.device.name

        assert str(self.device.pk) == return_data['id']
        assert self.device.type.pk == return_data['type']['id']
        assert self.device.location.pk == return_data['location']['id']

    @factory.django.mute_signals(signals.post_save, signals.pre_save)
    def test_create(self, api_client):
        device_data = {
            'name': 'Test Device',
            'description': 'Test Device Description',
            'type': self.device_type.id,
            'location': self.location.id,
            'ip_address': '192.168.0.2',
            'mac_address': 'EE:01:A0:01:60:BE',
            'hostname': 'test-device-001',
        }
        response = api_client.post(f'{self.root_url}', device_data, format='json')
        return_data = response.json()

        assert response.status_code == 201
        assert return_data['name'] == device_data['name']

        assert self.device_type.pk == return_data['type']
        assert self.location.pk == return_data['location']

    @factory.django.mute_signals(signals.post_save, signals.pre_save)
    def test_update(self, api_client):
        device_data = {
            'name': 'Test Device - v2',
            'description': 'Test Device - v2 Description',
            'type': self.device_type.id,
            'location': self.location.id,
            'ip_address': '192.168.0.3',
            'mac_address': 'EE:01:A0:01:60:BE',
            'hostname': 'test-device-v2-001',
        }
        response = api_client.put(
            f'{self.root_url}{self.device.pk}/', device_data, format='json'
        )
        return_data = response.json()

        assert response.status_code == 200, return_data
        assert return_data['name'] == device_data['name']

        assert self.device_type.pk == return_data['type']
        assert self.location.pk == return_data['location']


@pytest.mark.django_db
class TestDevicePinViewset(object):
    root_url = '/api/devices/pins/'

    def setup_method(self, test_method):
        self.device = device_factories.DeviceFactory(
            ip_address='192.168.0.2', mac_address='0E:01:2A:C1:92:5E'
        )
        self.device_pins = device_factories.DevicePinFactory(devices=[self.device])

    def test_list(self, api_client):
        response = api_client.get(self.root_url)
        return_data = response.json()

        assert response.status_code == 200
        assert return_data['count'] == 1

        assert return_data['results'][0]['name'] == self.device_pins.name
        assert return_data['results'][0]['identifier'] == self.device_pins.identifier

        assert self.device_pins.pk == return_data['results'][0]['id']
        assert (
            str(self.device_pins.devices.first().pk)
            in return_data['results'][0]['devices']
        )

    def test_detail(self, api_client):
        response = api_client.get(f'{self.root_url}{self.device_pins.pk}/')
        return_data = response.json()

        assert response.status_code == 200

        assert return_data['name'] == self.device_pins.name
        assert return_data['identifier'] == self.device_pins.identifier

        assert self.device_pins.pk == return_data['id']
        assert str(self.device_pins.devices.first().pk) in return_data['devices']

    def test_create(self, api_client):
        device_pin_data = {
            'devices': [self.device.id],
            'name': 'Test Pin',
            'identifier': 'test-pin',
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

        assert str(self.device.id) in return_data['devices']

    def test_update(self, api_client):
        device_pin_data = {
            'devices': [self.device.id],
            'name': 'Test Pin 2',
            'identifier': 'test-pin-2',
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

        assert str(self.device.id) in return_data['devices']
