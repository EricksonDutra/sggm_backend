from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.models import Artista, Escala, Evento, Instrumento, Musica, Musico


class MusicoModelTest(TestCase):
    """Testes completos do modelo Musico."""

    def setUp(self):
        """Configuração inicial dos testes."""
        self.user = User.objects.create_user(
            username="erickson", email="erickson@email.com", password="testpass123"
        )
        self.instrumento = Instrumento.objects.create(nome="Guitarra")

    def test_criar_musico_com_sucesso(self):
        """Testa criação básica de músico."""
        musico = Musico.objects.create(
            user=self.user,
            nome="Erickson",
            telefone="9999999",
            instrumento_principal=self.instrumento,
            status="ATIVO",
        )

        self.assertEqual(musico.nome, "Erickson")
        self.assertEqual(musico.email, "erickson@email.com")
        self.assertEqual(musico.status, "ATIVO")
        self.assertEqual(musico.tipo_usuario, "MUSICO")  # Default

    def test_musico_com_valores_default(self):
        """Testa valores padrão do modelo."""
        musico = Musico.objects.create(user=self.user, nome="Teste")

        self.assertEqual(musico.status, "ATIVO")
        self.assertEqual(musico.tipo_usuario, "MUSICO")
        self.assertEqual(musico.role, "MUSICO")
        self.assertTrue(musico.precisa_mudar_senha)

    def test_email_property_retorna_email_usuario(self):
        """Testa property email."""
        musico = Musico.objects.create(user=self.user, nome="Teste")
        self.assertEqual(musico.email, "erickson@email.com")

    def test_email_property_retorna_none_sem_user(self):
        """Testa property email quando não há usuário."""
        musico = Musico(nome="Sem User", user=None)
        self.assertIsNone(musico.email)

    def test_nao_permite_user_duplicado(self):
        """Testa que não permite dois músicos com mesmo usuário."""
        Musico.objects.create(user=self.user, nome="Primeiro")

        with self.assertRaises(ValidationError):
            Musico.objects.create(user=self.user, nome="Segundo")

    def test_is_lider_para_tipo_lider(self):
        """Testa método is_lider para líder."""
        musico = Musico.objects.create(
            user=self.user, nome="Líder", tipo_usuario="LIDER"
        )
        self.assertTrue(musico.is_lider())

    def test_is_lider_para_tipo_admin(self):
        """Testa método is_lider para admin."""
        musico = Musico.objects.create(
            user=self.user, nome="Admin", tipo_usuario="ADMIN"
        )
        self.assertTrue(musico.is_lider())

    def test_is_lider_para_superuser(self):
        """Testa método is_lider para superuser."""
        self.user.is_superuser = True
        self.user.save()
        musico = Musico.objects.create(
            user=self.user, nome="Super", tipo_usuario="MUSICO"
        )
        self.assertTrue(musico.is_lider())

    def test_is_lider_false_para_musico_comum(self):
        """Testa método is_lider retorna False para músico comum."""
        musico = Musico.objects.create(
            user=self.user, nome="Músico", tipo_usuario="MUSICO"
        )
        self.assertFalse(musico.is_lider())

    def test_is_admin_para_tipo_admin(self):
        """Testa método is_admin."""
        musico = Musico.objects.create(
            user=self.user, nome="Admin", tipo_usuario="ADMIN"
        )
        self.assertTrue(musico.is_admin())

    def test_is_admin_false_para_lider(self):
        """Testa método is_admin retorna False para líder."""
        musico = Musico.objects.create(
            user=self.user, nome="Líder", tipo_usuario="LIDER"
        )
        self.assertFalse(musico.is_admin())

    def test_esta_disponivel_quando_ativo(self):
        """Testa disponibilidade para músico ativo."""
        musico = Musico.objects.create(user=self.user, nome="Ativo", status="ATIVO")
        self.assertTrue(musico.esta_disponivel())

    def test_nao_esta_disponivel_quando_inativo(self):
        """Testa disponibilidade para músico inativo."""
        musico = Musico.objects.create(user=self.user, nome="Inativo", status="INATIVO")
        self.assertFalse(musico.esta_disponivel())

    def test_nao_esta_disponivel_quando_afastado_sem_datas(self):
        """Testa disponibilidade para músico afastado sem período definido."""
        musico = Musico.objects.create(
            user=self.user, nome="Afastado", status="AFASTADO"
        )
        self.assertFalse(musico.esta_disponivel())

    def test_nao_esta_disponivel_quando_afastado_dentro_periodo(self):
        """Testa disponibilidade para músico afastado dentro do período."""
        hoje = timezone.now().date()
        musico = Musico.objects.create(
            user=self.user,
            nome="Afastado",
            status="AFASTADO",
            data_inicio_inatividade=hoje - timedelta(days=5),
            data_fim_inatividade=hoje + timedelta(days=5),
        )
        self.assertFalse(musico.esta_disponivel())

    def test_esta_disponivel_quando_afastado_fora_periodo(self):
        """Testa disponibilidade para músico afastado fora do período."""
        hoje = timezone.now().date()
        musico = Musico.objects.create(
            user=self.user,
            nome="Afastado",
            status="AFASTADO",
            data_inicio_inatividade=hoje - timedelta(days=10),
            data_fim_inatividade=hoje - timedelta(days=5),
        )
        self.assertTrue(musico.esta_disponivel())

    def test_esta_afastado_quando_status_afastado_sem_datas(self):
        """Testa método esta_afastado sem datas."""
        musico = Musico.objects.create(
            user=self.user, nome="Afastado", status="AFASTADO"
        )
        self.assertTrue(musico.esta_afastado())

    def test_nao_esta_afastado_quando_status_ativo(self):
        """Testa método esta_afastado para status ativo."""
        musico = Musico.objects.create(user=self.user, nome="Ativo", status="ATIVO")
        self.assertFalse(musico.esta_afastado())

    def test_sincronizar_grupo_musico(self):
        """Testa sincronização de grupo para músico."""
        musico = Musico.objects.create(
            user=self.user, nome="Músico", tipo_usuario="MUSICO"
        )
        self.assertTrue(self.user.groups.filter(name="Músicos").exists())

    def test_sincronizar_grupo_lider(self):
        """Testa sincronização de grupo para líder."""
        user2 = User.objects.create_user(username="lider", password="123")
        musico = Musico.objects.create(user=user2, nome="Líder", tipo_usuario="LIDER")
        self.assertTrue(user2.groups.filter(name="Lideres").exists())

    def test_sincronizar_grupo_admin(self):
        """Testa sincronização de grupo para admin."""
        user3 = User.objects.create_user(username="admin", password="123")
        musico = Musico.objects.create(user=user3, nome="Admin", tipo_usuario="ADMIN")
        self.assertTrue(user3.groups.filter(name="Administradores").exists())
        user3.refresh_from_db()
        self.assertTrue(user3.is_staff)

    def test_str_retorna_nome(self):
        """Testa método __str__."""
        musico = Musico.objects.create(user=self.user, nome="João Silva")
        self.assertEqual(str(musico), "João Silva")


