import uuid

from django.contrib.gis.db import models as gis_models
from django.db import models


class Location(models.Model):
    name = models.CharField(max_length=32)
    coordinates = gis_models.PointField()

    def __str__(self):
        return self.name


class DeviceType(models.Model):
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    active = models.BooleanField(default=False)

    name = models.CharField(max_length=128)
    description = models.CharField(max_length=1024)

    type = models.ForeignKey(DeviceType, on_delete=models.SET_NULL, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)

    ip_address = models.GenericIPAddressField(null=True)
    mac_address = models.CharField(max_length=48)
    hostname = models.CharField(max_length=64)

    config = models.JSONField(null=True)

    def __str__(self):
        return self.name
