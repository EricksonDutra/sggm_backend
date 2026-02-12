from .settings import *
import tempfile

# --------------------------------------------------
# DEBUG
# --------------------------------------------------
DEBUG = False

# --------------------------------------------------
# SECRET KEY
# --------------------------------------------------
SECRET_KEY = "test-secret-key"

# --------------------------------------------------
# DATABASE — ultra rápido
# --------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# --------------------------------------------------
# PASSWORD HASHER — rápido
# --------------------------------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# --------------------------------------------------
# EMAIL — mock
# --------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# --------------------------------------------------
# CACHE — mock
# --------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache"
    }
}

# --------------------------------------------------
# MEDIA FILES — temporário
# --------------------------------------------------
MEDIA_ROOT = tempfile.mkdtemp()

# --------------------------------------------------
# STORAGE — fake
# --------------------------------------------------
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# --------------------------------------------------
# CELERY — síncrono
# --------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# --------------------------------------------------
# LOGGING — silencioso
# --------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}

# --------------------------------------------------
# MIGRATIONS — opcional ultra rápido
# (remove se quiser testar migrations)
# --------------------------------------------------
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()
