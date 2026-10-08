from django.db.models import F
from django_filters import rest_framework as filters

from iotserver.apps.device import models


class DeviceStatusFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(
        field_name='created_at', lookup_expr='gte'
    )
    end_date = filters.DateTimeFilter(
        field_name="created_at", lookup_expr='lte'
    )
    created_at = filters.DateFilter(field_name="created_at", lookup_expr='date')
    sample_size = filters.NumberFilter(method='filter_sample_size')

    def filter_sample_size(self, queryset, name, value):
        if value is not None:
            queryset = queryset.annotate(idmod4=F('id') % int(value)).filter(
                idmod4=0
            )
        return queryset

    class Meta:
        model = models.DeviceStatus
        fields = ['device']
