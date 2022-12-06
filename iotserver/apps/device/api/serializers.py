from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from iotserver.apps.device import models


class LocationSerializer(gis_serializers.GeoModelSerializer):
    class Meta:
        model = models.Location
        geo_field = 'position'
        fields = '__all__'


class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DeviceType
        fields = '__all__'


class DevicePinSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DevicePin
        fields = '__all__'


class DeviceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DeviceStatus
        fields = '__all__'


class DeviceHealthSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = models.DeviceHealth
        fields = '__all__'

    def get_status(self, instance):
        return instance.status


class DeviceSerializer(serializers.ModelSerializer):
    type = DeviceTypeSerializer(many=False, read_only=True)
    location = LocationSerializer(many=False)
    pins = DevicePinSerializer(many=True, read_only=True)
    last_status = serializers.SerializerMethodField()
    health = serializers.SerializerMethodField()

    class Meta:
        model = models.Device
        fields = '__all__'
        lookup_field = 'id'

    def get_last_status(self, instance):
        return DeviceStatusSerializer(instance.statuses.last()).data

    def get_health(self, instance):
        return DeviceHealthSerializer(instance.health).data
