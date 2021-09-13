from django.contrib import admin

from iotserver.apps.device import models


@admin.register(models.DeviceType)
class DeviceTypeModelAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.Device)
class DeviceModelAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('active', 'name', 'description', 'type', 'location')}),
        (
            'Advanced options',
            {
                'classes': ('collapse',),
                'fields': ('ip_address', 'mac_address', 'hostname'),
            },
        ),
    )
    list_display = ('name', 'description', 'active', 'type', 'location', 'ip_address')
    list_filter = ('active', 'type__name', 'location__name')


@admin.register(models.Location)
class LocationModelAdmin(admin.ModelAdmin):
    list_display = ('name', '')
