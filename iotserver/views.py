from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def health(request, device_pk=None):
    return Response({'status': 'ok'})
