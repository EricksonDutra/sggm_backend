"""
Importa as configurações baseadas na variável de ambiente DJANGO_SETTINGS_MODULE
ou DJANGO_ENV.
"""

import os

# Detecta o ambiente
ENVIRONMENT = os.environ.get("DJANGO_ENV", "development")

if ENVIRONMENT == "production":
    from .production import *
elif ENVIRONMENT == "testing":
    from .testing import *
else:
    from .development import *
