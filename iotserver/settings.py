import os
from pathlib import Path

from dotenv import load_dotenv

# Load the environmental variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('IOTSERVER_SECRET_KEY', 'insecure-secretkey')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('IOTSERVER_DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = ['*']


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    # 3rd party apps
    'corsheaders',
    'django_filters',
    'mapwidgets',
    'rest_framework',
    'rest_framework_gis',
    'rest_framework.authtoken',
    # Project specific apps
    'iotserver.apps.device',
    'iotserver.apps.user',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'iotserver.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'iotserver.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('IOTSERVER_POSTGRES_DBNAME', 'iotserver'),
        'USER': os.environ.get('IOTSERVER_POSTGRES_USER', ''),
        'PASSWORD': os.environ.get('IOTSERVER_POSTGRES_PASSWORD', ''),
        'HOST': os.environ.get('IOTSERVER_POSTGRES_HOST', 'localhost'),
        'PORT': '5432',
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': os.environ.get('IOTSERVER_MEMCACHED_LOCATION', 'localhost:11211'),
        'TIMEOUT': (60 * 60),  # 1 hour
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.DjangoModelPermissions'],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50,
}


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

# CORS Setup
CORS_ORIGIN_WHITELIST = os.environ.get(
    'IOTSERVER_CORS_ORIGIN_WHITELIST', 'http://localhost:3000'
)
if CORS_ORIGIN_WHITELIST == '*':
    CORS_ORIGIN_WHITELIST = None
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ORIGIN_WHITELIST = CORS_ORIGIN_WHITELIST.split(',')

# MQTT settings
MQTT = {
    'host': os.environ.get('IOTSERVER_MQTT_HOST', 'localhost'),
    'port': os.environ.get('IOTSERVER_MQTT_PORT', 1883),
}

# Integration config
INTEGRATIONS = {
    'weather': {
        'url': os.environ.get(
            'IOTSERVER_OPENWEATHER_URL',
            'https://api.openweathermap.org/data/2.5/onecall',
        ),
        'api_key': os.environ.get('IOTSERVER_OPENWEATHER_APIKEY', 'openweather-key'),
    }
}

# GIS config
MAP_WIDGETS = {
    'GooglePointFieldWidget': (
        ('zoom', 15),
        ('mapCenterLocation', [-26.190, 28.050]),
        (
            'GooglePlaceAutocompleteOptions',
            {'componentRestrictions': {'country': 'za'}},
        ),
        ('markerFitZoom', 12),
    ),
    'GOOGLE_MAP_API_KEY': os.environ.get(
        'IOTSERVER_GOOGLEMAPS_APIKEY', 'googlemaps-key'
    ),
}

# Device syncing
AUTO_SYNC_DEVICE = os.environ.get('IOTSERVER_AUTO_SYNC_DEVICE', '0') == '1'

# Webrepl config
WEBREPL_PORT = os.environ.get('IOTSERVER_WEBREPL_PORT', 8266)
WEBREPL_PASSWORD = os.environ.get('IOTSERVER_WEBREPL_PASSWORD', 'webrepl-password')