class InstrumentoModelTest(TestCase):
    """Testes do modelo Instrumento."""

    def test_criar_instrumento(self):
        """Testa criação de instrumento."""
        instrumento = Instrumento.objects.create(nome="Bateria")
        self.assertEqual(instrumento.nome, "Bateria")

    def test_instrumento_nome_unico(self):
        """Testa constraint de nome único."""
        Instrumento.objects.create(nome="Violão")
        with self.assertRaises(IntegrityError):
            Instrumento.objects.create(nome="Violão")

    def test_str_retorna_nome(self):
        """Testa método __str__."""
        instrumento = Instrumento.objects.create(nome="Piano")
        self.assertEqual(str(instrumento), "Piano")


class ArtistaModelTest(TestCase):
    """Testes do modelo Artista."""

    def test_criar_artista(self):
        """Testa criação de artista."""
        artista = Artista.objects.create(nome="Hillsong United")
        self.assertEqual(artista.nome, "Hillsong United")
        self.assertIsNotNone(artista.criado_em)
        self.assertIsNotNone(artista.atualizado_em)

    def test_artista_nome_unico(self):
        """Testa constraint de nome único."""
        Artista.objects.create(nome="Bethel Music")
        with self.assertRaises(IntegrityError):
            Artista.objects.create(nome="Bethel Music")

    def test_clean_remove_espacos_extras(self):
        """Testa que clean() remove espaços extras."""
        artista = Artista(nome="  Elevation Worship  ")
        artista.clean()
        self.assertEqual(artista.nome, "Elevation Worship")

    def test_str_retorna_nome(self):
        """Testa método __str__."""
        artista = Artista.objects.create(nome="Passion")
        self.assertEqual(str(artista), "Passion")


