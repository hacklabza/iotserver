import hashlib
import secrets

import requests
from django.conf import settings
from django.core.cache import cache

READING_MAP = {
    'rain_gauge': {
        'address': 1,
        'model_code': 87,
        'fields': {'rainfall_mm_hour': 'rainfall'},
    },
    'pool_thermometer': {
        'address': 2,
        'model_code': 268,
        'fields': {'temperature_c': 'pool_temperature'},
    },
    'temperature_sensor': {
        'address': 3,
        'model_code': 262,
        'fields': {
            'temperature_c': 'temperature',
            'humidity_pct': 'humidity',
        },
    },
}


class RainPoint:
    """Read-only RainPoint Home integration via the HomGar cloud API."""

    def __init__(self, hub_id: str, cache_timeout: int = None) -> None:
        self.config = settings.INTEGRATIONS['rainpoint']
        self.hub_id = hub_id
        self.cache_timeout = cache_timeout or self.config['cache_timeout']
        self.cache_prefix = f'{self.__module__}.{self.__class__.__name__}'
        self.request_headers = {
            'lang': 'en',
            'appCode': self.config['app_code'],
        }

    def _authenticate(self):
        auth_url = f"{self.config['base_url']}/auth/basic/app/login"
        request_data = {
            'areaCode': self.config['area_code'],
            'phoneOrEmail': self.config['email'],
            'password': hashlib.md5(
                self.config['password'].encode()
            ).hexdigest(),
            'deviceId': secrets.token_hex(16),
        }
        response = requests.post(
            url=auth_url,
            headers=self.request_headers,
            json=request_data,
            timeout=settings.INTEGRATION_TIMEOUT,
        )
        response.raise_for_status()
        auth_data = response.json()['data']

        return auth_data['token']

    def _decode_sensor(self, value, model_code):
        if not isinstance(value, str) or not value.startswith(('10#', '11#')):
            return {}

        data = bytes.fromhex(value.split('#', 1)[1])
        offset = 1 if value.startswith('11#') else 0
        datapoints = {}
        while offset < len(data):
            header = data[offset]
            offset += 1
            if not header & 0x80:
                continue
            code = (header >> 2) & 0x1F
            length = (header & 0x03) + 1
            if code == 31:
                if offset >= len(data):
                    raise ValueError('Truncated RainPoint datapoint code')
                code = data[offset]
                offset += 1
            else:
                code += 8
            if offset + length > len(data):
                raise ValueError('Truncated RainPoint datapoint value')
            datapoints[code] = data[offset : offset + length]
            offset += length

        readings = {}
        if model_code == 87:
            if 4 in datapoints:
                readings['rainfall_mm_hour'] = (
                    int.from_bytes(datapoints[4], 'little') / 10
                )
        elif model_code in (262, 268):
            if 9 in datapoints:
                fahrenheit = (
                    int.from_bytes(datapoints[9], 'little', signed=True) / 10
                )
                readings['temperature_c'] = round((fahrenheit - 32) * 5 / 9, 1)
            if model_code == 262 and 10 in datapoints:
                readings['humidity_pct'] = int.from_bytes(
                    datapoints[10], 'little'
                )
        return readings

    @property
    def statuses(self):
        cache_key = f'{self.cache_prefix}.statuses:{self.hub_id}'
        cached_statuses = cache.get(cache_key)
        if cached_statuses is not None:
            return cached_statuses

        token = self._authenticate()
        headers = self.request_headers.copy()
        headers['auth'] = token

        response = requests.get(
            url=f"{self.config['base_url']}/app/device/getDeviceStatus",
            params={'mid': self.hub_id},
            headers=headers,
            timeout=settings.INTEGRATION_TIMEOUT,
        )
        response.raise_for_status()
        statuses_data = response.json()['data']

        entries = {
            entry['id']: entry
            for entry in (statuses_data or {}).get('subDeviceStatus', [])
        }
        statuses = {}
        for reading in READING_MAP.values():
            status_id = f'D{int(reading["address"]):02d}'
            entry = entries.get(status_id, {})
            readings = self._decode_sensor(
                entry.get('value'), reading['model_code']
            )
            statuses.update(
                {
                    output: readings[field]
                    for field, output in reading['fields'].items()
                    if field in readings
                }
            )

        cache.set(cache_key, statuses, timeout=self.cache_timeout)

        return statuses
