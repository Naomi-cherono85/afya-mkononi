"""
Django settings for afya_mkononi project.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'tailwind',
    'theme',
    'django_browser_reload',

    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.chatbot',
    'apps.appointments',
    'apps.reminders',
    'apps.health_tips',
    'apps.frontend',
]

TAILWIND_APP_NAME = 'theme'
INTERNAL_IPS = ['127.0.0.1']
NPM_BIN_PATH = r'C:\Program Files\nodejs\npm.cmd'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_browser_reload.middleware.BrowserReloadMiddleware',
]

ROOT_URLCONF = 'afya_mkononi.urls'

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
                'apps.core.context_processors.site_settings',
                'apps.health_tips.context_processors.health_tip_of_the_day',
            ],
        },
    },
]

WSGI_APPLICATION = 'afya_mkononi.wsgi.application'


DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
    )
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "theme" / "static",
]

# User-uploaded media (avatars, health-tip images).
# NOTE: served by Django only in DEBUG (see afya_mkononi/urls.py). In production
# this should be backed by object storage (e.g. S3) — WhiteNoise serves static
# files only, not media.
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / "media"

# Authentication redirects
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'frontend:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Anthropic Claude (chatbot AI service)
ANTHROPIC_API_KEY = config('AI_API_KEY', default='')
ANTHROPIC_MODEL = config('ANTHROPIC_MODEL', default='claude-haiku-4-5')
ANTHROPIC_MAX_TOKENS = config('ANTHROPIC_MAX_TOKENS', default=1024, cast=int)
ANTHROPIC_HISTORY_TURNS = config('ANTHROPIC_HISTORY_TURNS', default=10, cast=int)