class MusicaModelTest(TestCase):
    """Testes do modelo Musica."""

    def setUp(self):
        """Configuração inicial."""
        self.artista = Artista.objects.create(nome="Hillsong")

    def test_criar_musica(self):
        """Testa criação de música."""
        musica = Musica.objects.create(
            titulo="Oceans",
            artista=self.artista,
            tom="D",
            link_cifra="https://example.com/cifra",
            link_youtube="https://youtube.com/watch",
        )
        self.assertEqual(musica.titulo, "Oceans")
        self.assertEqual(musica.artista, self.artista)
        self.assertEqual(musica.tom, "D")

    def test_musica_unique_together_titulo_artista(self):
        """Testa constraint unique_together."""
        Musica.objects.create(titulo="Alive", artista=self.artista)
        with self.assertRaises(IntegrityError):
            Musica.objects.create(titulo="Alive", artista=self.artista)

    def test_musica_mesmo_titulo_artista_diferente(self):
        """Testa que permite mesmo título com artista diferente."""
        artista2 = Artista.objects.create(nome="Bethel")
        Musica.objects.create(titulo="Alive", artista=self.artista)
        musica2 = Musica.objects.create(titulo="Alive", artista=artista2)
        self.assertIsNotNone(musica2)

    def test_nao_permite_deletar_artista_com_musicas(self):
        """Testa PROTECT em artista com músicas."""
        Musica.objects.create(titulo="Test", artista=self.artista)
        with self.assertRaises(Exception):  # ProtectedError
            self.artista.delete()

    def test_str_retorna_titulo_artista(self):
        """Testa método __str__."""
        musica = Musica.objects.create(titulo="Cornerstone", artista=self.artista)
        self.assertEqual(str(musica), "Cornerstone - Hillsong")


class EventoModelTest(TestCase):
    """Testes do modelo Evento."""

    def setUp(self):
        """Configuração inicial."""
        self.data_evento = timezone.now() + timedelta(days=7)

    def test_criar_evento(self):
        """Testa criação de evento."""
        evento = Evento.objects.create(
            nome="Culto de Domingo",
            tipo="CULTO",
            data_evento=self.data_evento,
            local="Igreja Central",
            descricao="Culto principal",
        )
        self.assertEqual(evento.nome, "Culto de Domingo")
        self.assertEqual(evento.tipo, "CULTO")
        self.assertIsNotNone(evento.criado_em)

    def test_evento_tipo_default(self):
        """Testa valor default de tipo."""
        evento = Evento.objects.create(
            nome="Evento Teste", data_evento=self.data_evento, local="Local"
        )
        self.assertEqual(evento.tipo, "CULTO")

    def test_adicionar_musicas_repertorio(self):
        """Testa adição de músicas ao repertório."""
        evento = Evento.objects.create(
            nome="Culto", data_evento=self.data_evento, local="Igreja"
        )
        artista = Artista.objects.create(nome="Artista")
        musica1 = Musica.objects.create(titulo="Música 1", artista=artista)
        musica2 = Musica.objects.create(titulo="Música 2", artista=artista)

        evento.repertorio.add(musica1, musica2)

        self.assertEqual(evento.repertorio.count(), 2)
        self.assertIn(musica1, evento.repertorio.all())
        self.assertIn(musica2, evento.repertorio.all())

    def test_str_retorna_nome_data(self):
        """Testa método __str__."""
        from datetime import datetime

        from django.conf import settings

        # Criar data compatível com USE_TZ True ou False
        if settings.USE_TZ:
            # Se USE_TZ estiver ativo, usar timezone aware
            data = timezone.make_aware(datetime(2026, 3, 15, 19, 0))
        else:
            # Se USE_TZ estiver desativado, usar datetime naive
            data = datetime(2026, 3, 15, 19, 0)

        evento = Evento.objects.create(
            nome="Culto Especial", data_evento=data, local="Igreja"
        )

        # Verificar que __str__ contém nome e data formatada
        resultado = str(evento)
        self.assertIn("Culto Especial", resultado)
        self.assertIn("15/03/2026", resultado)


