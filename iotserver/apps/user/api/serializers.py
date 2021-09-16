from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    full_name = serializers.SerializerMethodField('get_full_name')

    class Meta:
        model = get_user_model()
        fields = ['url', 'username', 'email', 'full_name', 'is_active']

    def get_full_name(self, obj):
        return obj.get_full_name()
