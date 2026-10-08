from typing import Dict, List, Optional

import requests
from django.conf import settings
from django.core.cache import cache

ACTIVE_ALARM_EVENT_STATES = {'alarm', 'fire', 'emergency'}
DEACTIVATED_ALARM_EVENT_STATES = {'disarmed'}


class Olarm(object):
    """Simple Olarm integration class which returns events for the configured
    Olarm device and whether the alarm is currently activated (triggered).
    """

    def __init__(self, cache_timeout: int = None) -> None:
        self.config = settings.INTEGRATIONS['olarm']
        self.device_id = self.config['device_id']
        self.cache_prefix = f'{self.__module__}.{self.__class__.__name__}'
        self.cache_timeout = cache_timeout or self.config['cache_timeout']

    @property
    def events(self) -> List[Dict]:
        cache_key = f'{self.cache_prefix}.events:{self.device_id}'
        cached_events = cache.get(cache_key)
        if cached_events is not None:
            return cached_events

        response = requests.get(
            url=f"{self.config['base_url']}/api/v4/devices/{self.device_id}/events",
            headers={'Authorization': f"Bearer {self.config['api_key']}"},
            timeout=10,
        )
        response.raise_for_status()
        events = response.json().get('data', [])

        cache.set(cache_key, events, timeout=self.cache_timeout)
        return events

    @property
    def latest_event(self) -> Optional[Dict]:
        """Return the latest area event, zone/device events don't reflect alarms."""
        area_events = [
            event for event in self.events if event.get('eventAction') == 'area'
        ]
        if not area_events:
            return None
        return max(area_events, key=lambda event: event.get('eventTime', 0))

    @property
    def activated(self) -> bool:
        event = self.latest_event
        if event is None:
            return False
        if event.get('eventState') in DEACTIVATED_ALARM_EVENT_STATES:
            return False
        return event.get('eventState') in ACTIVE_ALARM_EVENT_STATES
