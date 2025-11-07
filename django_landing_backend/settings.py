import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Set path of media
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ─── Core Django Config ─────────────────────────────
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

# ─── Installed Apps ─────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    "rest_framework",
    "drf_spectacular",
    # Local apps
    "landing",
]

# ─── Middleware ─────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = "django_landing_backend.urls"

# ─── Templates (needed for admin/DRF browsable API) ─
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
            ],
        },
    },
]

# ─── WSGI (Gunicorn entrypoint) ─────────────────────
WSGI_APPLICATION = "django_landing_backend.wsgi.application"

# ─── Database (PostgreSQL) ──────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "landing_db"),
        "USER": os.getenv("POSTGRES_USER", "landing_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "landing_pass"),
        "HOST": os.getenv("POSTGRES_HOST", "postgres_db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# ─── MongoDB Config (for logs) ───────────────────────
MONGO_CONFIG = {
    "host": os.getenv("MONGO_HOST", "mongo_log_db"),
    "port": int(os.getenv("MONGO_PORT", 27017)),
    "username": os.getenv("MONGO_USER", "landing_mongo"),
    "password": os.getenv("MONGO_PASSWORD", "landing_mongo_pass"),
    "db_name": os.getenv("MONGO_INITDB_DATABASE", "landing_logs"),
}

# ─── Redis Cache ─────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{os.getenv('REDIS_HOST', 'redis_cache')}:{os.getenv('REDIS_PORT', '6379')}/{os.getenv('REDIS_DB', '0')}",
    }
}

# ─── Static Files ─────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = "/app/static"

# ─── REST Framework ──────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'EEOverFlow API',
    'DESCRIPTION': 'API documentation for your Django project with Swagger/OpenAPI.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1',
    'COMPONENTS': {
        'securitySchemes': {
            'jwtAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    }
}

# ─── Celery Config Import ────────────────────────────
from .celery import app as celery_app
__all__ = ("celery_app",)

# ─── Other Settings ──────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TIME_ZONE = "UTC"
USE_TZ = True
