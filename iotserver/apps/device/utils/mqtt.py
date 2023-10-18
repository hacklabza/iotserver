from typing import Dict, Optional

import paho.mqtt.subscribe as mqtt_subscribe
import paho.mqtt.publish as mqtt_publish
from django.conf import settings


def toggle(device_id: str, state: int, mqtt_settings: Optional[Dict] = None) -> None:
    """
    Toggle the device on/off via mqtt if the rule has been applied to one of it's 
    pins.
    """
    topic = f'iot-devices/{device_id}/toggle'
    mqtt_settings = mqtt_settings or settings.MQTT
    
    # Switch to the new toggle state
    mqtt_publish.single(
        topic, 
        state, 
        hostname=mqtt_settings['host'],
        port=mqtt_settings['port'], 
        retain=True
    )