"""
Configurações para ambiente de testes.
"""

from .base import *

# ==============================================================================
# DEBUG
# ==============================================================================
DEBUG = False

ALLOWED_HOSTS = ["*"]

# ==============================================================================
# DATABASE - SQLite para testes (não requer privilégios especiais)
# ==============================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # Banco em memória - mais rápido
    }
}

# ==============================================================================
# STATIC FILES
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
# CORS - Permissivo em testes
# ==============================================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# ==============================================================================
# SECURITY - Desabilitado em testes
# ==============================================================================
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]

# ==============================================================================
# PASSWORD VALIDATORS - Simplificado para testes
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = []

# ==============================================================================
# LOGGING - Silencioso em testes
# ==============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}
