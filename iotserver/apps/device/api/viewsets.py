from django.db.models import F
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from iotserver.apps.device import models
from iotserver.apps.device.api import filters, serializers
from iotserver.apps.device.integrations.weather import Location, Weather


class SampleSizeMixin(object):
    """
    Only returns a smaple of the data in the query set based on the query
    param: `sample_size`
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        sample_size = self.request.query_params.get('sample_size')
        if sample_size is not None:
            queryset = queryset.annotate(idmod4=F('id') % int(sample_size)).filter(
                idmod4=0
            )
        return queryset


class DeviceTypeViewSet(viewsets.ModelViewSet):
    queryset = models.DeviceType.objects.all()
    serializer_class = serializers.DeviceTypeSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = models.Device.objects.all()
    serializer_class = serializers.DeviceSerializer
    filterset_fields = ['type', 'active']

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        try:
            device = self.get_object()
        except models.Device.DoesNotExist:
            return Response(
                data={'error': 'Device does not exist'},
                status=status.HTTP_404_NOT_FOUND,
            )
        state = request.data.get('state')
        if state is None or state not in [0, 1]:
            return Response(
                data={'error': 'Device state must either be 1 or 0'},
                status=status.HTTP_404_NOT_FOUND,
            )
        device.mqtt_toggle(state)
        return Response(status=status.HTTP_202_ACCEPTED)


class DevicePinViewSet(viewsets.ModelViewSet):
    queryset = models.DevicePin.objects.all()
    serializer_class = serializers.DevicePinSerializer
    filterset_fields = ['device', 'active']


class DeviceStatusViewSet(SampleSizeMixin, viewsets.ModelViewSet):
    queryset = models.DeviceStatus.objects.all()
    serializer_class = serializers.DeviceStatusSerializer
    filterset_class = filters.DeviceStatusFilter
    ordering_fields = ['created_at']
    ordering = ['created_at']


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
