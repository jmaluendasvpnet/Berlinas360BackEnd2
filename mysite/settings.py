from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-659s223%_rb_ga9#-$cvfklm7(dn4%icgw0y$3$wizuv+)-er5'

# settings.py
INSTALLED_APPS = [
    # Aplicaciones de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Terceros
    'djoser',
    'channels',
    'psycopg2',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    
    # Aplicaciones locales
    'myapp.apps.MyAppConfig',
    'django_extensions'
]

ASGI_APPLICATION = 'mysite.asgi.application'
WSGI_APPLICATION = 'mysite.wsgi.application'

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, 6379)],
        },
    },
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'myapp.middleware.CurrentUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'mysite.urls'

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


# DATABASES = {
#     'default': {
#         'NAME': 'verceldb',
#         'USER': 'default',
#         'PASSWORD': 'nL3a0MFZXvST',
#         'HOST': 'ep-bitter-moon-a45p4dqh-pooler.us-east-1.aws.neon.tech',
#         'PORT': 5432,
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         # 'OPTIONS': {
#         #     'dsn': 'postgres://default:nL3a0MFZXvST@ep-bitter-moon-a45p4dqh-pooler.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require&options=endpoint%3Dep-bitter-moon-a45p4dqh'
#         # }

#     }
# } # Esto es local en Windows

DATABASES = {
    'default': {
        'NAME': 'SST',
        'USER': 'postgres',
        'PASSWORD': 'D3v3l0p3r2025**',
        'HOST': '201.216.13.254',
        'PORT': 5445,
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        # 'OPTIONS': {
        #     'dsn': 'postgres://default:nL3a0MFZXvST@ep-bitter-moon-a45p4dqh-pooler.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require&options=endpoint%3Dep-bitter-moon-a45p4dqh'
        # }

    }
} # Esto es local en Windows

# PRUEBA2023
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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = False

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'myapp.Login'

CORS_ALLOW_ALL_ORIGINS = True  # Activo solo por pruebas o desarrollo.

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:8000',
    'http://localhost:8001',
    "https://api.jmaluendas.site",
    "https://berlione-ia.jmaluendas.site",
    'http://wsdx.berlinasdelfonce.com',
    'https://19a3-191-97-15-98.ngrok-free.app'
]


CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://localhost:8001',
    'https://*.jmaluendas.site,',
    'https://api.jmaluendas.site'
]
DEBUG = True  # Activo solo en desarrollo

SECURE_SSL_REDIRECT = False

ALLOWED_HOSTS = ['172.16.0.53', '.jmaluendas.site', '192.168.0.103', '192.168.0.106', '172.23.112.1', 'localhost','192.168.205.105', '192.168.0.109', '172.26.48.1', '192.168.0.114', '192.168.0.105', '192.168.0.108', '192.168.0.117', '192.168.2.23',
                 '127.0.0.1', '192.168.0.112', '192.168.2.17', '192.168.0.111', '192.168.0.110', '[::1]', '192.168.8.6', ]  # Host Permitidos

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_CREDENTIALS = True

# 24 horas de sesion activa - aun sin comprobacion.
CORS_PREFLIGHT_MAX_AGE = 86400

DATA_UPLOAD_MAX_MEMORY_SIZE = None
FILE_UPLOAD_MAX_MEMORY_SIZE = None
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 30,
    'PAGE_SIZE_QUERY_PARAM': 'page_size',
    'MAX_PAGE_SIZE': 100, 
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'myapp.authentication.StaticTokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

DJOSER = {
    'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
}
# 50 megabytes - es el ancho de banda maximo que permite a una sesion
# DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024

# Ruta a Face IDs
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

APPEND_SLASH = False

# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATIC_API_TOKEN = 'JMalu-BerliDATA'

FRONTEND_URL =  'https://berlione-ia.jmaluendas.site'

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'America/Bogota'
CELERY_ENABLE_UTC = False
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,
    'fanout_patterns': True,
    'fanout_prefix': True,
}

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-expiring-documents-daily': {
        'task': 'myapp.tasks.check_expiring_documents',
        'schedule': crontab(hour=12, minute=6),  # Ejecuta a medianoche diariamente
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'celery.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'myapp': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'ppocr': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

GOOGLE_MAPS_API_KEY = 'AIzaSyBCbem5jjGxtGKABh2f3C61b_HQ0wBhKN4'