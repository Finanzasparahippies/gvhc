"""
Django settings for gvhc project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import os  
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import psycopg2
from pathlib import Path
import cloudinary 
from dotenv import load_dotenv
from datetime import timedelta
from django.core.management.utils import get_random_secret_key
import environ
import ssl # Necesario si vas a manejar CERT_REQUIRED/OPTIONAL programáticamente

env = environ.Env()
environ.Env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR / '.env')

load_dotenv(dotenv_path=BASE_DIR / '.env', override=True) 

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
MODE = os.getenv("MODE", "development").lower()

if MODE == "production":
    SHARPEN_API_BASE_URL = os.getenv('SHARPEN_API_BASE_URL')
    # Opcional: si Sharpen tiene claves diferentes para producción
    SHARPEN_CKEY1 = os.getenv('SHARPEN_CKEY1')
    SHARPEN_CKEY2 = os.getenv('SHARPEN_CKEY2')
    SHARPEN_UKEY = os.getenv('SHARPEN_UKEY')
else: # development (o cualquier otro valor de MODE)
    SHARPEN_API_BASE_URL = os.getenv('SHARPEN_API_BASE_URL', 'https://api-current.iz1.sharpen.cx/') # Valor por defecto para dev si no está en .env
    # Opcional: si Sharpen tiene claves diferentes para desarrollo
    SHARPEN_CKEY1 = os.getenv('SHARPEN_CKEY1')
    SHARPEN_CKEY2 = os.getenv('SHARPEN_CKEY2')
    SHARPEN_UKEY = os.getenv('SHARPEN_UKEY')

# URL de Redis para Channels
# Render usa REDIS_URL para Redis
if MODE == "production":
    # Ahora, asume que REDIS_URL_PROD ya tiene el parámetro SSL
    REDIS_URL = os.getenv('REDIS_URL_PROD')
    if not REDIS_URL:
        raise Exception("REDIS_URL_PROD must be set in production mode.")
    # Elimina esta sección, ya no es necesaria:
    # if 'onrender.com' in REDIS_URL and 'ssl_cert_reqs' not in REDIS_URL:
    #     REDIS_URL += '?ssl_cert_reqs=none'
else: # development
    REDIS_URL = os.getenv('REDIS_URL_DEV', 'redis://localhost:6379/')
    
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer', 
        'CONFIG': {
            "hosts": [REDIS_URL], # Usa la variable que configuramos por entorno
        },
    },
}


# Impresiones para depuración
print(f"Loading settings in MODE: {MODE}")
print(f"DEBUG is: {DEBUG}")
print(f"SHARPEN_API_BASE_URL is: {SHARPEN_API_BASE_URL}")
print(f"REDIS_URL is: {REDIS_URL}")

ALLOWED_HOSTS_STR = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,gvhc-backend.onrender.com,gvhc.netlify.app,gvhc-websocket.onrender.com')
ALLOWED_HOSTS_ENV = ALLOWED_HOSTS_STR.split(',')

ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV if host.strip()] # Limpiar espacios y vacíos

# Añadir explícitamente los dominios de Render y Netlify
# ALLOWED_HOSTS.extend([
#     'gvhc-backend.onrender.com',
#     'gvhc.netlify.app',
#     'localhost', # Para desarrollo local
#     '127.0.0.1', # Para desarrollo local
# ])

# Eliminar duplicados si los hay
ALLOWED_HOSTS = list(set(ALLOWED_HOSTS))

print(f"Loading settings in MODE: {MODE}")
print(f"DEBUG is: {DEBUG}") # Usar la variable DEBUG que ya definiste
print(f"POSTGRES_HOST is: '{os.getenv('POSTGRES_HOST')}'")
print(f"POSTGRES_USER is: '{os.getenv('POSTGRES_DB_USER')}'")

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
    )


# Build paths inside the project like this: BASE_DIR / 'subdir'.
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
# CLOUDINARY_NAME = config("CLOUD_NAME")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", get_random_secret_key())


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "daphne", 
    "django.contrib.staticfiles",
    "faqs",
    "users",
    "testing",
    "queues",
    "reports",
    "dashboards",
    "django_celery_beat",
    "websocket_app",
    "channels",
    #third party
    "rest_framework",
    "corsheaders",
    "openai",
    "cloudinary",
    "cloudinary_storage",
]

ASGI_APPLICATION = "gvhc.asgi.application"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 1000,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=540),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',  # Algoritmo de cifrado
    'SIGNING_KEY': SECRET_KEY,  # Usa la clave secreta de tu proyecto
    'AUTH_HEADER_TYPES': ('Bearer',),  # Tipo de encabezado de autenticación
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Agregar aquí
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gvhc.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "gvhc.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


    # Configuración para PostgreSQL en producción
DATABASES = {
        "default": {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_NAME'),
            'USER': os.getenv('POSTGRES_DB_USER'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'HOST': os.getenv('POSTGRES_HOST'),
            'PORT': os.getenv('POSTGRES_PORT'),             
        }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # Add other backends if you use them, e.g., 'allauth.account.auth_backends.AuthenticationBackend'
]

AUTH_USER_MODEL = 'users.User'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG', # Cambia a INFO si solo quieres ver los INFO y superiores
            'class': 'logging.StreamHandler',
            'formatter': 'simple', # Puedes usar 'verbose' para más detalles
        },
    },
    'loggers': {
        'django': { # Logs de Django
            'handlers': ['console'],
            'level': 'INFO', # O 'DEBUG' si quieres ver más logs internos de Django
            'propagate': False,
        },
        '': { # Este es el logger por defecto para tu código de aplicación (tu views.py)
            'handlers': ['console'],
            'level': 'DEBUG', # ¡IMPORTANTE! Asegúrate de que esté en DEBUG o INFO
            'propagate': False,
        },
        'channels': {
            'handlers': ['console'],
            'level': 'DEBUG', # Cambia a INFO en producción si hay demasiados logs
            'propagate': False,
        },
        # Añadir logger para tu app websocket_app
        'websocket_app': {
            'handlers': ['console'],
            'level': 'DEBUG', # Asegúrate de que los logs de tu consumer se vean
            'propagate': False,
        },
    }
}
# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

#keywords for calls
KEYWORDS = ["Golden Valley Health Center", "ER", "two months", "PCP", "primary care provider", "emergency room", "help you", "assist you", "name", "date of birth", "birth date", "address", "phone", "else"]

CORS_ALLOWED_ORIGINS = [
    "https://gvhc.netlify.app",  # URL del frontend
    "http://localhost:5173",  # Para pruebas locales
    "http://localhost:8000",
    "https://api-current.iz1.sharpen.cx",
    "https://gvhc-backend.onrender.com",
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.github\.dev$",
    r"^https://gvhc-backend\.onrender\.com$", # Añade esto si no está
    r"^https://gvhc\.netlify\.app$", # Añade esto para tu frontend Netlify
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:8001",
    "http://localhost:5173",
    "https://gvhc.netlify.app", 
    "https://gvhc-backend.onrender.com",
    "wss://gvhc-backend.onrender.com",
    "https://api-current.iz1.sharpen.cx",
    "ws://localhost:8001",
    "https://gvhc-websocket.onrender.com"
]

CSRF_COOKIE_NAME = 'csrftoken'  # Asegúrate de que este valor sea el correcto

CORS_ALLOW_HEADERS = [
    "content-type",
    "authorization",
    "x-requested-with",
]

CORS_ALLOW_CREDENTIALS = True

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')


CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_IMPORTS = ('websocket_app.tasks',) # Or CELERY_INCLUDE = ['websocket_app.tasks'] if using Celery 4.x+ preferred syntax
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Hermosillo' # Ajusta tu zona horaria
CELERY_ENABLE_UTC = False # Si manejas tus horas localmente

CELERY_BEAT_SCHEDULE_FILENAME = "/data/celerybeat-schedule"
CELERY_BEAT_SCHEDULE = {
    'broadcast-every-5-seconds': {
        'task': 'websocket_app.tasks.broadcast_calls_update',
        'schedule': 5.0,
        'args': (),
    },
}

print(f"FINAL REDIS URL: {REDIS_URL}")
print(f"CELERY_BROKER_URL: {CELERY_BROKER_URL}")
