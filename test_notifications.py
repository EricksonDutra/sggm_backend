import os

import django
import pytest

from core.models import Evento, Musico
from core.services import NotificationService

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sggm_backend.settings")
django.setup()


@pytest.mark.django_db
def testar_notificacao():
    print("🔍 Buscando músico e evento...")

    # Buscar primeiro músico
    musico = Musico.objects.first()
    if not musico:
        print("❌ Nenhum músico encontrado no banco de dados")
        return

    print(f"✅ Músico: {musico.nome}")

    # Buscar primeiro evento
    evento = Evento.objects.first()
    if not evento:
        print("❌ Nenhum evento encontrado no banco de dados")
        return

    print(f"✅ Evento: {evento.nome}")

    # Verificar FCM token
    if not musico.fcm_token:
        print("⚠️ Músico não tem FCM token configurado")
        token = input("Cole o FCM token do app mobile: ").strip()
        musico.fcm_token = token
        musico.save()
        print("✅ Token salvo!")

    # Enviar notificação
    print("📤 Enviando notificação...")
    try:
        NotificationService.enviar_notificacao_escala(musico, evento)
        print("✅ Notificação enviada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar notificação: {e}")


if __name__ == "__main__":
    testar_notificacao()
