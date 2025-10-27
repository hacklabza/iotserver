from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response

from iotserver.apps.device.models import DeviceHealth


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def health(request, device_pk=None):
    if device_pk is not None:
        device_health, created = DeviceHealth.objects.get_or_create(device_id=device_pk)
        if not created:
            device_health.save()

    return Response({'status': 'ok'})
