import hashlib
import json
import logging
import threading

import paho.mqtt.client as mqtt
import requests
from django.utils import timezone

from iotserver.apps.device.integrations.sonoff import Sonoff

logger = logging.getLogger(__name__)

# Ordering (not alphabetical) matches the IoTDevice firmware's LOG_LEVELS so the
# same `logging.level` config value has the same meaning on both sides.
LOG_LEVELS = ['info', 'debug', 'warning', 'error']

CONDITION_OPERATORS = {
    'eq': lambda input, value: input == value,
    'gt': lambda input, value: input > value,
    'lt': lambda input, value: input < value,
}


def find_xpath_value(response, xpaths):
    """
    Recursively finds a value in a nested dict/list structure based on a list of
    xpaths. `xpaths` must be reversed before being passed in.
    """
    xpath = xpaths.pop()

    try:
        response = response[xpath]
    except (KeyError, IndexError, TypeError):
        return None

    if not xpaths:
        return response

    return find_xpath_value(response, xpaths)


def evaluate_condition(input, operator, value):
    """
    Evaluates a condition and returns a boolean.
    """
    try:
        return CONDITION_OPERATORS[operator](input, value)
    except TypeError:
        return False


def handle_conditions(rule_values, input_value):
    """
    Returns a dict of `must`/`should` condition boolean lists to be evaluated.
    """
    condition_values = {'must': [], 'should': []}
    for condition_type, conditions in input_value['conditions'].items():
        if condition_type in condition_values:
            for pin_identifier, condition in conditions.items():
                xpaths = pin_identifier.split('.')
                xpaths.reverse()
                condition_values[condition_type].append(
                    evaluate_condition(
                        find_xpath_value(rule_values, xpaths), **condition
                    )
                )

    return condition_values


def value_to_bool(value):
    """
    Converts a string, int, bool, or None to a boolean.
    """
    if isinstance(value, str):
        return value.strip().lower() in ['true', '1', 'yes', 'on']
    return bool(value)


def timer(**kwargs):
    """
    Checks if the current local time is within a start/end time range, handling
    ranges which span midnight (e.g. 18:00 - 05:00).
    """
    now = timezone.localtime().strftime('%H%M')
    start = kwargs.get('start_time').replace(':', '')
    end = kwargs.get('end_time').replace(':', '')

    if start <= end:
        return start <= now <= end
    return now >= start or now <= end


def service(**kwargs):
    """
    Calls a web service and returns its JSON response.
    """
    url = kwargs.get('url')
    auth_header = kwargs.get('auth_header')
    headers = {'Authorization': f'Token {auth_header}'} if auth_header else None

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def mqtt_toggle(**kwargs):
    """
    Reads the latest retained MQTT message received for `topic` by the device
    worker's MQTT client and returns it as a boolean.
    """
    topic = kwargs.get('topic')
    mqtt_values = kwargs.get('mqtt_values', {})
    return value_to_bool(mqtt_values.get(topic))


def sonoff_toggle(**kwargs):
    """
    Toggles a Sonoff cloud device on/off via the eWeLink/Coolkit API.
    """
    on = kwargs.get('on')
    device_id = kwargs.get('device_id')
    state = Sonoff(device_id).toggle_device('on' if on else 'off')
    return value_to_bool(state)


# Explicit whitelist of callable rule actions, rather than `getattr` on this
# module, so `rule['action']` (data, not code) can't invoke arbitrary attributes.
RULE_ACTIONS = {
    'timer': timer,
    'service': service,
    'mqtt_toggle': mqtt_toggle,
    'sonoff_toggle': sonoff_toggle,
}


def _build_mqtt_client(mqtt_config, on_connect, on_message):
    """
    Builds, connects, and starts the network loop for a device's persistent MQTT
    client.
    """
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_config['client_id']
    )
    client.on_connect = on_connect
    client.on_message = on_message

    username = mqtt_config.get('username')
    if username:
        client.username_pw_set(username, mqtt_config.get('password'))

    if mqtt_config.get('ssl_enabled'):
        client.tls_set()

    lastwill = mqtt_config.get('lastwill')
    if lastwill:
        client.will_set(topic=lastwill['topic'], payload=lastwill['message'])

    client.connect(host=mqtt_config['host'], port=mqtt_config.get('port', 1883))
    client.loop_start()

    return client


def _resolve_rule_params(rule, rule_values, mqtt_values):
    """
    Resolves a rule's `input` into keyword arguments, evaluating any must/should
    conditions against previously collected rule values.
    """
    rule_params = {}
    for key, value in rule['input'].items():
        if isinstance(value, dict) and 'conditions' in value:
            condition_values = handle_conditions(rule_values, value)
            rule_params[key] = any(
                [all(condition_values['must']), any(condition_values['should'])]
            )
        else:
            rule_params[key] = value

    if rule['action'] == 'mqtt_toggle':
        rule_params['mqtt_values'] = mqtt_values

    return rule_params


def _publish_status(client, device_id, rule_values, previous_status_hash):
    """
    Publishes the current rule values as the device status if they've changed
    since the last publish, returning the new dedup hash.
    """
    payload = json.dumps(rule_values, sort_keys=True)
    status_hash = hashlib.sha1(payload.encode()).digest()

    if status_hash != previous_status_hash:
        client.publish(f'iot-devices/{device_id}/status', payload)

    return status_hash


def _publish_log(client, device_id, logging_config, level, message):
    """
    Logs locally and, if the configured logging level permits it, publishes the
    message to the device's log topic for ingestion by the `mqtt` command.
    """
    getattr(logger, level, logger.info)(message)

    threshold = logging_config.get('level', 'warning')
    if LOG_LEVELS.index(level) >= LOG_LEVELS.index(threshold):
        client.publish(f'iot-devices/{device_id}/logs', message)


def run_device(device, stop_event: threading.Event) -> None:
    """
    Runs the rules engine loop for a single non-managed-firmware device until
    `stop_event` is set. Mirrors the IoTDevice firmware's main loop, but drives
    the device over HTTP/MQTT (via its own config) instead of local GPIO pins.
    """
    config = device.full_config
    device_id = str(device.id)

    mqtt_values = {}
    mqtt_topics = [
        pin['rule']['input']['topic']
        for pin in config['pins']
        if pin['rule']['action'] == 'mqtt_toggle'
    ]

    def on_connect(client, userdata, connect_flags, reason_code, properties):
        for topic in mqtt_topics:
            client.subscribe(topic)

    def on_message(client, userdata, message):
        mqtt_values[message.topic] = message.payload.decode('utf-8')

    client = _build_mqtt_client(config['mqtt'], on_connect, on_message)

    rule_values = {}
    previous_status_hash = None
    run_count = 0

    try:
        while not stop_event.is_set():
            try:
                requests.get(config['health']['url'], timeout=10)

                for pin in config['pins']:
                    if run_count % pin.get('interval', 1):
                        continue

                    rule = pin['rule']
                    rule_params = _resolve_rule_params(rule, rule_values, mqtt_values)
                    rule_values[pin['identifier']] = RULE_ACTIONS[rule['action']](
                        **rule_params
                    )

                previous_status_hash = _publish_status(
                    client, device_id, rule_values, previous_status_hash
                )
            except Exception:
                logger.exception('Error running rules for device %s', device_id)
                _publish_log(
                    client,
                    device_id,
                    config['logging'],
                    'error',
                    f'Error running rules for device {device_id}',
                )

            run_count += 1
            stop_event.wait(config['main']['process_interval'])
    finally:
        client.loop_stop()
        client.disconnect()
