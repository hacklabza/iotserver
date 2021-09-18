from rest_framework import serializers

from iotserver.apps.device import models


class DeviceTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.DeviceType
        fields = '__all__'


class DeviceSerializer(serializers.HyperlinkedModelSerializer):
    device_type = serializers.HyperlinkedRelatedField(
        many=False, read_only=True, view_name='devicetype-detail'
    )
    location = serializers.HyperlinkedRelatedField(
        many=False, read_only=True, view_name='location-detail'
    )

    class Meta:
        model = models.Device
        fields = '__all__'
        lookup_field = 'id'


class LocationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Location
        fields = '__all__'
