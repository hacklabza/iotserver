import json

import paho.mqtt.client as mqtt
from django.conf import settings
from django.core.management.base import BaseCommand

from iotserver.apps.device.models import Device, DeviceStatus


class Command(BaseCommand):
    help = 'Run the mqtt client for devices.'

    def mqtt_on_connect(self, client, userdata, flags, result_code):
        client.subscribe('iot-devices/#')

    def mqtt_on_message(self, client, userdata, message):
        self.stdout.write(self.style.SUCCESS(f'{message.topic}: {message.payload}'))
        if 'status' in message.topic:
            self.handle_status_queue(message)

    def handle(self, *args, **options):
        client = mqtt.Client()
        client.on_connect = self.mqtt_on_connect
        client.on_message = self.mqtt_on_message

        client.connect(host=settings.MQTT['host'], port=settings.MQTT['port'])

        client.loop_forever()

        self.stdout.write(self.style.SUCCESS('MQTT Client started...'))

    def handle_status_queue(self, message):
        device_id = message.topic.split('/')[1]
        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Device with id: {device_id} does not exist. Ignoring.'
                )
            )
            return
        device_status = DeviceStatus.objects.create(
            device=device, status=json.loads(message.payload)
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Status message received for {device_status.device_id} and processed.'
            )
        )
