from typing import Dict, List, Optional

import requests
from django.conf import settings

ALARM_EVENT_STATES = {'alarm', 'fire', 'emergency'}


class Olarm(object):
    """Simple Olarm integration class which returns events for the configured
    Olarm device and whether the alarm is currently activated (triggered).
    """

    def __init__(self) -> None:
        self.config = settings.INTEGRATIONS['olarm']
        self.device_id = self.config['device_id']

    @property
    def events(self) -> List[Dict]:
        response = requests.get(
            url=f"{self.config['base_url']}/api/v4/devices/{self.device_id}/events",
            headers={'Authorization': f"Bearer {self.config['api_key']}"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get('data', [])

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
        return event.get('eventState') in ALARM_EVENT_STATES
