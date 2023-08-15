import base64
import hashlib
import hmac
import json
import string
import random
import time
from typing import Dict, List

import requests
from django.conf import settings


class Sonoff(object):
    """Simple sonoff integration class which can switch a basic device on/off.

    Args:
        device_id (str): The sonoff device_id
    """

    def __init__(self, device_id: str) -> None:
        self.config = settings.INTEGRATIONS['sonoff']
        
        self.device_id = device_id
        self.nonce = None

    def _sign_request(self, data: Dict) -> str:
        """
        Sign the request in order to authenticate.
        """
        hmac_digest = hmac.new(
            self.config['app_secret'].encode('utf-8'),
            json.dumps(data).encode('utf-8'), 
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(hmac_digest).decode()
    
    def _generate_nonce(self) -> str:
        """
        Generate a random 8 character nonce.
        """
        return ''.join([random.choice(string.ascii_letters) for _ in range(8)])

    def _authenticate(self) -> str:
        """
        Authenticate with a pre-configured email address and password and return the 
        access_token.
        """
        self.nonce = self._generate_nonce()
        request_data = {
            'appid': self.config['app_id'],
            'countryCode': self.config['country_code'],
            'email': self.config['email'],
            'password': self.config['password'],
            'ts': time.time(),
            'version': 8,
            'nonce': self.nonce,
        }
        signed_token = self._sign_request(request_data)

        response = requests.post(
            url=self.config['auth_url'],
            json=request_data,
            headers={
                'Authorization': f'Sign {signed_token}'
            },
        )
        response.raise_for_status()
        auth_data = response.json()

        return auth_data['at']


    def toggle_device(self, state: str) -> List:
        """
        Toggle the device state, valid states are [on, off].
        """
        access_token = self._authenticate()

        request_data = {
            'deviceid': self.device_id,
            'params': {'switch': state},
            'appid': self.config['app_id'],
            'ts': time.time(),
            'version': 8,
            'nonce': self.nonce,
        }

        response = requests.post(
            url=self.config['device_url'],
            json=request_data,
            headers={
                'Authorization': f'Bearer {access_token}'
            },
        )
        response.raise_for_status()

        return state

    
