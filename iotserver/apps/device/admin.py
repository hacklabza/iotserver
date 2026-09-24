from django.contrib import admin, messages
from django.contrib.gis.db import models as gis_models
from django.db.models import JSONField
from django.utils.safestring import mark_safe
from mapwidgets.widgets import GoogleMapPointFieldWidget

from iotserver.apps.device import exceptions, models, widgets


def toggle_devices_on(modeladmin, request, queryset):
    for obj in queryset:
        obj.mqtt_toggle('on')

    message = 'All selected device have been toggled on.'
    messages.add_message(request, level=messages.SUCCESS, message=message)


def toggle_devices_off(modeladmin, request, queryset):
    for obj in queryset:
        obj.mqtt_toggle('off')

    message = 'All selected device have been toggled off.'
    messages.add_message(request, level=messages.SUCCESS, message=message)


@admin.register(models.DeviceType)
class DeviceTypeModelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'identifier': ('name',)}


@admin.register(models.Device)
class DeviceModelAdmin(admin.ModelAdmin):
    actions = [toggle_devices_on, toggle_devices_off]
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'active',
                    'managed_firmware',
                    'name',
                    'description',
                    'type',
                    'location',
                )
            },
        ),
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
        'managed_firmware',
        'created_at',
        'type',
        'location',
        'ip_address',
    )
    list_filter = ('active', 'managed_firmware', 'type__name', 'location__name')
    formfield_overrides = {
        JSONField: {'widget': widgets.PrettyJSONWidget(attrs={'rows': 20, 'cols': 120})}
    }

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except exceptions.DeviceUnreachableError as error:
            messages.add_message(request, level=messages.WARNING, message=str(error))


@admin.register(models.DevicePinType)
class DevicePinTypeModelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'identifier': ('name',)}


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
    list_filter = ('devices__name', 'active')
    prepopulated_fields = {'identifier': ('name',)}
    formfield_overrides = {
        JSONField: {'widget': widgets.PrettyJSONWidget(attrs={'rows': 20, 'cols': 120})}
    }


@admin.register(models.DeviceStatus)
class DeviceStatusModelAdmin(admin.ModelAdmin):
    list_display = ('device', 'created_at')
    list_filter = ('device__name', 'created_at')
    formfield_overrides = {
        JSONField: {'widget': widgets.PrettyJSONWidget(attrs={'rows': 20, 'cols': 120})}
    }


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
    formfield_overrides = {gis_models.PointField: {'widget': GoogleMapPointFieldWidget}}
    list_display = ('name', 'position')


@admin.register(models.SonoffToken)
class SonoffTokenModelAdmin(admin.ModelAdmin):
    """Read-only view of the OAuth token; connect via /integrations/sonoff/authorize/."""

    list_display = (
        'region',
        'access_token_expires_at',
        'refresh_token_expires_at',
        'updated_at',
    )
    readonly_fields = (
        'access_token',
        'refresh_token',
        'access_token_expires_at',
        'refresh_token_expires_at',
        'region',
        'updated_at',
    )

    def has_add_permission(self, request):
        return False
