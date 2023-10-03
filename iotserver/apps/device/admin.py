from django.contrib import admin, messages
from django.contrib.gis.db import models as gis_models
from django.utils.safestring import mark_safe
from mapwidgets.widgets import GooglePointFieldWidget

from iotserver.apps.device import models


def toggle_device(modeladmin, request, queryset):
    for obj in queryset:
        obj.mqtt_toggle()

    message = 'All selected device have been toggled on/off.'
    messages.add_message(request, level=messages.SUCCESS, message=message)


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
        (
            'Device config',
            {
                'classes': ('collapse',),
                'fields': ('config',),
            },
        ),
    )
    list_display = (
        'name',
        'description',
        'active',
        'created_at',
        'type',
        'location',
        'ip_address',
    )
    list_filter = ('active', 'type__name', 'location__name')
    actions = [toggle_device]


@admin.register(models.DevicePin)
class DevicePinModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'identifier',
        'pin_number',
        'analog',
        'read',
        'i2c',
        'active',
    )
    list_filter = ('device__name', 'active')
    prepopulated_fields = {'identifier': ('name',)}


@admin.register(models.DeviceStatus)
class DeviceStatusModelAdmin(admin.ModelAdmin):
    list_display = ('device', 'created_at')
    list_filter = ('device__name', 'created_at')


@admin.register(models.DeviceHealth)
class DeviceHealthModelAdmin(admin.ModelAdmin):
    list_display = ('device', 'updated_at', 'status')
    list_filter = ('device__name', 'updated_at')

    def status(self, obj):
        if obj.status:
            return mark_safe('<img src="/static/admin/img/icon-yes.svg" alt="True">')
        return mark_safe('<img src="/static/admin/img/icon-no.svg" alt="False">')

    status.short_description = "Status"


@admin.register(models.Location)
class LocationModelAdmin(admin.ModelAdmin):
    formfield_overrides = {gis_models.PointField: {'widget': GooglePointFieldWidget}}
    list_display = ('name', 'position')
