from django.apps import AppConfig


class DeviceConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'iotserver.apps.device'
    verbose_name = 'Devices'
