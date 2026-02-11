from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.models import Escala, Evento, Musico
from core.services import GerenciadorEscala


class GerenciadorEscalaTest(TestCase):
    def setUp(self):
        self.musico = Musico.objects.create(nome="Erickson", email="e@e.com")
        self.evento = Evento.objects.create(
            nome="Culto Jovens",
            data_evento=timezone.now(),
            local="Templo"
        )

    def test_adicionar_musico_via_servico(self):
        escala = GerenciadorEscala.adicionar_musico_ao_evento(
            self.evento.id, self.musico.id, "Violão"
        )
        self.assertEqual(escala.instrumento_no_evento, "Violão")
        self.assertEqual(Escala.objects.count(), 1)

    def test_bloquear_conflito_escala(self):
        GerenciadorEscala.adicionar_musico_ao_evento(
            self.evento.id, self.musico.id)

        with self.assertRaises(ValidationError):
            GerenciadorEscala.adicionar_musico_ao_evento(
                self.evento.id, self.musico.id)
