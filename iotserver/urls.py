from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken import views

from iotserver.apps.device.api import viewsets as device_viewsets
from iotserver.apps.user.api import viewsets as user_viewsets

router = routers.DefaultRouter()
router.register('devices/locations', device_viewsets.LocationViewSet)
router.register('devices/types', device_viewsets.DeviceTypeViewSet)
router.register('devices', device_viewsets.DeviceViewSet)
router.register('users', user_viewsets.UserViewSet)


# Built-in url patterns
urlpatterns = [
    path('admin/', admin.site.urls),
]


# DRF url patterns
urlpatterns += [
    path('api/auth/token', views.obtain_auth_token),
    path('api/auth/', include('rest_framework.urls')),
    path('api/', include(router.urls)),
]
