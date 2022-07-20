import json
from datetime import datetime

import paho.mqtt.client as mqtt
from django.conf import settings
from django.core.management.base import BaseCommand

from iotserver.apps.device.models import Device, DeviceStatus


class Command(BaseCommand):
    help = 'Run the mqtt client for devices.'

    def mqtt_on_connect(self, client, userdata, flags, result_code):
        client.subscribe('iot-devices/#')

    def mqtt_on_message(self, client, userdata, message):
        if 'status' in message.topic:
            self.handle_status_queue(message)
        if 'logs' in message.topic:
            self.handle_log_queue(message)

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
        timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
        self.stdout.write(
            self.style.SUCCESS(
                f'[{timestamp}] Status message received for {device_status.device_id} and processed.'
            )
        )

    def handle_log_queue(self, message):
        device_id = message.topic.split('/')[1]
        timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
        self.stdout.write(
            self.style.WARNING(
                f'[{timestamp}] Log received for {device_id} with message: "{message.payload}"'
            )
        )
