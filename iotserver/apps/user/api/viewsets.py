from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.authtoken import views
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from iotserver.apps.user.api import serializers


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer


class ObtainAuthTokenUser(views.ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return Response({'token': token.key, 'user_id': token.user_id})
