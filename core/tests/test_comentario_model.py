from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.models import (
    Artista,
    ComentarioPerformance,
    Escala,
    Evento,
    Instrumento,
    Musica,
    Musico,
    ReacaoComentario,
)


class ComentarioPerformanceModelTest(TestCase):
    """Testes do modelo ComentarioPerformance."""

    def setUp(self):
        """Fixtures compartilhadas por todos os testes."""
        # Autor (músico comum)
        self.user_autor = User.objects.create_user(
            username="autor", email="autor@test.com", password="testpass123"
        )
        instrumento = Instrumento.objects.create(nome="Violão")
        self.autor = Musico.objects.create(
            user=self.user_autor,
            nome="Autor",
            instrumento_principal=instrumento,
            status="ATIVO",
            tipo_usuario="MUSICO",
        )

        # Artista e música
        self.artista = Artista.objects.create(nome="Hillsong")
        self.musica = Musica.objects.create(titulo="Oceans", artista=self.artista)

        # Evento já ocorrido (no passado) — permite comentários
        self.evento_passado = Evento.objects.create(
            nome="Culto de Domingo",
            data_evento=timezone.now() - timedelta(hours=2),
            local="Igreja",
        )
        self.evento_passado.repertorio.add(self.musica)

        # Evento futuro — bloqueia comentários
        self.evento_futuro = Evento.objects.create(
            nome="Culto Próximo",
            data_evento=timezone.now() + timedelta(days=7),
            local="Igreja",
        )
        self.evento_futuro.repertorio.add(self.musica)

    # ------------------------------------------------------------------
    # Criação básica
    # ------------------------------------------------------------------

    def test_criar_comentario_com_sucesso(self):
        """Comentário válido deve ser criado sem erros."""
        comentario = ComentarioPerformance.objects.create(
            evento=self.evento_passado,
            musica=self.musica,
            autor=self.autor,
            texto="Ótima performance hoje!",
        )
        self.assertEqual(comentario.texto, "Ótima performance hoje!")
        self.assertEqual(comentario.autor, self.autor)
        self.assertIsNotNone(comentario.criado_em)
        self.assertIsNotNone(comentario.editado_em)

    def test_str_retorna_representacao_legivel(self):
        """__str__ deve conter autor, música e evento."""
        comentario = ComentarioPerformance.objects.create(
            evento=self.evento_passado,
            musica=self.musica,
            autor=self.autor,
            texto="Bom trabalho!",
        )
        resultado = str(comentario)
        self.assertIn(self.autor.nome, resultado)
        self.assertIn(self.musica.titulo, resultado)
        self.assertIn(self.evento_passado.nome, resultado)

    # ------------------------------------------------------------------
    # Validação: evento no futuro
    # ------------------------------------------------------------------

    def test_bloqueia_comentario_antes_do_evento(self):
        """clean() deve rejeitar comentário antes do início do evento."""
        comentario = ComentarioPerformance(
            evento=self.evento_futuro,
            musica=self.musica,
            autor=self.autor,
            texto="Empolgado!",
        )
        with self.assertRaises(ValidationError):
            comentario.full_clean()

    def test_permite_comentario_apos_evento(self):
        """clean() não deve lançar exceção para evento já ocorrido."""
        comentario = ComentarioPerformance(
            evento=self.evento_passado,
            musica=self.musica,
            autor=self.autor,
            texto="Foi incrível!",
        )
        # Não deve lançar exceção
        comentario.full_clean()

    # ------------------------------------------------------------------
    # Validação: música no repertório
    # ------------------------------------------------------------------

    def test_bloqueia_musica_fora_do_repertorio(self):
        """clean() deve rejeitar música que não está no repertório."""
        outra_musica = Musica.objects.create(
            titulo="Amazing Grace", artista=self.artista
        )
        # outra_musica NÃO está no repertório do evento_passado
        comentario = ComentarioPerformance(
            evento=self.evento_passado,
            musica=outra_musica,
            autor=self.autor,
            texto="Texto qualquer",
        )
        with self.assertRaises(ValidationError):
            comentario.full_clean()

    def test_permite_musica_no_repertorio(self):
        """clean() não deve rejeitar música que está no repertório."""
        comentario = ComentarioPerformance(
            evento=self.evento_passado,
            musica=self.musica,
            autor=self.autor,
            texto="Texto qualquer",
        )
        comentario.full_clean()  # não deve lançar

    # ------------------------------------------------------------------
    # CASCADE
    # ------------------------------------------------------------------

    def test_cascade_deleta_comentario_ao_deletar_evento(self):
        """Deletar evento deve apagar comentários vinculados."""
        comentario = ComentarioPerformance.objects.create(
            evento=self.evento_passado,
            musica=self.musica,
            autor=self.autor,
            texto="Texto",
        )
        self.evento_passado.delete()
        self.assertFalse(
            ComentarioPerformance.objects.filter(pk=comentario.pk).exists()
        )

    def test_cascade_deleta_comentario_ao_deletar_musica(self):
        """Deletar música deve apagar comentários vinculados."""
        comentario = ComentarioPerformance.objects.create(
            evento=self.evento_passado,
            musica=self.musica,
            autor=self.autor,
            texto="Texto",
        )
        self.musica.delete()
        self.assertFalse(
            ComentarioPerformance.objects.filter(pk=comentario.pk).exists()
        )

    def test_autor_set_null_ao_deletar_musico(self):
        """Deletar músico deve setar autor=None (SET_NULL)."""
        comentario = ComentarioPerformance.objects.create(
            evento=self.evento_passado,
            musica=self.musica,
            autor=self.autor,
            texto="Texto",
        )
        self.autor.delete()
        comentario.refresh_from_db()
        self.assertIsNone(comentario.autor)

    # ------------------------------------------------------------------
    # Ordenação
    # ------------------------------------------------------------------

    def test_ordenacao_padrao_mais_recente_primeiro(self):
        """Comentários devem ser listados do mais recente para o mais antigo."""
        c1 = ComentarioPerformance.objects.create(
            evento=self.evento_passado,
            musica=self.musica,
            autor=self.autor,
            texto="Primeiro",
        )
        c2 = ComentarioPerformance.objects.create(
            evento=self.evento_passado,
            musica=self.musica,
            autor=self.autor,
            texto="Segundo",
        )
        lista = list(ComentarioPerformance.objects.all())
        self.assertEqual(lista[0].pk, c2.pk)
        self.assertEqual(lista[1].pk, c1.pk)


