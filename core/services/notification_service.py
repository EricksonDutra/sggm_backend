import firebase_admin
from django.conf import settings
from firebase_admin import credentials, messaging


class NotificationService:
    _initialized = False

    @classmethod
    def initialize(cls):
        """Inicializa Firebase Admin SDK usando variáveis de ambiente"""
        if cls._initialized:
            return

        try:
            if settings.FIREBASE_CONFIG:
                # Usar credenciais do settings (variável de ambiente)
                cred = credentials.Certificate(settings.FIREBASE_CONFIG)
                firebase_admin.initialize_app(cred)
                cls._initialized = True
                print("✅ Firebase Admin SDK inicializado")
            else:
                print("⚠️ Firebase não configurado")

        except ValueError as e:
            if "already exists" in str(e):
                cls._initialized = True
            else:
                raise
        except Exception as e:
            print(f"❌ Erro ao inicializar Firebase: {e}")

    @staticmethod
    def enviar_notificacao_escala(musico, evento):
        """Enviar notificação quando músico for escalado"""

        # Obter token FCM do músico (adicionar campo no modelo)
        if not musico.fcm_token:
            return False

        message = messaging.Message(
            notification=messaging.Notification(
                title="Nova Escala! 🎵",
                body=f'Você foi escalado para {evento.nome} em {evento.data_evento.strftime("%d/%m/%Y")}',
            ),
            data={
                "type": "escala",
                "evento_id": str(evento.id),
                "musico_id": str(musico.id),
            },
            token=musico.fcm_token,
        )

        try:
            response = messaging.send(message)
            print(f"✅ Notificação enviada: {response}")
            return True
        except Exception as e:
            print(f"❌ Erro ao enviar notificação: {e}")
            return False

    @staticmethod
    def enviar_notificacao_topico(topico, titulo, corpo, dados=None):
        """Enviar notificação para um tópico (ex: todos os músicos)"""

        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=corpo,
            ),
            data=dados or {},
            topic=topico,
        )

        try:
            response = messaging.send(message)
            return True
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
