from django.test import TestCase
from .models import Musicos, Eventos

class MusicoModelTest(TestCase):
    def setUp(self):
        Musicos.objects.create(nome="Test Musico", telefone="123456789", email="test@exemplo.com", endereco="Rua Teste")

    def test_musico_creation(self):
        musico = Musicos.objects.get(nome="Test Musico")
        self.assertEqual(musico.telefone, "123456789")