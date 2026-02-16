# ruff: noqa: F403, F401

"""
Configurações otimizadas para execução de testes.
Ultra rápido com SQLite em memória.
"""
import tempfile
from datetime import timedelta

from .settings.base import *  # Importar tudo do base

# ==============================================================================
# DEBUG
# ==============================================================================
DEBUG = False
ALLOWED_HOSTS = ["*"]

# ==============================================================================
# SECRET KEY
# ==============================================================================
SECRET_KEY = "test-secret-key-insegura-apenas-para-testes"

# ==============================================================================
# DATABASE - SQLite em memória (ultra rápido)
# ==============================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ==============================================================================
# DJANGO REST FRAMEWORK - SEM autenticação em testes
# ATENÇÃO: Sobrescrever COMPLETAMENTE a configuração do base.py
# ==============================================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],  # ✅ Lista vazia = sem autenticação
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",  # ✅ Permitir tudo
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
}

# ==============================================================================
# SIMPLE JWT - Desabilitado em testes (não precisa)
# ==============================================================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# ==============================================================================
# PASSWORD HASHER - Simplificado para velocidade
# ==============================================================================
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ==============================================================================
# PASSWORD VALIDATORS - Desabilitado para testes
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = []

# ==============================================================================
# EMAIL - Backend em memória
# ==============================================================================
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ==============================================================================
# CACHE - Em memória local
# ==============================================================================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-test-cache",
    }
}

# ==============================================================================
# MEDIA FILES - Diretório temporário
# ==============================================================================
MEDIA_ROOT = tempfile.mkdtemp()

# ==============================================================================
# STORAGE - Sistema de arquivos padrão
# ==============================================================================
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ==============================================================================
# CORS - Permissivo para testes
# ==============================================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

# ==============================================================================
# SECURITY - Desabilitado para testes
# ==============================================================================
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ==============================================================================
# CELERY - Execução síncrona
# ==============================================================================
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ==============================================================================
# LOGGING - Silencioso nos testes
# ==============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
}


# ==============================================================================
# MIGRATIONS - Desabilitadas para velocidade máxima
# ==============================================================================
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()
