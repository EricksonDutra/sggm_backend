from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from core.models import Escala, Evento, Musico, Instrumento


class MusicoModelTest(TestCase):

    def test_criar_musico_com_sucesso(self):
        instrumento = Instrumento.objects.create(nome="Guitarra")

        musico = Musico.objects.create(
            nome="Erickson",
            email="erickson@email.com",
            telefone="9999999",
            instrumento_principal=instrumento
        )

        self.assertEqual(musico.nome, "Erickson")

    def test_email_deve_ser_unico(self):
        Musico.objects.create(nome="M1", email="teste@email.com")

        with self.assertRaises(ValidationError):
            Musico.objects.create(nome="M2", email="teste@email.com")


class EscalaModelTest(TestCase):

    def setUp(self):
        self.instrumento = Instrumento.objects.create(nome="Violão")

        self.musico = Musico.objects.create(
            nome="Erickson",
            email="e@e.com",
            telefone="999",
            instrumento_principal=self.instrumento
        )

        self.evento = Evento.objects.create(
            nome="Culto Domingo",
            data_evento=timezone.now() + timedelta(days=1),
            local="Igreja Sede"
        )

    def test_nao_permite_duplicidade_na_escala(self):
        Escala.objects.create(
            musico=self.musico,
            evento=self.evento,
            instrumento_no_evento=self.instrumento
        )

        with self.assertRaises(ValidationError):
            Escala.objects.create(
                musico=self.musico,
                evento=self.evento,
                instrumento_no_evento=self.instrumento
            )

    def test_nao_permite_musico_inativo(self):
        self.musico.status = "INATIVO"
        self.musico.save()

        escala = Escala(
            musico=self.musico,
            evento=self.evento,
            instrumento_no_evento=self.instrumento
        )

        with self.assertRaises(ValidationError):
            escala.full_clean()

    def test_nao_permite_musico_afastado_no_periodo(self):
        self.musico.status = "AFASTADO"
        self.musico.data_inicio_inatividade = timezone.now().date()
        self.musico.data_fim_inatividade = (
            timezone.now() + timedelta(days=5)
        ).date()
        self.musico.save()

        escala = Escala(
            musico=self.musico,
            evento=self.evento,
            instrumento_no_evento=self.instrumento
        )

        with self.assertRaises(ValidationError):
            escala.full_clean()

    def test_permite_musico_ativo(self):
        escala = Escala(
            musico=self.musico,
            evento=self.evento,
            instrumento_no_evento=self.instrumento
        )

        try:
            escala.full_clean()
        except ValidationError:
            self.fail("Músico ativo não deveria gerar erro")
