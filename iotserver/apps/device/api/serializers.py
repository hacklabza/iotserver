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
    devices = serializers.PrimaryKeyRelatedField(
        many=True, queryset=models.Device.objects.all()
    )

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


class DeviceListDetailSerializer(serializers.ModelSerializer):
    type = DeviceTypeSerializer(many=False, read_only=True)
    location = LocationSerializer(many=False, read_only=True)
    pins = DevicePinSerializer(many=True, read_only=True)
    last_status = serializers.SerializerMethodField()
    health = serializers.SerializerMethodField()

    class Meta:
        model = models.Device
        fields = '__all__'
        lookup_field = 'id'

    def get_last_status(self, instance):
        if instance.last_status:
            return DeviceStatusSerializer(instance.last_status).data

    def get_health(self, instance):
        try:
            return DeviceHealthSerializer(instance.health).data
        except models.Device.health.RelatedObjectDoesNotExist:
            return None


class DeviceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Device
        fields = '__all__'
        lookup_field = 'id'
