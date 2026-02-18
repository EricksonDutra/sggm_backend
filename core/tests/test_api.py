from django.contrib.auth.models import Permission, User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Escala, Evento, Instrumento, Musica, Musico


class EscalaAPITest(APITestCase):
    def setUp(self):
        self.musico_user = User.objects.create_user(
            username="musico_erickson",
            email="erickson@teste.com",
            password="testpass123",
        )

        instrumento = Instrumento.objects.create(nome="Contra baixo")

        self.musico, created = Musico.objects.update_or_create(
            user=self.musico_user,
            defaults={
                "nome": "Erickson",
                "telefone": "99999999",
                "instrumento_principal": instrumento,
                "status": "ATIVO",
                "tipo_usuario": "LIDER",
            },
        )

        # 🔐 Gerar token JWT real
        refresh = RefreshToken.for_user(self.musico_user)
        access_token = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.evento = Evento.objects.create(
            nome="Culto de Domingo",
            data_evento=timezone.now() + timezone.timedelta(days=1),
            local="Igreja Principal",
        )

        self.client.force_authenticate(user=self.musico_user)

    def test_criar_escala_api_sucesso(self):
        url = reverse("escala-list")
        data = {"musico": self.musico.id, "evento": self.evento.id}

        response = self.client.post(url, data, format="json")

        # ✅ Debug para ver o erro
        if response.status_code != status.HTTP_201_CREATED:
            print(f"\n❌ Status: {response.status_code}")
            print(f"❌ Data: {response.data}")

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

    def test_musico_confirma_propria_escala(self):
        self.musico.tipo_usuario = "MUSICO"
        self.musico.save()

        escala = Escala.objects.create(musico=self.musico, evento=self.evento)

        url = reverse("escala-confirmar", args=[escala.id])

        response = self.client.post(url, {"confirmado": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        escala.refresh_from_db()
        self.assertTrue(escala.confirmado)

    def test_musico_nao_pode_confirmar_escala_de_outro(self):
        # ✅ Mudar o músico atual para tipo MUSICO (não LIDER)
        self.musico.tipo_usuario = "MUSICO"
        self.musico.save()

        outro_user = User.objects.create_user("outro", password="123456")
        outro_instrumento = Instrumento.objects.create(nome="Guitarra")
        outro_musico = Musico.objects.create(
            user=outro_user,
            nome="Outro",
            status="ATIVO",
            instrumento_principal=outro_instrumento,
        )

        escala = Escala.objects.create(musico=outro_musico, evento=self.evento)

        url = reverse("escala-confirmar", args=[escala.id])
        response = self.client.post(url, {"confirmado": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EventoAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
        )

        # Criar instrumento e músico para o usuário
        instrumento = Instrumento.objects.create(nome="Teclado")
        self.musico = Musico.objects.create(
            user=self.user,
            nome="Test User",
            status="ATIVO",
            tipo_usuario="LIDER",
            instrumento_principal=instrumento,
        )

        # Criar evento para os testes
        self.evento = Evento.objects.create(
            nome="Evento Teste",
            data_evento=timezone.now() + timezone.timedelta(days=1),
            local="Sala de Ensaio",
        )

        self.client.force_authenticate(user=self.user)

        # 🔑 Permissão para visualizar eventos
        permissao = Permission.objects.get(codename="view_evento")
        self.user.user_permissions.add(permissao)

    def test_listar_eventos_json(self):
        Evento.objects.create(
            nome="Ensaio Geral",
            data_evento=timezone.now() + timezone.timedelta(days=2),
            local="Sala 1",
        )

        url = reverse("evento-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_adicionar_repertorio_lista_vazia(self):
        url = reverse("evento-adicionar-repertorio", args=[self.evento.id])
        response = self.client.post(url, {"musicas": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adicionar_repertorio_tipo_invalido(self):
        url = reverse("evento-adicionar-repertorio", args=[self.evento.id])
        response = self.client.post(url, {"musicas": "errado"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adicionar_repertorio_musica_inexistente(self):
        url = reverse("evento-adicionar-repertorio", args=[self.evento.id])
        response = self.client.post(url, {"musicas": [999]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adicionar_repertorio_sucesso(self):
        from core.models import Artista

        artista = Artista.objects.create(nome="Teste Artista")
        musica = Musica.objects.create(titulo="Teste", artista=artista)

        url = reverse("evento-adicionar-repertorio", args=[self.evento.id])
        response = self.client.post(url, {"musicas": [musica.id]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.evento.repertorio.count(), 1)

    def test_listar_proximos_eventos(self):
        Evento.objects.create(
            nome="Evento Futuro",
            data_evento=timezone.now() + timezone.timedelta(days=5),
            local="Sala",
        )

        url = reverse("evento-proximos")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


class MusicoAPITest(APITestCase):
    def setUp(self):
        # Criar usuário e músico
        self.user = User.objects.create_user(
            username="musico_test",
            email="musico@test.com",
            password="testpass123",
        )

        instrumento = Instrumento.objects.create(nome="Bateria")
        self.musico = Musico.objects.create(
            user=self.user,
            nome="Músico Teste",
            status="ATIVO",
            tipo_usuario="MUSICO",
            instrumento_principal=instrumento,
        )

        # Autenticar
        self.client.force_authenticate(user=self.user)

    def test_mudar_senha_incorreta(self):
        url = reverse("musico-mudar-senha")

        response = self.client.post(
            url,
            {
                "senha_atual": "errada",
                "senha_nova": "nova12345",
                "confirmar_senha": "nova12345",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mudar_senha_sucesso(self):
        url = reverse("musico-mudar-senha")

        response = self.client.post(
            url,
            {
                "senha_atual": "testpass123",
                "senha_nova": "nova12345",
                "confirmar_senha": "nova12345",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_me_retorna_perfil(self):
        url = reverse("musico-me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.musico.id)
        self.assertEqual(response.data["nome"], self.musico.nome)
