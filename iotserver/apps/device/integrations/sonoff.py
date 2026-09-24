import base64
import hashlib
import hmac
import json
import random
import string
from datetime import datetime, timedelta
from datetime import timezone as tzinfo
from typing import Dict
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils import timezone

from iotserver.apps.device.models import SonoffToken


class SonoffNotAuthorizedError(Exception):
    """Raised when there is no valid Sonoff OAuth token to authenticate with."""


class Sonoff(object):
    """Simple sonoff integration class which can switch a basic device on/off.

    Uses the eWeLink v2 OAuth API, see:
    https://coolkit-technologies.github.io/eWeLink-API/#/en/OAuth2.0

    The configured appid only permits the OAuth authorization-code flow, so a
    staff member must authorize the integration once (via `authorize_url()` /
    `exchange_code()`) before `toggle_device()` can be used. The resulting
    token pair is persisted in `SonoffToken` and refreshed automatically.

    Args:
        device_id (str): The sonoff device_id, not required for the
            authorize/exchange_code steps of the OAuth flow.
    """

    def __init__(self, device_id: str = None) -> None:
        self.config = settings.INTEGRATIONS['sonoff']
        self.device_id = device_id

    def _sign(self, message: str) -> str:
        """
        Sign a message in order to authenticate.
        """
        hmac_digest = hmac.new(
            self.config['app_secret'].encode('utf-8'),
            message.encode('utf-8'),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_digest).decode()

    def _sign_request(self, data: Dict) -> str:
        """
        Sign a JSON request body in order to authenticate.
        """
        return self._sign(json.dumps(data))

    def _generate_nonce(self) -> str:
        """
        Generate a random 8 character nonce.
        """
        return ''.join([random.choice(string.ascii_letters) for _ in range(8)])

    def _headers(self, authorization: str) -> Dict:
        return {
            'X-CK-Appid': self.config['app_id'],
            'X-CK-Nonce': self._generate_nonce(),
            'Authorization': authorization,
            'Content-Type': 'application/json',
        }

    def _unwrap(self, response: requests.Response) -> Dict:
        """
        Raise for a v2 API-level error and return the response's `data`.
        """
        response_data = response.json()
        if response_data['error'] != 0:
            raise RuntimeError(response_data['msg'])

        return response_data['data']

    @staticmethod
    def _from_epoch_ms(value: int) -> datetime:
        return datetime.fromtimestamp(value / 1000, tz=tzinfo.utc)

    def _store_tokens(
        self,
        access_token: str,
        refresh_token: str,
        access_token_expires_at: datetime,
        refresh_token_expires_at: datetime,
    ) -> None:
        # Update the existing singleton row in place rather than assuming pk=1,
        # since a deleted row's pk is not reused (e.g. on Postgres).
        token = SonoffToken.objects.first() or SonoffToken()
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.access_token_expires_at = access_token_expires_at
        token.refresh_token_expires_at = refresh_token_expires_at
        token.region = self.config['region']
        token.save()

    def authorize_url(self, state: str) -> str:
        """
        Build the eWeLink authorization page URL a staff member must open to
        grant access to their eWeLink account.
        """
        seq = str(int(timezone.now().timestamp() * 1000))
        params = {
            'clientId': self.config['app_id'],
            'seq': seq,
            'authorization': self._sign(f"{self.config['app_id']}_{seq}"),
            'redirectUrl': self.config['redirect_url'],
            'grantType': 'authorization_code',
            'state': state,
            'nonce': self._generate_nonce(),
            'showQRCode': 'false',
        }
        return f"{self.config['authorize_url']}?{urlencode(params)}"

    def exchange_code(self, code: str) -> None:
        """
        Exchange an authorization code (obtained via `authorize_url()`) for an
        access/refresh token pair, and persist it.
        """
        request_data = {
            'code': code,
            'redirectUrl': self.config['redirect_url'],
            'grantType': 'authorization_code',
        }
        signed_token = self._sign_request(request_data)

        response = requests.post(
            url=self.config['token_url'],
            json=request_data,
            headers=self._headers(f'Sign {signed_token}'),
        )
        response.raise_for_status()
        data = self._unwrap(response)

        self._store_tokens(
            access_token=data['accessToken'],
            refresh_token=data['refreshToken'],
            access_token_expires_at=self._from_epoch_ms(data['atExpiredTime']),
            refresh_token_expires_at=self._from_epoch_ms(data['rtExpiredTime']),
        )

    def _refresh(self, token: SonoffToken) -> str:
        request_data = {'rt': token.refresh_token}
        signed_token = self._sign_request(request_data)

        response = requests.post(
            url=self.config['refresh_url'],
            json=request_data,
            headers=self._headers(f'Sign {signed_token}'),
        )
        response.raise_for_status()
        data = self._unwrap(response)

        now = timezone.now()
        self._store_tokens(
            access_token=data['at'],
            refresh_token=data['rt'],
            access_token_expires_at=now + timedelta(days=30),
            refresh_token_expires_at=now + timedelta(days=60),
        )
        return data['at']

    def _get_access_token(self) -> str:
        """
        Return a usable access token, refreshing it first if it has expired.
        """
        token = SonoffToken.objects.first()
        if token is None:
            raise SonoffNotAuthorizedError(
                'Sonoff integration is not authorized yet, visit the '
                'authorize URL to connect an eWeLink account.'
            )

        if token.access_token_expires_at > timezone.now():
            return token.access_token

        return self._refresh(token)

    def toggle_device(self, state: str) -> str:
        """
        Toggle the device state, valid states are [on, off].
        """
        access_token = self._get_access_token()

        request_data = {
            'type': 1,
            'id': self.device_id,
            'params': {'switch': state},
        }

        response = requests.post(
            url=self.config['device_url'],
            json=request_data,
            headers=self._headers(f'Bearer {access_token}'),
        )
        response.raise_for_status()
        self._unwrap(response)

        return state
