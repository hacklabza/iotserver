import requests
from django.utils import timezone

from iotserver.apps.device.integrations.sonoff import Sonoff

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
