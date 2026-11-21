"""Django settings for DevHelp (VK EDU Web)."""
import os
import sys
from ipaddress import IPv4Address
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# В Docker переменные .env.docker передаёт Compose и они имеют приоритет.
load_dotenv(BASE_DIR / '.env.local')


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=''):
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


def docker_gateway():
    routes = Path('/proc/net/route')
    if routes.is_file():
        for route in routes.read_text().splitlines()[1:]:
            _, destination, gateway, *_ = route.split()
            if destination == '00000000':
                return str(IPv4Address(int(gateway, 16).to_bytes(4, 'little')))


SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = env_bool('DEBUG')

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'questions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'application.urls'

DEBUG_TOOLBAR_ENABLED = DEBUG and sys.argv[1:2] != ['test']

if DEBUG_TOOLBAR_ENABLED:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = env_list('INTERNAL_IPS', '127.0.0.1,::1')
    if env_bool('RUNNING_IN_DOCKER') and (gateway := docker_gateway()):
        INTERNAL_IPS.append(gateway)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.sidebar',
            ],
        },
    },
]

WSGI_APPLICATION = 'application.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'devhelp'),
        'USER': os.getenv('POSTGRES_USER', 'devhelp'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    'sidebar': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'core_sidebar_cache',
    },
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Статика: исходники лежат в <app>/static/<app>/, collectstatic собирает их в /static
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

# Файлы, загруженные пользователями (аватарки)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
