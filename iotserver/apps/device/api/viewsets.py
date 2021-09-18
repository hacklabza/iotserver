from rest_framework import viewsets

from iotserver.apps.device import models
from iotserver.apps.device.api import serializers


class DeviceTypeViewSet(viewsets.ModelViewSet):
    queryset = models.DeviceType.objects.all()
    serializer_class = serializers.DeviceTypeSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = models.Device.objects.all()
    serializer_class = serializers.DeviceSerializer


class LocationViewSet(viewsets.ModelViewSet):
    queryset = models.Location.objects.all()
    serializer_class = serializers.LocationSerializer