class ReacaoComentarioModelTest(TestCase):
    """Testes do modelo ReacaoComentario."""

    def setUp(self):
        user1 = User.objects.create_user(username="u1", password="123")
        user2 = User.objects.create_user(username="u2", password="123")
        instrumento = Instrumento.objects.create(nome="Bateria")

        self.musico1 = Musico.objects.create(
            user=user1,
            nome="Musico 1",
            instrumento_principal=instrumento,
            status="ATIVO",
        )
        self.musico2 = Musico.objects.create(
            user=user2,
            nome="Musico 2",
            instrumento_principal=instrumento,
            status="ATIVO",
        )

        artista = Artista.objects.create(nome="Artista Teste")
        musica = Musica.objects.create(titulo="Música Teste", artista=artista)
        evento = Evento.objects.create(
            nome="Evento Teste",
            data_evento=timezone.now() - timedelta(hours=1),
            local="Igreja",
        )
        evento.repertorio.add(musica)

        self.comentario = ComentarioPerformance.objects.create(
            evento=evento, musica=musica, autor=self.musico1, texto="Bom!"
        )

    def test_criar_reacao_com_sucesso(self):
        """Reação válida deve ser criada."""
        reacao = ReacaoComentario.objects.create(
            comentario=self.comentario, musico=self.musico1
        )
        self.assertEqual(reacao.musico, self.musico1)
        self.assertIsNotNone(reacao.criado_em)

    def test_unique_together_impede_reacao_duplicada(self):
        """Mesmo músico não pode curtir o mesmo comentário duas vezes."""
        ReacaoComentario.objects.create(comentario=self.comentario, musico=self.musico1)
        with self.assertRaises(IntegrityError):
            ReacaoComentario.objects.create(
                comentario=self.comentario, musico=self.musico1
            )

    def test_musicos_diferentes_podem_reagir_ao_mesmo_comentario(self):
        """Dois músicos distintos podem curtir o mesmo comentário."""
        ReacaoComentario.objects.create(comentario=self.comentario, musico=self.musico1)
        ReacaoComentario.objects.create(comentario=self.comentario, musico=self.musico2)
        self.assertEqual(self.comentario.reacoes.count(), 2)

    def test_cascade_deleta_reacao_ao_deletar_comentario(self):
        """Deletar comentário deve apagar reações vinculadas."""
        ReacaoComentario.objects.create(comentario=self.comentario, musico=self.musico1)
        self.comentario.delete()
        self.assertEqual(ReacaoComentario.objects.count(), 0)

    def test_str_retorna_representacao_legivel(self):
        """__str__ deve mencionar o músico."""
        reacao = ReacaoComentario.objects.create(
            comentario=self.comentario, musico=self.musico1
        )
        self.assertIn(self.musico1.nome, str(reacao))
