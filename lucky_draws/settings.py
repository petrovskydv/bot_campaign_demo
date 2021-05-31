"""
Django settings for lucky_draws project.

Generated by 'django-admin startproject' using Django 3.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os
import rollbar

from environs import Env


env = Env()
env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY', 'REPLACE_ME')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', ['127.0.0.1', 'localhost'])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'draw_app',
    'phonenumber_field',
    'django_rq',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'rollbar.contrib.django.middleware.RollbarNotifierMiddlewareExcluding404',
]

ROOT_URLCONF = 'lucky_draws.urls'

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

WSGI_APPLICATION = 'lucky_draws.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': env.dj_db_url(
        'DATABASE_URL',
        env.str('DATABASE_URL', 'postgres://lucky_draws:Sunrise23@localhost:5432/lucky_draws'),
    )
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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Settings to configure Rollbar
ROLLBAR = {
    'access_token': env.str('ROLLBAR_TOKEN', ''),
    'environment': 'development' if DEBUG else 'production',
    'branch': 'master',
    'root': BASE_DIR,
}

rollbar.init(**ROLLBAR)

INN = env.int('INN', 0)
PASSWORD = env.str('PASSWORD', '')
CLIENT_SECRET = env.str('CLIENT_SECRET', '')
DYNAM_LICENSE_KEY = env.str('DYNAM_LICENSE_KEY', '')
BARCODE_FORMAT = env.str('BARCODE_FORMAT', 'All')

NODE_API_ENDPOINT = env.str('NODE_API_ENDPOINT', 'http://127.0.0.1:1880/api/')
TG_TOKEN = env.str('TG_TOKEN', '')

RQ_QUEUES = {
    'default': {
        'HOST': env.str('REDIS_HOST', 'localhost'),
        'PORT': env.int('REDIS_PORT', 6379),
        'PASSWORD': env.str('REDIS_PASSWORD', ''),
    },
}

FNS_MASTER_TOKEN = env.str('FNS_MASTER_TOKEN', '')
FNS_APPID = env.str('FNS_APPID', '')
FNS_TEMPORARY_TOKEN_REDIS_KEY = 'fns_open_api_temporary_token'
FNS_REQUEST_INTERFACE = '10.19.0.7'
FNS_AUTH_ENDPOINT = 'https://openapi.nalog.ru:8090/open-api/AuthService/0.1'
FNS_KKT_SERVICE_ENDPOINT = 'https://openapi.nalog.ru:8090/open-api/ais3/KktService/0.1'
