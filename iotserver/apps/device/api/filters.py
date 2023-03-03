from django_filters import rest_framework as filters

from iotserver.apps.device import models


class DeviceStatusFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = filters.DateFilter(field_name="created_at", lookup_expr='lte')
    created_at = filters.DateFilter(field_name="created_at", lookup_expr='date')

    class Meta:
        model = models.DeviceStatus
        fields = ['device']
