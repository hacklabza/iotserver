import paho.mqtt.subscribe as mqtt_subscribe
import paho.mqtt.publish as mqtt_publish


def toggle(device_id, state, mqtt_settings):
    """
    Toggle the device on/off via mqtt if the rule has been applied to one of it's 
    pins.
    """
    topic = f'iot-devices/{device_id}/toggle'
    
    # Switch to the new toggle state
    mqtt_publish.single(
        topic, 
        state, 
        hostname=mqtt_settings['host'],
        port=mqtt_settings['port'], 
        retain=True
    )