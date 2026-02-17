# core/services/notification_service.py

from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging


class NotificationService:
    _initialized = False

    @staticmethod
    def _ensure_firebase_initialized():
        """Garante que Firebase está inicializado."""
        if NotificationService._initialized:
            return True

        if firebase_admin._apps:
            NotificationService._initialized = True
            print("ℹ️ Firebase já inicializado")
            return True

        try:
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            cred_path = BASE_DIR / "SGGM" / "serviceAccountKey.json"

            print(f"\n🔥 Inicializando Firebase...")
            print(f"📂 {cred_path}")

            if not cred_path.exists():
                print(f"❌ Arquivo não encontrado: {cred_path}")
                return False

            cred = credentials.Certificate(str(cred_path))
            firebase_admin.initialize_app(cred)

            NotificationService._initialized = True
            print("✅ Firebase inicializado!\n")
            return True

        except Exception as e:
            print(f"❌ Erro Firebase: {e}")
            import traceback

            traceback.print_exc()
            return False

    @staticmethod
    def enviar_notificacao_escala(musico, evento):
        """Envia notificação push para músico escalado."""
        if not NotificationService._ensure_firebase_initialized():
            print("❌ Firebase não inicializado")
            return False

        if not musico.fcm_token:
            print(f"⚠️ {musico.nome} sem token FCM")
            return False

        try:
            print(f"\n📤 ENVIANDO NOTIFICAÇÃO")
            print(f"   Para: {musico.nome}")
            print(f"   Token: {musico.fcm_token[:30]}...")
            print(f"   Evento: {evento.nome}")

            from datetime import datetime

            data_evento = datetime.fromisoformat(str(evento.data_evento))
            data_formatada = data_evento.strftime("%d/%m/%Y às %H:%M")

            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"🎵 Nova Escala: {evento.nome}",
                    body=f"Você foi escalado para {data_formatada}. Confirme sua presença!",
                ),
                data={
                    "tipo": "nova_escala",
                    "escala_id": str(musico.id),
                    "evento_id": str(evento.id),
                    "evento_nome": evento.nome,
                    "data_evento": str(evento.data_evento),
                },
                token=musico.fcm_token,
            )

            response = messaging.send(message)
            print(f"✅ Notificação enviada! ID: {response}\n")
            return True

        except Exception as e:
            print(f"❌ Erro ao enviar: {e}")
            import traceback

            traceback.print_exc()
            return False
