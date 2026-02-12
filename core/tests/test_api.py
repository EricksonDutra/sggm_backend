from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Escala, Evento, Musico, Instrumento


class EscalaAPITest(APITestCase):
    def setUp(self):
        instrumento = Instrumento.objects.create(nome="Contra baixo")

        # 1. Prepara o terreno (Massa de dados)
        self.musico = Musico.objects.create(
            nome="Erickson",
            email="erickson@teste.com",
            telefone="99999999",
            instrumento_principal=instrumento
        )
        self.evento = Evento.objects.create(
            nome="Culto Santa Ceia",
            data_evento=timezone.now(),
            local="Templo Principal"
        )
        # O 'reverse' busca a URL pelo nome definido no router (ex: /api/escalas/)
        self.url_escalas = reverse('escala-list')

    def test_criar_escala_api_sucesso(self):
        """
        Cenário: Flutter envia um POST com IDs válidos.
        Resultado Esperado: 201 Created e o JSON de volta com os nomes.
        """
        data = {
            "musico": self.musico.id,
            "evento": self.evento.id,
            "instrumento_no_evento": "Baixo"
        }
        response = self.client.post(self.url_escalas, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Escala.objects.count(), 1)
        # Verifica se o Serializer trouxe o campo extra 'musico_nome' (read_only)
        self.assertEqual(response.data['musico_nome'], "Erickson")

    def test_impedir_escala_duplicada_api(self):
        """
        Cenário: Tentar escalar o mesmo músico no mesmo evento 2x via API.
        Resultado Esperado: 400 Bad Request (Validação do Serializer/Model).
        """
        # 1. Cria a primeira vez no banco
        Escala.objects.create(musico=self.musico, evento=self.evento)

        # 2. Tenta criar de novo via POST
        data = {
            "musico": self.musico.id,
            "evento": self.evento.id
        }
        response = self.client.post(self.url_escalas, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EventoAPITest(APITestCase):
    def test_listar_eventos_json(self):
        """Verifica se o endpoint de eventos retorna a lista correta"""
        Evento.objects.create(nome="Ensaio Geral",
                              data_evento=timezone.now(), local="Sala 1")

        url = reverse('evento-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
