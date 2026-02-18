from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.models import Escala, Evento, Instrumento, Musico
from core.services import GerenciadorEscala, NotificationService


class GerenciadorEscalaTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="erickson", email="e@e.com", password="testpass123"
        )

        self.musico = Musico.objects.create(
            user=self.user, nome="Erickson", status="ATIVO"
        )
        self.evento = Evento.objects.create(
            nome="Culto Jovens", data_evento=timezone.now(), local="Templo"
        )

    def test_adicionar_musico_via_servico(self):
        escala = GerenciadorEscala.adicionar_musico_ao_evento(
            self.evento.id, self.musico.id, "Violão"
        )
        self.assertEqual(escala.instrumento_no_evento.nome, "Violão")
        self.assertEqual(Escala.objects.count(), 1)

    def test_bloquear_conflito_escala(self):
        GerenciadorEscala.adicionar_musico_ao_evento(self.evento.id, self.musico.id)

        with self.assertRaises(ValidationError):
            GerenciadorEscala.adicionar_musico_ao_evento(self.evento.id, self.musico.id)


class NotificationServiceTest(TestCase):
    """Testes para o serviço de notificações push do Firebase."""

    def setUp(self):
        """Configuração inicial dos testes."""
        # Resetar flag de inicialização antes de cada teste
        NotificationService._initialized = False

        # Criar usuário
        self.user = User.objects.create_user(
            username="musico_test",
            email="test@test.com",
            password="testpass123",
        )

        # Criar instrumento
        self.instrumento = Instrumento.objects.create(nome="Guitarra")

        # Criar músico com token FCM
        self.musico = Musico.objects.create(
            user=self.user,
            nome="João Silva",
            status="ATIVO",
            instrumento_principal=self.instrumento,
            fcm_token="fake_fcm_token_123456789",
        )

        # Criar evento
        self.evento = Evento.objects.create(
            nome="Culto de Domingo",
            data_evento=timezone.now() + timezone.timedelta(days=1),
            local="Igreja Central",
        )

    def tearDown(self):
        """Limpeza após cada teste."""
        # Resetar estado do Firebase após cada teste
        NotificationService._initialized = False

    @patch("core.services.notification_service.firebase_admin")
    @patch("core.services.notification_service.credentials")
    @patch("core.services.notification_service.Path.exists")
    def test_inicializacao_firebase_sucesso(
        self, mock_exists, mock_credentials, mock_firebase
    ):
        """Testa inicialização bem-sucedida do Firebase."""
        # Configurar mocks
        mock_exists.return_value = True
        mock_firebase._apps = []
        mock_credentials.Certificate.return_value = Mock()

        # Executar
        result = NotificationService._ensure_firebase_initialized()

        # Verificar
        self.assertTrue(result)
        self.assertTrue(NotificationService._initialized)
        mock_firebase.initialize_app.assert_called_once()

    @patch("core.services.notification_service.firebase_admin")
    def test_inicializacao_firebase_ja_inicializado(self, mock_firebase):
        """Testa que não reinicializa Firebase se já estiver inicializado."""
        # Simular Firebase já inicializado
        mock_firebase._apps = [Mock()]

        # Executar
        result = NotificationService._ensure_firebase_initialized()

        # Verificar
        self.assertTrue(result)
        self.assertTrue(NotificationService._initialized)
        mock_firebase.initialize_app.assert_not_called()

    @patch("core.services.notification_service.Path.exists")
    @patch("core.services.notification_service.firebase_admin")
    def test_inicializacao_firebase_arquivo_nao_encontrado(
        self, mock_firebase, mock_exists
    ):
        """Testa falha quando arquivo de credenciais não existe."""
        # Configurar mocks
        mock_exists.return_value = False
        mock_firebase._apps = []

        # Executar
        result = NotificationService._ensure_firebase_initialized()

        # Verificar
        self.assertFalse(result)
        self.assertFalse(NotificationService._initialized)
        mock_firebase.initialize_app.assert_not_called()

    @patch("core.services.notification_service.firebase_admin")
    @patch("core.services.notification_service.credentials")
    @patch("core.services.notification_service.Path.exists")
    def test_inicializacao_firebase_erro_excecao(
        self, mock_exists, mock_credentials, mock_firebase
    ):
        """Testa tratamento de exceção durante inicialização."""
        # Configurar mocks para gerar exceção
        mock_exists.return_value = True
        mock_firebase._apps = []
        mock_firebase.initialize_app.side_effect = Exception("Erro de inicialização")

        # Executar
        result = NotificationService._ensure_firebase_initialized()

        # Verificar
        self.assertFalse(result)

    @patch("core.services.notification_service.messaging.send")
    @patch("core.services.notification_service.firebase_admin")
    @patch("core.services.notification_service.credentials")
    @patch("core.services.notification_service.Path.exists")
    def test_enviar_notificacao_sucesso(
        self, mock_exists, mock_credentials, mock_firebase, mock_send
    ):
        """Testa envio bem-sucedido de notificação."""
        # Configurar mocks
        mock_exists.return_value = True
        mock_firebase._apps = []
        mock_send.return_value = "message_id_123"

        # Executar
        result = NotificationService.enviar_notificacao_escala(self.musico, self.evento)

        # Verificar
        self.assertTrue(result)
        mock_send.assert_called_once()

        # Verificar estrutura da mensagem
        call_args = mock_send.call_args[0][0]
        self.assertIsNotNone(call_args.notification)
        self.assertIn("Nova Escala", call_args.notification.title)
        self.assertEqual(call_args.token, self.musico.fcm_token)
        self.assertEqual(call_args.data["tipo"], "nova_escala")
        self.assertEqual(call_args.data["evento_nome"], self.evento.nome)

    @patch("core.services.notification_service.firebase_admin")
    def test_enviar_notificacao_sem_token_fcm(self, mock_firebase):
        """Testa que não envia notificação se músico não tem token FCM."""
        # Remover token FCM do músico
        self.musico.fcm_token = None
        self.musico.save()

        # Executar
        result = NotificationService.enviar_notificacao_escala(self.musico, self.evento)

        # Verificar
        self.assertFalse(result)

    @patch("core.services.notification_service.firebase_admin")
    def test_enviar_notificacao_sem_token_fcm_vazio(self, mock_firebase):
        """Testa que não envia notificação se músico tem token vazio."""
        # Token vazio
        self.musico.fcm_token = ""
        self.musico.save()

        # Executar
        result = NotificationService.enviar_notificacao_escala(self.musico, self.evento)

        # Verificar
        self.assertFalse(result)

    @patch("core.services.notification_service.Path.exists")
    @patch("core.services.notification_service.firebase_admin")
    def test_enviar_notificacao_firebase_nao_inicializado(
        self, mock_firebase, mock_exists
    ):
        """Testa falha no envio quando Firebase não pode ser inicializado."""
        # Configurar mocks para falhar inicialização
        mock_exists.return_value = False
        mock_firebase._apps = []

        # Executar
        result = NotificationService.enviar_notificacao_escala(self.musico, self.evento)

        # Verificar
        self.assertFalse(result)

    @patch("core.services.notification_service.messaging.send")
    @patch("core.services.notification_service.firebase_admin")
    @patch("core.services.notification_service.credentials")
    @patch("core.services.notification_service.Path.exists")
    def test_enviar_notificacao_erro_envio(
        self, mock_exists, mock_credentials, mock_firebase, mock_send
    ):
        """Testa tratamento de erro durante envio da notificação."""
        # Configurar mocks
        mock_exists.return_value = True
        mock_firebase._apps = []
        mock_send.side_effect = Exception("Erro ao enviar notificação")

        # Executar
        result = NotificationService.enviar_notificacao_escala(self.musico, self.evento)

        # Verificar
        self.assertFalse(result)

    @patch("core.services.notification_service.messaging.send")
    @patch("core.services.notification_service.firebase_admin")
    @patch("core.services.notification_service.credentials")
    @patch("core.services.notification_service.Path.exists")
    def test_enviar_notificacao_formatacao_data(
        self, mock_exists, mock_credentials, mock_firebase, mock_send
    ):
        """Testa formatação correta da data na notificação."""
        from datetime import datetime

        from django.conf import settings

        # Configurar mocks
        mock_exists.return_value = True
        mock_firebase._apps = []
        mock_send.return_value = "message_id_123"

        # Data específica para teste - funciona com USE_TZ True ou False
        if settings.USE_TZ:
            # Se USE_TZ estiver ativo, usar timezone aware
            data_naive = datetime(2026, 3, 15, 19, 30)
            data_especifica = timezone.make_aware(data_naive)
        else:
            # Se USE_TZ estiver desativado, usar datetime naive
            data_especifica = datetime(2026, 3, 15, 19, 30)

        self.evento.data_evento = data_especifica
        self.evento.save()

        # Executar
        result = NotificationService.enviar_notificacao_escala(self.musico, self.evento)

        # Verificar
        self.assertTrue(result)
        call_args = mock_send.call_args[0][0]

        # Verificar que a data está presente na mensagem
        self.assertIn("15/03/2026", call_args.notification.body)

    @patch("core.services.notification_service.messaging.send")
    @patch("core.services.notification_service.firebase_admin")
    @patch("core.services.notification_service.credentials")
    @patch("core.services.notification_service.Path.exists")
    def test_enviar_notificacao_multiplos_musicos(
        self, mock_exists, mock_credentials, mock_firebase, mock_send
    ):
        """Testa envio de notificações para múltiplos músicos."""
        # Configurar mocks
        mock_exists.return_value = True
        mock_firebase._apps = []
        mock_send.return_value = "message_id_123"

        # Criar segundo músico
        user2 = User.objects.create_user(
            username="musico2", email="test2@test.com", password="testpass123"
        )
        musico2 = Musico.objects.create(
            user=user2,
            nome="Maria Santos",
            status="ATIVO",
            instrumento_principal=self.instrumento,
            fcm_token="fake_fcm_token_987654321",
        )

        # Enviar para ambos
        result1 = NotificationService.enviar_notificacao_escala(
            self.musico, self.evento
        )
        result2 = NotificationService.enviar_notificacao_escala(musico2, self.evento)

        # Verificar
        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertEqual(mock_send.call_count, 2)

    @patch("core.services.notification_service.firebase_admin")
    def test_estado_inicializacao_persiste_entre_chamadas(self, mock_firebase):
        """Testa que estado de inicialização persiste entre chamadas."""
        # Simular Firebase já inicializado
        mock_firebase._apps = [Mock()]

        # Primeira chamada
        result1 = NotificationService._ensure_firebase_initialized()
        self.assertTrue(result1)
        self.assertTrue(NotificationService._initialized)

        # Segunda chamada (deve usar estado cached)
        result2 = NotificationService._ensure_firebase_initialized()
        self.assertTrue(result2)
        self.assertTrue(NotificationService._initialized)

        # Firebase initialize_app não deve ser chamado pois já estava inicializado
        mock_firebase.initialize_app.assert_not_called()
