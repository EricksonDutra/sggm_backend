from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.models import Escala, Evento, Instrumento, Musico


class MusicoModelTest(TestCase):
    def test_criar_musico_com_sucesso(self):
        # ✅ Criar usuário primeiro
        user = User.objects.create_user(
            username="erickson", email="erickson@email.com", password="testpass123"
        )

        instrumento = Instrumento.objects.create(nome="Guitarra")

        musico = Musico.objects.create(
            user=user,  # ✅ Vincular usuário
            nome="Erickson",
            email="erickson@email.com",
            telefone="9999999",
            instrumento_principal=instrumento,
        )

        self.assertEqual(musico.nome, "Erickson")
        self.assertEqual(musico.email, "erickson@email.com")

    def test_email_deve_ser_unico(self):
        """
        Testa que usernames devem ser únicos no Django.
        (Email não tem constraint de unicidade por padrão no User do Django)
        """
        user1 = User.objects.create_user(
            username="user1", email="teste@email.com", password="testpass123"
        )
        Musico.objects.create(user=user1, nome="M1")

        from django.db import IntegrityError

        # ✅ Username deve ser único
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="user1",  # ✅ Username duplicado
                email="outro@email.com",
                password="testpass123",
            )


class EscalaModelTest(TestCase):
    def setUp(self):
        # ✅ Criar usuário no setUp
        self.user = User.objects.create_user(
            username="erickson", email="e@e.com", password="testpass123"
        )

        self.instrumento = Instrumento.objects.create(nome="Violão")

        self.musico = Musico.objects.create(
            user=self.user,  # ✅ Vincular usuário
            nome="Erickson",
            email="e@e.com",
            telefone="999",
            instrumento_principal=self.instrumento,
            status="ATIVO",
        )

        self.evento = Evento.objects.create(
            nome="Culto Domingo", data_evento=timezone.now(), local="Igreja"
        )

    def test_nao_permite_duplicidade_na_escala(self):
        Escala.objects.create(musico=self.musico, evento=self.evento)

        with self.assertRaises(Exception):
            Escala.objects.create(musico=self.musico, evento=self.evento)

    def test_nao_permite_musico_inativo(self):
        self.musico.status = "INATIVO"
        self.musico.save()

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            Escala.objects.create(musico=self.musico, evento=self.evento)

    def test_permite_musico_ativo(self):
        self.musico.status = "ATIVO"
        self.musico.save()

        escala = Escala.objects.create(musico=self.musico, evento=self.evento)
        self.assertIsNotNone(escala)
