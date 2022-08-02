from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from iotserver.apps.device.api import viewsets as device_viewsets
from iotserver.apps.user.api import viewsets as user_viewsets
from iotserver.views import health

router = routers.DefaultRouter()


# Device endpoints
router.register('devices/locations', device_viewsets.LocationViewSet)
router.register('devices/health', device_viewsets.DeviceHealthViewSet)
router.register('devices/types', device_viewsets.DeviceTypeViewSet)
router.register('devices/pins', device_viewsets.DevicePinViewSet)
router.register('devices/statuses', device_viewsets.DeviceStatusViewSet)
router.register('devices', device_viewsets.DeviceViewSet)

# User endpoints
router.register('users', user_viewsets.UserViewSet)

# Health endpoint
urlpatterns = [
    path('health/<str:device_pk>/', health),
    path('health/', health),
]

# Built-in url patterns
urlpatterns += [
    path('admin/', admin.site.urls),
]


# DRF url patterns
urlpatterns += [
    path('api/auth/token/', user_viewsets.ObtainAuthTokenUser.as_view()),
    path('api/auth/', include('rest_framework.urls')),
    path('api/', include(router.urls)),
]

# Static files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
