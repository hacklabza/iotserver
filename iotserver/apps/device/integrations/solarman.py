import hashlib
from typing import Dict

import requests
from django.conf import settings


class Solarman(object):
    """Simple Solarman integration class which returns realtime data for a
    solar power station.

    Args:
        station_id (int): The Solarman station_id
    """

    def __init__(self, station_id: int) -> None:
        self.config = settings.INTEGRATIONS['solarman']
        self.station_id = station_id

    def _hash_password(self) -> str:
        return hashlib.sha256(self.config['password'].encode('utf-8')).hexdigest()

    def _authenticate(self) -> str:
        """
        Authenticate with a pre-configured email address and password and return the
        access_token.
        """
        auth_url = (
            f"{self.config['base_url']}/account/v1.0/token"
            f"?appId={self.config['app_id']}&language=en"
        )
        request_data = {
            'appSecret': self.config['app_secret'],
            'email': self.config['email'],
            'password': self._hash_password(),
        }

        response = requests.post(url=auth_url, json=request_data)
        response.raise_for_status()
        auth_data = response.json()

        return auth_data['access_token']

    @property
    def real_time(self) -> Dict:
        """
        Return the solar input, battery state of charge and current consumption
        for the station.
        """
        access_token = self._authenticate()

        response = requests.post(
            url=f"{self.config['base_url']}/station/v1.0/realTime",
            json={'stationId': self.station_id},
            headers={'Authorization': f'Bearer {access_token}'},
        )
        response.raise_for_status()
        real_time_data = response.json()

        return {
            'solar_input': real_time_data['generationPower'],
            'battery_soc': real_time_data['batterySoc'],
            'current_consumption': real_time_data['usePower'],
        }
