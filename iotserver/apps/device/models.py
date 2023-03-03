import json
import uuid

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from iotserver.apps.device.utils import webrepl


class Location(models.Model):
    name = models.CharField(max_length=32)
    position = gis_models.PointField()

    def __str__(self):
        return self.name

    @cached_property
    def resource_url(self):
        return reverse('location-detail', kwargs={'pk': self.pk})

    @cached_property
    def coordinates(self):
        return {
            'latitude': self.position.y,
            'longitude': self.position.x,
        }


class DeviceType(models.Model):
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name

    @cached_property
    def resource_url(self):
        return reverse('devicetype-detail', kwargs={'pk': self.pk})


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    active = models.BooleanField(default=False)

    name = models.CharField(max_length=128)
    description = models.CharField(max_length=1024)

    type = models.ForeignKey(
        DeviceType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='devices',
    )
    location = models.OneToOneField(
        Location, on_delete=models.SET_NULL, blank=True, null=True
    )

    ip_address = models.GenericIPAddressField(unique=True)
    mac_address = models.CharField(max_length=48, unique=True)
    hostname = models.CharField(max_length=64, blank=True, null=True)

    config = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name

    @cached_property
    def resource_url(self):
        return reverse('device-detail', kwargs={'pk': str(self.id)})

    @cached_property
    def full_config(self):
        config = self.config
        config['pins'] = [
            pin.config for pin in self.pins.filter(active=True).order_by('-pin_number')
        ]
        return config


class DevicePin(models.Model):
    active = models.BooleanField(default=True)

    device = models.ManyToManyField(Device, related_name='pins')

    name = models.CharField(max_length=32)
    identifier = models.SlugField(max_length=64, unique=True)
    pin_number = models.PositiveSmallIntegerField(blank=True, null=True)

    interval = models.IntegerField(default=1)
    analog = models.BooleanField(default=False)
    read = models.BooleanField(default=False)

    rule = models.JSONField(null=False)

    def __str__(self):
        return self.name

    @cached_property
    def resource_url(self):
        return reverse('devicepin-detail', kwargs={'pk': self.pk})

    @cached_property
    def config(self):
        return {
            'pin_number': self.pin_number,
            'name': self.name,
            'identifier': self.identifier,
            'interval': self.interval,
            'analog': self.analog,
            'read': self.read,
            'rule': self.rule,
        }


class DeviceStatus(models.Model):
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name='statuses'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    status = models.JSONField(null=False)

    class Meta:
        verbose_name_plural = 'Device Statuses'
        ordering = ['-created_at']

    def __str__(self):
        return self.device.name

    @cached_property
    def resource_url(self):
        return reverse('devicestatus-detail', kwargs={'pk': self.pk})


class DeviceHealth(models.Model):
    device = models.OneToOneField(
        Device, on_delete=models.CASCADE, related_name='health'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Device Health'

    def __str__(self):
        return self.device.name

    @cached_property
    def resource_url(self):
        return reverse('devicehealth-detail', kwargs={'pk': self.pk})

    @cached_property
    def status(self):
        return self.updated_at > timezone.now() - timezone.timedelta(minutes=1)


@receiver(pre_save, sender=Device)
def handle_device_default_config(sender, instance, *args, **kwargs):
    """Get the config from the new device and update the config field."""
    if settings.AUTO_SYNC_DEVICE:
        if instance.config is None:
            temp_file_path = f'/tmp/config.{instance.id}.json'
            with open(temp_file_path, 'w') as input_file:
                input_file.write('')

            _socket, web_socket = webrepl.get_websocket(
                instance.ip_address, settings.WEBREPL_PORT, settings.WEBREPL_PASSWORD
            )
            webrepl.get_file(web_socket, temp_file_path, 'config/config.json')
            _socket.close()

            with open(temp_file_path, 'r') as input_file:
                device_config = json.loads(input_file.read())

                device_id = str(instance.id)
                device_config['main']['identifier'] = device_id

                # Ignore the pin config
                del device_config['pins']

                instance.config = device_config


@receiver(post_save, sender=Device)
def handle_device_config_update(sender, instance, *args, **kwargs):
    """Update config on the physical device via webrepl."""
    if settings.AUTO_SYNC_DEVICE:
        temp_file_path = f'/tmp/config.{instance.id}.json'
        with open(temp_file_path, 'w') as input_file:
            input_file.write(json.dumps(instance.full_config, indent=4))

        _socket, web_socket = webrepl.get_websocket(
            instance.ip_address, settings.WEBREPL_PORT, settings.WEBREPL_PASSWORD
        )
        webrepl.put_file(web_socket, temp_file_path, 'config/config.json')
        _socket.close()
