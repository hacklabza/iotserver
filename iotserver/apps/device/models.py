import uuid

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property


class Location(models.Model):
    name = models.CharField(max_length=32)
    position = gis_models.PointField()

    def __str__(self):
        return self.name

    @cached_property
    def resource_url(self):
        return reverse('location-detail', kwargs={'pk': self.pk})


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

    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=48)
    hostname = models.CharField(max_length=64)

    config = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name

    @cached_property
    def resource_url(self):
        return reverse('device-detail', kwargs={'pk': str(self.id)})


class DevicePin(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='pins')

    name = models.CharField(max_length=32)
    identifier = models.SlugField(max_length=64)
    pin_number = models.PositiveSmallIntegerField(blank=True, null=True)

    analog = models.BooleanField(default=False)
    read = models.BooleanField(default=False)

    rule = models.JSONField(null=False)

    def __str__(self):
        return self.name

    @cached_property
    def resource_url(self):
        return reverse('devicepin-detail', kwargs={'pk': self.pk})


class DeviceStatus(models.Model):
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name='statuses'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    status = models.JSONField(null=False)

    class Meta:
        verbose_name_plural = 'Device Statuses'

    def __str__(self):
        return self.device.name

    @cached_property
    def resource_url(self):
        return reverse('devicestatus-detail', kwargs={'pk': self.pk})
