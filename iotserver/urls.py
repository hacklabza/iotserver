from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from iotserver.apps.user.api import viewsets as user_viewsets

router = routers.DefaultRouter()
router.register('users', user_viewsets.UserViewSet)


# Built-in url patterns
urlpatterns = [
    path('admin/', admin.site.urls),
]


# DRF url patterns
urlpatterns += [
    path('api/auth/', include('rest_framework.urls')),
    path('api/', include(router.urls)),
]
