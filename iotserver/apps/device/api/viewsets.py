from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from iotserver.apps.device import models
from iotserver.apps.device.api import serializers
from iotserver.apps.device.integrations.weather import Location, Weather


class DeviceTypeViewSet(viewsets.ModelViewSet):
    queryset = models.DeviceType.objects.all()
    serializer_class = serializers.DeviceTypeSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = models.Device.objects.all()
    serializer_class = serializers.DeviceSerializer
    filterset_fields = ['type', 'active']


class DevicePinViewSet(viewsets.ModelViewSet):
    queryset = models.DevicePin.objects.all()
    serializer_class = serializers.DevicePinSerializer
    filterset_fields = ['device', 'active']


class DeviceStatusViewSet(viewsets.ModelViewSet):
    queryset = models.DeviceStatus.objects.all()
    serializer_class = serializers.DeviceStatusSerializer
    filterset_fields = ['device']


class DeviceHealthViewSet(viewsets.ModelViewSet):
    queryset = models.DeviceHealth.objects.all()
    serializer_class = serializers.DeviceHealthSerializer
    filterset_fields = ['device']


class LocationViewSet(viewsets.ModelViewSet):
    queryset = models.Location.objects.all()
    serializer_class = serializers.LocationSerializer
    filterset_fields = ['device']

    @action(detail=True, methods=['get'])
    def weather(self, request, pk=None):
        forecast_type = self.request.query_params.get('type', 'current')

        location = self.get_object()
        weather_location = Location(
            latitude=location.coordinates['latitude'],
            longitude=location.coordinates['longitude'],
        )
        weather = Weather(location=weather_location)

        try:
            return Response(data=getattr(weather, forecast_type))
        except AttributeError:
            return Response(
                data={'error': 'Incorrect forecast type'},
                status=status.HTTP_400_BAD_REQUEST,
            )
