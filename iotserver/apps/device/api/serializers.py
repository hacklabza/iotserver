from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from iotserver.apps.device import models


class LocationSerializer(gis_serializers.GeoModelSerializer):
    class Meta:
        model = models.Location
        geo_field = 'position'
        fields = '__all__'


class DeviceTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.DeviceType
        fields = '__all__'


class DeviceSerializer(serializers.HyperlinkedModelSerializer):
    device_type = serializers.HyperlinkedRelatedField(
        many=False, read_only=True, view_name='devicetype-detail'
    )
    location = serializers.HyperlinkedRelatedField(
        many=False, view_name='location-detail', queryset=models.Location.objects.all()
    )
    pins = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name='devicepin-detail'
    )
    statuses = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name='devicestatus-detail'
    )

    class Meta:
        model = models.Device
        fields = '__all__'
        lookup_field = 'id'


class DevicePinSerializer(serializers.HyperlinkedModelSerializer):
    device = serializers.HyperlinkedRelatedField(
        many=False, view_name='device-detail', queryset=models.Device.objects.all()
    )
    identifier = serializers.SerializerMethodField()

    class Meta:
        model = models.DevicePin
        fields = '__all__'

    def get_identifier(self, instance):
        return slugify(instance.name)


class DeviceStatusSerializer(serializers.HyperlinkedModelSerializer):
    device = serializers.HyperlinkedRelatedField(
        many=False, read_only=True, view_name='device-detail'
    )

    class Meta:
        model = models.DeviceStatus
        fields = '__all__'
