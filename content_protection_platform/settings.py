import os
from pathlib import Path
from decouple import config

# --------------------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-insecure-key-change-me")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# --------------------------------------------------------------------------------------
# Apps
# --------------------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 3rd-party
    "rest_framework",
    "corsheaders",

    # Local apps
    "users",
    "scanning",
    "detection",
    "legal",

    # (optional) register the project package if you keep templates/views here
    "content_protection_platform",
]

# --------------------------------------------------------------------------------------
# Middleware
# (CORS must come before CommonMiddleware)
# --------------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "content_protection_platform.urls"

# --------------------------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "content_protection_platform.wsgi.application"

# --------------------------------------------------------------------------------------
# Database (defaults to SQLite, can be overridden by env)
# --------------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": config("DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
        "USER": config("DB_USER", default=""),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default=""),
        "PORT": config("DB_PORT", default=""),
    }
}

# --------------------------------------------------------------------------------------
# Auth / i18n
# --------------------------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------------------
# Static & Media
# --------------------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------------------
# DRF
# --------------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# --------------------------------------------------------------------------------------
# CORS / CSRF (frontend at localhost:3000)
# --------------------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# If you do POSTs from the frontend, add CSRF trusted origins:
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# --------------------------------------------------------------------------------------
# Third-party API config (as you had)
# --------------------------------------------------------------------------------------
TELEGRAM = {
    "BOT_TOKEN": config("TELEGRAM_BOT_TOKEN", default=""),
    "WEBHOOK_SECRET": config("TELEGRAM_WEBHOOK_SECRET", default=""),
    "API_ID": config("TG_API_ID", default=None, cast=int),
    "API_HASH": config("TG_API_HASH", default=""),
    "SESSION_FILE": config("TG_SESSION_FILE", default=".tg_session"),
}

WHATSAPP = {
    "VERIFY_TOKEN": config("WHATSAPP_VERIFY_TOKEN", default=""),
    "ACCESS_TOKEN": config("WHATSAPP_ACCESS_TOKEN", default=""),
    "PHONE_NUMBER_ID": config("WHATSAPP_PHONE_NUMBER_ID", default=""),
}

OPENROUTER = {
    "API_KEY": config("OPENROUTER_API_KEY", default=""),
    "MODEL": config("OPENROUTER_MODEL", default="openrouter/anthropic/claude-3.5-sonnet"),
    "BASE_URL": config("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1"),
    "REFERER": config("OPENROUTER_REFERER", default="http://localhost:8000"),
    "APP_TITLE": config("OPENROUTER_APP_TITLE", default="ContentGuard"),
}

# --------------------------------------------------------------------------------------
# Celery / Redis (optional)
# --------------------------------------------------------------------------------------
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# --------------------------------------------------------------------------------------
# Email
# --------------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@contentguard.local")

# --------------------------------------------------------------------------------------
# App-specific
# --------------------------------------------------------------------------------------
PLATFORM_APIS = {
    "YOUTUBE_API_KEY": config("YOUTUBE_API_KEY", default=""),
    "FACEBOOK_ACCESS_TOKEN": config("FACEBOOK_ACCESS_TOKEN", default=""),
    "INSTAGRAM_ACCESS_TOKEN": config("INSTAGRAM_ACCESS_TOKEN", default=""),
    "TELEGRAM_BOT_TOKEN": config("TELEGRAM_BOT_TOKEN", default=""),
}

AI_MODEL_SETTINGS = {
    "SIMILARITY_THRESHOLD": config("SIMILARITY_THRESHOLD", default=0.8, cast=float),
}

LEGAL_TEMPLATES_DIR = BASE_DIR / "templates" / "legal"
EVIDENCE_STORAGE_PATH = BASE_DIR / "evidence"
CONFIGURE_MODELS_ON_STARTUP = config("CONFIGURE_MODELS_ON_STARTUP", default=False, cast=bool)
