from pathlib import Path
from decouple import config
from datetime import timedelta
import importlib.util

# BASE_DIR deve ser o primeiro
BASE_DIR = Path(__file__).resolve().parent.parent
HAS_WHITENOISE = importlib.util.find_spec('whitenoise') is not None

SECRET_KEY = config('SECRET_KEY', default='django-insecure-CHANGE_ME', cast=str)
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = [
    host.strip()
    for host in config(
        'ALLOWED_HOSTS',
        default='.hf.space, .onrender.com, proxy.spaces.internal.huggingface.tech, localhost, 127.0.0.1'
    ).split(',')
    if host.strip()
]
for host in ['.onrender.com', 'proxy.spaces.internal.huggingface.tech', 'localhost', '127.0.0.1']:
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)


GROQ_API_KEY = config('GROQ_API_KEY', default=None)

# Database
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    import dj_database_url
    db_config = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    # Ensure SSL is configured for cloud database/Neon DB when not in debug mode
    if not DEBUG and 'sqlite' not in db_config.get('ENGINE', ''):
        db_config.setdefault('OPTIONS', {})
        db_config['OPTIONS']['sslmode'] = 'require'
    DATABASES = {
        'default': db_config
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'base',
    'uploads',
    'knowledge_base',
    'chat',
    'ai_agents',
    'studies',
    'flashcards',
    'quizzes',
    'notifications',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if HAS_WHITENOISE:
    MIDDLEWARE.insert(2, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['core/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

#WSGI_APPLICATION = 'core.wsgi.application'

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

raw_origins = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,https://supercai0-sampaio-ai.hf.space',
).split(',')

CORS_ALLOWED_ORIGINS = []
for origin in raw_origins:
    origin = origin.strip()
    if origin:
        if not origin.startswith(('http://', 'https://')):
            origin = f'https://{origin}'
        CORS_ALLOWED_ORIGINS.append(origin)
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

APPEND_SLASH = True

STORAGES = {
    'default': {
        'BACKEND': 'core.storage.DatabaseStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# Celery Configurations — Redis used as both broker AND result backend
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Redis Cache Configurations
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Overrides para ambiente de testes automatizados
import sys
if 'test' in sys.argv:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    GROQ_API_KEY = 'gsk_placeholder_for_development'

# File upload limits (100MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB in bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB in bytes

# Hardening Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    import os
    # Disable SSL redirect inside Hugging Face Spaces as the reverse proxy handles it,
    # and forcing it internally breaks Hugging Face's local HTTP health check.
    SECURE_SSL_REDIRECT = not bool(os.environ.get("SPACE_ID"))
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config(
        'CSRF_TRUSTED_ORIGINS',
        default='https://supercai0-sampaio-ai.hf.space,https://sampaio-ai.onrender.com'
    ).split(',')
    if origin.strip()
]
if 'https://sampaio-ai.onrender.com' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://sampaio-ai.onrender.com')

# Trust the X-Forwarded-Proto header from the Hugging Face proxy for HTTPS detection
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Email Settings
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=587)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='no-reply@sampaio-ai.com')

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
