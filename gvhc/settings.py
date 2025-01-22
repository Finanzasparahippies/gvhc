"""
Django settings for gvhc project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
from dotenv import load_dotenv  # Importa dotenv para cargar variables
from decouple import config
from pathlib import Path
import cloudinary
import os
from datetime import timedelta


load_dotenv()  # Carga las variables desde .env 

cloudinary.config(
    cloud_name=config("CLOUD_NAME"),
    api_key=config("CLOUDINARY_API_KEY"),
    api_secret=config("CLOUDINARY_API_SECRET"),
    secure=True
    )


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
# CLOUDINARY_NAME = config("CLOUD_NAME")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "faqs",
    "users",
    "testing",
    "queues",
    #third party
    "rest_framework",
    "corsheaders",
    "openai",
    "cloudinary",
    "cloudinary_storage",
]

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
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
MODE = config("MODE", default="development")
print("MODE from .env:", MODE)

if MODE == "production":
    # Configuración para PostgreSQL en producción
    DATABASES = {
        "default": {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('POSTGRES_NAME'),
            'USER': config('POSTGRES_DB_USER'),
            'PASSWORD': config('POSTGRES_PASSWORD'),
            'HOST': config('POSTGRES_HOST'),
            'PORT': config('POSTGRES_PORT'),             
        }
}

else:
    # Configuración para SQLite en desarrollo
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
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

AUTH_USER_MODEL = 'users.User'


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

#keywords for calls
KEYWORDS = ["Golden Valley Health Center", "ER", "two months", "PCP", "primary care provider", "emergency room", "help you", "assist you", "name", "date of birth", "birth date", "address", "phone", "else"]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.github\.dev$",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",    
]

