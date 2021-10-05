import factory.fuzzy
from django.contrib.gis.geos import Point

from iotserver.apps.device import models


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Location

    name = factory.fuzzy.FuzzyText(length=12)
    position = Point((-26.13946, 28.36402))


class DeviceTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DeviceType

    name = factory.fuzzy.FuzzyText(length=12)


class DeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Device

    active = True
    name = factory.fuzzy.FuzzyText(length=12)
    description = factory.fuzzy.FuzzyText(length=48)
    type = factory.SubFactory(DeviceTypeFactory)
    location = factory.SubFactory(LocationFactory)

    ip_address = '192.168.0.1'
    mac_address = '0E:00:20:01:71:AE'
    hostname = 'test-device'

    config = {}


class DeviceStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DeviceStatus

    device = factory.SubFactory(DeviceFactory)
    status = {}
