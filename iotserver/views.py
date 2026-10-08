from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.request import Request
from rest_framework.response import Response

from iotserver.apps.device.models import DeviceHealth


@api_view(['GET', 'POST'])
@authentication_classes([])
@permission_classes([])
def health(request: Request, device_pk: int = None):
    wifi_signal_strength = request.data.get('wifi_signal_strength')
    battery_level = request.data.get('battery_level')

    if device_pk is not None:
        device_health, created = DeviceHealth.objects.get_or_create(
            device_id=device_pk,
            defaults={
                'wifi_signal_strength': wifi_signal_strength,
                'battery_level': battery_level,
            },
        )
        if not created:
            device_health.wifi_signal_strength = wifi_signal_strength
            device_health.battery_level = battery_level
            device_health.save()

    return Response({'status': 'ok'})
