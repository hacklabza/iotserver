import paho.mqtt.subscribe as mqtt_subscribe
import paho.mqtt.publish as mqtt_publish


def toggle(device_id, mqtt_settings):
    """
    Toggle the device on/off via mqtt if the rule has been applied to one of it's 
    pins.
    """
    topic = f'iot-devices/{device_id}/toggle'

    # Check the current toggle state
    mqtt_state = mqtt_subscribe.simple(
        topic,
        hostname=mqtt_settings['host'],
        port=mqtt_settings['port']
    )
    state = '1' if mqtt_state == '0' else '0'
    
    # Switch to the new toggle state
    mqtt_publish.single(
        topic, 
        state, 
        hostname=mqtt_settings['host'],
        port=mqtt_settings['port'], 
        retain=True
    )