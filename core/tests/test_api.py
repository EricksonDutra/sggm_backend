from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Escala, Evento, Instrumento, Musico
from SGGM import settings


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.AllowAny",
        ],
        "DEFAULT_RENDERER_CLASSES": [
            "rest_framework.renderers.JSONRenderer",
        ],
        "DEFAULT_PARSER_CLASSES": [
            "rest_framework.parsers.JSONParser",
        ],
    }
)
class EscalaAPITest(APITestCase):
    def setUp(self):
        # Criar usuário para o músico
        self.musico_user = User.objects.create_user(
            username="musico_erickson",
            email="erickson@teste.com",
            password="testpass123",
        )

        instrumento = Instrumento.objects.create(nome="Contra baixo")

        self.musico = Musico.objects.create(
            user=self.musico_user,
            nome="Erickson",
            telefone="99999999",
            instrumento_principal=instrumento,
            status="ATIVO",
        )

        self.evento = Evento.objects.create(
            nome="Culto de Domingo",
            data_evento=timezone.now(),
            local="Igreja Principal",
        )

    def test_criar_escala_api_sucesso(self):
        url = reverse("escala-list")
        data = {"musico": self.musico.id, "evento": self.evento.id}

        response = self.client.post(url, data, format="json")

        # ✅ Debug para ver o erro
        if response.status_code != status.HTTP_201_CREATED:
            print(f"\n❌ Status: {response.status_code}")
            print(f"❌ Data: {response.data}")
            print(f"❌ Settings REST_FRAMEWORK: {settings.REST_FRAMEWORK}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_impedir_escala_duplicada_api(self):
        Escala.objects.create(musico=self.musico, evento=self.evento)

        url = reverse("escala-list")
        data = {"musico": self.musico.id, "evento": self.evento.id}

        response = self.client.post(url, data, format="json")

        # ✅ Debug
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print(f"\n❌ Status: {response.status_code}")
            print(f"❌ Data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EventoAPITest(APITestCase):
    def setUp(self):
        # ✅ Criar usuário e autenticar
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_listar_eventos_json(self):
        """Verifica se o endpoint de eventos retorna a lista correta"""
        Evento.objects.create(
            nome="Ensaio Geral", data_evento=timezone.now(), local="Sala 1"
        )

        url = reverse("evento-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
