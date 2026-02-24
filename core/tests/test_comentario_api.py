from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import (
    Artista,
    ComentarioPerformance,
    Evento,
    Instrumento,
    Musica,
    Musico,
    ReacaoComentario,
)


class ComentarioPerformanceAPITest(APITestCase):
    """Testes de endpoint para ComentarioPerformance."""

    def setUp(self):
        instrumento = Instrumento.objects.create(nome="Teclado")

        # Músico comum (autor)
        self.user_autor = User.objects.create_user(
            username="autor", email="autor@test.com", password="pass123"
        )
        self.musico_autor = Musico.objects.create(
            user=self.user_autor,
            nome="Autor",
            status="ATIVO",
            tipo_usuario="MUSICO",
            instrumento_principal=instrumento,
        )

        # Líder
        self.user_lider = User.objects.create_user(
            username="lider", email="lider@test.com", password="pass123"
        )
        self.lider = Musico.objects.create(
            user=self.user_lider,
            nome="Lider",
            status="ATIVO",
            tipo_usuario="LIDER",
            instrumento_principal=instrumento,
        )

        # Terceiro músico (sem vínculo com o comentário)
        self.user_outro = User.objects.create_user(
            username="outro", email="outro@test.com", password="pass123"
        )
        self.outro = Musico.objects.create(
            user=self.user_outro,
            nome="Outro",
            status="ATIVO",
            tipo_usuario="MUSICO",
            instrumento_principal=instrumento,
        )

        # Artista, música e evento
        artista = Artista.objects.create(nome="Hillsong")
        self.musica = Musica.objects.create(titulo="Oceans", artista=artista)
        self.musica_fora = Musica.objects.create(titulo="Fora do Rep", artista=artista)

        self.evento = Evento.objects.create(
            nome="Culto Passado",
            data_evento=timezone.now() - timedelta(hours=2),
            local="Igreja",
        )
        self.evento.repertorio.add(self.musica)

        self.evento_futuro = Evento.objects.create(
            nome="Culto Futuro",
            data_evento=timezone.now() + timedelta(days=7),
            local="Igreja",
        )
        self.evento_futuro.repertorio.add(self.musica)

        # Comentário base reutilizável
        self.comentario = ComentarioPerformance.objects.create(
            evento=self.evento,
            musica=self.musica,
            autor=self.musico_autor,
            texto="Comentário inicial",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    # ------------------------------------------------------------------
    # POST /api/comentarios/ — Criar
    # ------------------------------------------------------------------

    def test_musico_cria_comentario_valido(self):
        """Músico autenticado pode criar comentário em evento passado."""
        self._auth(self.user_autor)
        url = reverse("comentarioperformance-list")
        data = {
            "evento": self.evento.id,
            "musica": self.musica.id,
            "texto": "Ótima performance!",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["autor"], self.musico_autor.id)

    def test_bloqueia_comentario_antes_do_evento(self):
        """POST para evento futuro deve retornar 400."""
        self._auth(self.user_autor)
        url = reverse("comentarioperformance-list")
        data = {
            "evento": self.evento_futuro.id,
            "musica": self.musica.id,
            "texto": "Muito animado!",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bloqueia_musica_fora_do_repertorio(self):
        """POST com música fora do repertório deve retornar 400."""
        self._auth(self.user_autor)
        url = reverse("comentarioperformance-list")
        data = {
            "evento": self.evento.id,
            "musica": self.musica_fora.id,
            "texto": "Música errada",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nao_autenticado_nao_pode_criar(self):
        """Usuário sem autenticação deve receber 401."""
        self.client.force_authenticate(user=None)
        url = reverse("comentarioperformance-list")
        data = {
            "evento": self.evento.id,
            "musica": self.musica.id,
            "texto": "Sem auth",
        }
        response = self.client.post(url, data, format="json")
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    # ------------------------------------------------------------------
    # GET /api/comentarios/ — Listar com filtros
    # ------------------------------------------------------------------

    def test_listar_comentarios_por_evento(self):
        """GET ?evento=id deve retornar apenas comentários daquele evento."""
        self._auth(self.user_autor)
        url = reverse("comentarioperformance-list") + f"?evento={self.evento.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data.get("results", response.data)
        for item in items:
            self.assertEqual(item["evento"], self.evento.id)

    def test_listar_comentarios_por_musica(self):
        """GET ?musica=id deve retornar apenas comentários daquela música."""
        self._auth(self.user_autor)
        url = reverse("comentarioperformance-list") + f"?musica={self.musica.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data.get("results", response.data)

        for item in items:
            self.assertEqual(item["musica"], self.musica.id)

    def test_resposta_contem_campos_essenciais(self):
        """GET deve retornar campos obrigatórios no payload."""
        self._auth(self.user_autor)
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for campo in [
            "id",
            "texto",
            "autor_nome",
            "total_reacoes",
            "eu_curto",
            "pode_editar",
        ]:
            self.assertIn(campo, response.data)

    # ------------------------------------------------------------------
    # PATCH /api/comentarios/{id}/ — Editar
    # ------------------------------------------------------------------

    def test_autor_pode_editar_proprio_comentario(self):
        """Autor deve conseguir editar seu comentário dentro de 24h."""
        self._auth(self.user_autor)
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.patch(url, {"texto": "Editado!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comentario.refresh_from_db()
        self.assertEqual(self.comentario.texto, "Editado!")

    def test_outro_musico_nao_pode_editar_comentario_alheio(self):
        """Músico sem ser autor deve receber 403."""
        self._auth(self.user_outro)
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.patch(url, {"texto": "Invasão!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lider_pode_editar_qualquer_comentario(self):
        """Líder deve conseguir editar comentário de qualquer músico."""
        self._auth(self.user_lider)
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.patch(
            url, {"texto": "Corrigido pelo líder"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_autor_nao_pode_editar_apos_24h(self):
        """Edição após 24h por músico comum deve retornar 403."""
        self._auth(self.user_autor)
        # Forçar criado_em para mais de 24h atrás
        ComentarioPerformance.objects.filter(pk=self.comentario.pk).update(
            criado_em=timezone.now() - timedelta(hours=25)
        )
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.patch(url, {"texto": "Tarde demais"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # DELETE /api/comentarios/{id}/ — Deletar
    # ------------------------------------------------------------------

    def test_autor_pode_deletar_proprio_comentario(self):
        """Autor pode deletar seu próprio comentário."""
        self._auth(self.user_autor)
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ComentarioPerformance.objects.filter(pk=self.comentario.pk).exists()
        )

    def test_outro_musico_nao_pode_deletar_comentario_alheio(self):
        """Músico não-autor deve receber 403 ao tentar deletar."""
        self._auth(self.user_outro)
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lider_pode_deletar_qualquer_comentario(self):
        """Líder pode deletar comentário de qualquer músico sem restrição de tempo."""
        self._auth(self.user_lider)
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_lider_pode_deletar_apos_24h(self):
        """Líder pode deletar mesmo após 24h da criação."""
        self._auth(self.user_lider)
        ComentarioPerformance.objects.filter(pk=self.comentario.pk).update(
            criado_em=timezone.now() - timedelta(hours=48)
        )
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # POST /api/comentarios/{id}/reagir/ — Toggle curtida
    # ------------------------------------------------------------------

    def test_reagir_adiciona_curtida(self):
        """Primeira chamada a /reagir/ deve adicionar a reação."""
        self._auth(self.user_outro)
        url = reverse("comentarioperformance-reagir", args=[self.comentario.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "adicionada")
        self.assertEqual(response.data["total_reacoes"], 1)

    def test_reagir_remove_curtida_se_ja_existe(self):
        """Segunda chamada a /reagir/ deve remover a reação (toggle)."""
        self._auth(self.user_outro)
        ReacaoComentario.objects.create(comentario=self.comentario, musico=self.outro)
        url = reverse("comentarioperformance-reagir", args=[self.comentario.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "removida")
        self.assertEqual(response.data["total_reacoes"], 0)

    def test_nao_autenticado_nao_pode_reagir(self):
        """Usuário sem autenticação deve receber 401 ao tentar reagir."""
        self.client.force_authenticate(user=None)
        url = reverse("comentarioperformance-reagir", args=[self.comentario.id])
        response = self.client.post(url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_eu_curto_reflete_estado_correto(self):
        """Campo eu_curto deve ser True se o usuário curtiu, False se não."""
        self._auth(self.user_outro)
        ReacaoComentario.objects.create(comentario=self.comentario, musico=self.outro)
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.get(url)
        self.assertTrue(response.data["eu_curto"])

    def test_eu_curto_false_sem_reacao(self):
        """Campo eu_curto deve ser False se o usuário não curtiu."""
        self._auth(self.user_outro)
        url = reverse("comentarioperformance-detail", args=[self.comentario.id])
        response = self.client.get(url)
        self.assertFalse(response.data["eu_curto"])
