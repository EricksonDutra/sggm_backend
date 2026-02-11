from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.models import Escala, Evento, Musico


class MusicoModelTest(TestCase):
    def test_criar_musico_com_sucesso(self):
        musico = Musico.objects.create(
            nome="Erickson",
            email="erickson@email.com",
            telefone="9999999",
            instrumento_principal="Guitarra"
        )
        self.assertEqual(musico.nome, "Erickson")

    def test_email_deve_ser_unico(self):
        Musico.objects.create(nome="M1", email="teste@email.com")
        with self.assertRaises(IntegrityError):
            Musico.objects.create(nome="M2", email="teste@email.com")


class EscalaModelTest(TestCase):
    def setUp(self):
        self.musico = Musico.objects.create(nome="Erickson", email="e@e.com")
        self.evento = Evento.objects.create(
            nome="Culto Domingo",
            data_evento=timezone.now(),  # Use timezone.now()
            local="Igreja Sede"
        )

    def test_nao_permite_duplicidade_na_escala(self):
        Escala.objects.create(musico=self.musico, evento=self.evento)

        with self.assertRaises(IntegrityError):
            Escala.objects.create(musico=self.musico, evento=self.evento)
