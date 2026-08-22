from pathlib import Path
from decouple import config
from datetime import timedelta
import importlib.util
import sys

# BASE_DIR deve ser o primeiro
BASE_DIR = Path(__file__).resolve().parent.parent
HAS_WHITENOISE = importlib.util.find_spec("whitenoise") is not None

SECRET_KEY = config("SECRET_KEY", default="django-insecure-CHANGE_ME", cast=str)
# DEBUG must be False in production to avoid storing SQL queries in memory
DEBUG = config("DEBUG", default=False, cast=bool)

# Hosts permitidos com suporte a Railway, Render e HuggingFace
ALLOWED_HOSTS = [
    host.strip()
    for host in config(
        "ALLOWED_HOSTS",
        default="*",
    ).split(",")
    if host.strip()
]
for host in [
    ".railway.app",
    ".up.railway.app",
    ".onrender.com",
    "proxy.spaces.internal.huggingface.tech",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
]:
    if host not in ALLOWED_HOSTS and "*" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

GROQ_API_KEY = config("GROQ_API_KEY", default=None)

# Database
DATABASE_URL = config("DATABASE_URL", default=None)

if DATABASE_URL:
    import dj_database_url

    # Normaliza esquema postgres:// para postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    db_config = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=300,
        conn_health_checks=True,
    )

    # Configuração de SSL resiliente para Railway, Neon, Supabase e SQLite
    if not DEBUG and "sqlite" not in db_config.get("ENGINE", ""):
        options = db_config.setdefault("OPTIONS", {})
        if "sslmode" not in options:
            if "railway.internal" in DATABASE_URL:
                options["sslmode"] = "disable"
            elif any(cloud in DATABASE_URL for cloud in ["neon.tech", "supabase", "amazonaws.com", "cockroach"]):
                options["sslmode"] = "require"
            else:
                options["sslmode"] = "prefer"

    DATABASES = {"default": db_config}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=365),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "base",
    "uploads",
    "knowledge_base",
    "chat",
    "ai_agents",
    "studies",
    "flashcards",
    "quizzes",
    "notifications",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
]

# WhiteNoise deve vir antes de SessionMiddleware
if HAS_WHITENOISE:
    MIDDLEWARE.append("whitenoise.middleware.WhiteNoiseMiddleware")

MIDDLEWARE.extend([
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
])

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["core/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

raw_origins = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,https://supercai0-sampaio-ai.hf.space,https://web-production-9fdbc.up.railway.app",
).split(",")

CORS_ALLOWED_ORIGINS = []
for origin in raw_origins:
    origin = origin.strip()
    if origin:
        if not origin.startswith(("http://", "https://")):
            origin = f"https://{origin}"
        CORS_ALLOWED_ORIGINS.append(origin)
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

APPEND_SLASH = True

STORAGES = {
    "default": {
        "BACKEND": "core.storage.DatabaseStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Redis & Celery Configurations
raw_celery_broker = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0").strip()
if raw_celery_broker and not raw_celery_broker.startswith(("redis://", "rediss://", "unix://")):
    CELERY_BROKER_URL = f"redis://{raw_celery_broker}"
elif raw_celery_broker:
    CELERY_BROKER_URL = raw_celery_broker
else:
    CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"

raw_celery_result = config("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL).strip()
if raw_celery_result and not raw_celery_result.startswith(("redis://", "rediss://", "unix://")):
    CELERY_RESULT_BACKEND = f"redis://{raw_celery_result}"
else:
    CELERY_RESULT_BACKEND = raw_celery_result or CELERY_BROKER_URL

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_WORKER_CONCURRENCY = 2
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 512000

# Redis Cache & Database Sessions (100% estável entre deploys e restarts serverless)
raw_redis_url = config("REDIS_URL", default="redis://127.0.0.1:6379/1").strip()
if raw_redis_url and not raw_redis_url.startswith(("redis://", "rediss://", "unix://")):
    REDIS_URL = f"redis://{raw_redis_url}"
elif raw_redis_url:
    REDIS_URL = raw_redis_url
else:
    REDIS_URL = "redis://127.0.0.1:6379/1"

if REDIS_URL and "test" not in sys.argv:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
            "KEY_PREFIX": "sampaio",
            "TIMEOUT": 3600,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "sampaio-local-cache",
        }
    }

# Sessões persistidas com segurança no banco de dados relacional
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Overrides para ambiente de testes automatizados
if "test" in sys.argv:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.db"
    GROQ_API_KEY = "gsk_placeholder_for_development"


# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800    # 50MB in bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800    # 50MB in bytes

# Hardening Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    import os

    # Disable SSL redirect inside Hugging Face Spaces as the reverse proxy handles it
    SECURE_SSL_REDIRECT = not bool(os.environ.get("SPACE_ID"))
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

raw_csrf = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://*.up.railway.app,https://*.railway.app,https://supercai0-sampaio-ai.hf.space,https://sampaio-ai.onrender.com",
).split(",")

CSRF_TRUSTED_ORIGINS = []
for origin in raw_csrf:
    origin = origin.strip()
    if origin:
        if not origin.startswith(("http://", "https://")):
            origin = f"https://{origin}"
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

for fallback_domain in [
    "https://*.up.railway.app",
    "https://*.railway.app",
    "https://*.onrender.com",
    "https://supercai0-sampaio-ai.hf.space",
]:
    if fallback_domain not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(fallback_domain)

# Trust the X-Forwarded-Proto header from Railway / Render / HF proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Email Settings
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=587)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=True)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@sampaio-ai.com")

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = (
        "django.core.mail.backends.console.EmailBackend"
        if DEBUG
        else "django.core.mail.backends.smtp.EmailBackend"
    )

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