class EscalaModelTest(TestCase):
    """Testes do modelo Escala."""

    def setUp(self):
        """Configuração inicial."""
        self.user = User.objects.create_user(
            username="erickson", email="e@e.com", password="testpass123"
        )
        self.instrumento = Instrumento.objects.create(nome="Violão")
        self.musico = Musico.objects.create(
            user=self.user,
            nome="Erickson",
            telefone="999",
            instrumento_principal=self.instrumento,
            status="ATIVO",
        )
        self.evento = Evento.objects.create(
            nome="Culto Domingo",
            data_evento=timezone.now() + timedelta(days=7),
            local="Igreja",
        )

    def test_criar_escala(self):
        """Testa criação de escala."""
        escala = Escala.objects.create(
            musico=self.musico,
            evento=self.evento,
            instrumento_no_evento=self.instrumento,
            observacao="Teste",
        )
        self.assertEqual(escala.musico, self.musico)
        self.assertEqual(escala.evento, self.evento)
        self.assertFalse(escala.confirmado)  # Default False

    def test_nao_permite_duplicidade_na_escala(self):
        """Testa unique_together musico-evento."""
        Escala.objects.create(musico=self.musico, evento=self.evento)
        with self.assertRaises(ValidationError):
            Escala.objects.create(musico=self.musico, evento=self.evento)

    def test_nao_permite_musico_inativo(self):
        """Testa validação de status inativo."""
        self.musico.status = "INATIVO"
        self.musico.save()

        with self.assertRaises(ValidationError):
            Escala.objects.create(musico=self.musico, evento=self.evento)

    def test_permite_musico_ativo(self):
        """Testa criação com músico ativo."""
        self.musico.status = "ATIVO"
        self.musico.save()

        escala = Escala.objects.create(musico=self.musico, evento=self.evento)
        self.assertIsNotNone(escala)

    def test_confirmado_default_false(self):
        """Testa valor default de confirmado."""
        escala = Escala.objects.create(musico=self.musico, evento=self.evento)
        self.assertFalse(escala.confirmado)

    def test_confirmar_escala(self):
        """Testa confirmação de escala."""
        escala = Escala.objects.create(musico=self.musico, evento=self.evento)
        escala.confirmado = True
        escala.save()
        escala.refresh_from_db()
        self.assertTrue(escala.confirmado)

    def test_cascata_delete_evento(self):
        """Testa CASCADE na deleção de evento."""
        escala = Escala.objects.create(musico=self.musico, evento=self.evento)
        evento_id = self.evento.id

        self.evento.delete()

        self.assertFalse(Escala.objects.filter(id=escala.id).exists())

    def test_protect_delete_musico(self):
        """Testa PROTECT na deleção de músico."""
        Escala.objects.create(musico=self.musico, evento=self.evento)

        with self.assertRaises(Exception):  # ProtectedError
            self.musico.delete()

    def test_str_retorna_musico_evento(self):
        """Testa método __str__."""
        escala = Escala.objects.create(musico=self.musico, evento=self.evento)
        expected = f"{self.musico.nome} em {self.evento.nome}"
        self.assertEqual(str(escala), expected)

    def test_multiple_escalas_mesmo_evento(self):
        """Testa múltiplas escalas para o mesmo evento."""
        user2 = User.objects.create_user(username="maria", password="123")
        musico2 = Musico.objects.create(
            user=user2,
            nome="Maria",
            status="ATIVO",
            instrumento_principal=self.instrumento,
        )

        escala1 = Escala.objects.create(musico=self.musico, evento=self.evento)
        escala2 = Escala.objects.create(musico=musico2, evento=self.evento)

        self.assertEqual(self.evento.escalas.count(), 2)

    def test_multiple_escalas_mesmo_musico(self):
        """Testa múltiplas escalas para o mesmo músico."""
        evento2 = Evento.objects.create(
            nome="Culto Quarta",
            data_evento=timezone.now() + timedelta(days=3),
            local="Igreja",
        )

        escala1 = Escala.objects.create(musico=self.musico, evento=self.evento)
        escala2 = Escala.objects.create(musico=self.musico, evento=evento2)

        self.assertEqual(self.musico.escalas.count(), 2)
