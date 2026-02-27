import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from core.models import Artista, Escala, Evento, Instrumento, Musica, Musico
from core.services.compartilhamento_service import CompartilhamentoService

DATA_EVENTO = datetime.datetime(2026, 3, 15, 19, 0)
DATA_ENSAIO = datetime.datetime(2026, 3, 15, 17, 0)


class CompartilhamentoServiceTest(TestCase):

    def setUp(self):
        self.artista = Artista.objects.create(nome="Hillsong")

        self.musica_com_links = Musica.objects.create(
            titulo="Oceans",
            artista=self.artista,
            link_cifra="https://www.cifraclub.com.br/hillsong/oceans/",
            link_youtube="https://youtu.be/dy9nwe9_xzw",
        )
        self.musica_sem_links = Musica.objects.create(
            titulo="Alvo Mais que a Neve",
            artista=self.artista,
        )
        self.musica_so_cifra = Musica.objects.create(
            titulo="Quão Grande é o Meu Deus",
            artista=self.artista,
            link_cifra="https://www.cifraclub.com.br/chris-tomlin/how-great-is-our-god/",
        )

        self.evento = Evento.objects.create(
            nome="Culto Jovens",
            tipo="CULTO",
            data_evento=DATA_EVENTO,
            local="Templo Central",
        )

        self.instrumento = Instrumento.objects.create(nome="Violão")

        self.user = User.objects.create_user(
            username="joao", email="joao@test.com", password="pass"
        )
        self.musico = Musico.objects.create(
            user=self.user, nome="João Silva", status="ATIVO"
        )

    # ------------------------------------------------------------------
    # Cabeçalho
    # ------------------------------------------------------------------

    def test_cabecalho_contem_nome_evento(self):
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertIn("CULTO JOVENS", texto)

    def test_cabecalho_contem_data_evento(self):
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertIn("15/03/2026", texto)
        self.assertIn("19:00", texto)

    def test_cabecalho_contem_local(self):
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertIn("Templo Central", texto)

    # ------------------------------------------------------------------
    # Ensaio
    # ------------------------------------------------------------------

    def test_sem_ensaio_nao_exibe_linha_ensaio(self):
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertNotIn("Ensaio", texto)

    def test_com_ensaio_exibe_data_hora_ensaio(self):
        self.evento.data_hora_ensaio = DATA_ENSAIO
        self.evento.save()
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertIn("Ensaio", texto)
        self.assertIn("17:00", texto)

    # ------------------------------------------------------------------
    # Equipe escalada
    # ------------------------------------------------------------------

    def test_sem_escalados_nao_exibe_secao_equipe(self):
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertNotIn("Equipe escalada", texto)

    def test_musico_escalado_aparece_com_instrumento(self):
        Escala.objects.create(
            musico=self.musico,
            evento=self.evento,
            instrumento_no_evento=self.instrumento,
        )
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertIn("João Silva", texto)
        self.assertIn("Violão", texto)

    def test_musico_escalado_sem_instrumento(self):
        Escala.objects.create(
            musico=self.musico,
            evento=self.evento,
            instrumento_no_evento=None,
        )
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertIn("João Silva", texto)
        self.assertIn("Sem instrumento", texto)

    # ------------------------------------------------------------------
    # Repertório
    # ------------------------------------------------------------------

    def test_sem_repertorio_nao_exibe_secao_repertorio(self):
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertNotIn("Repertório", texto)

    def test_musica_com_ambos_links_exibe_cifra_e_youtube(self):
        self.evento.repertorio.add(self.musica_com_links)
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertIn("Oceans", texto)
        self.assertIn("https://www.cifraclub.com.br/hillsong/oceans/", texto)
        self.assertIn("https://youtu.be/dy9nwe9_xzw", texto)

    def test_musica_sem_links_nao_exibe_placeholder(self):
        self.evento.repertorio.add(self.musica_sem_links)
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertIn("Alvo Mais que a Neve", texto)
        self.assertNotIn("🔗", texto)
        self.assertNotIn("▶️", texto)
        self.assertNotIn("None", texto)
        self.assertNotIn("?", texto)

    def test_musica_so_com_cifra_exibe_apenas_cifra(self):
        self.evento.repertorio.add(self.musica_so_cifra)
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertIn("🔗", texto)
        self.assertNotIn("▶️", texto)

    def test_musica_exibe_artista(self):
        self.evento.repertorio.add(self.musica_com_links)
        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)
        self.assertIn("Hillsong", texto)

    # ------------------------------------------------------------------
    # Texto completo / integração
    # ------------------------------------------------------------------

    def test_texto_completo_com_tudo(self):
        """Cenário completo: ensaio + equipe + repertório com e sem links."""
        self.evento.data_hora_ensaio = DATA_ENSAIO
        self.evento.save()

        Escala.objects.create(
            musico=self.musico,
            evento=self.evento,
            instrumento_no_evento=self.instrumento,
        )

        self.evento.repertorio.add(self.musica_com_links)
        self.evento.repertorio.add(self.musica_sem_links)

        texto = CompartilhamentoService.gerar_texto_escala(self.evento.id)

        self.assertIn("CULTO JOVENS", texto)
        self.assertIn("15/03/2026", texto)
        self.assertIn("Ensaio", texto)
        self.assertIn("João Silva", texto)
        self.assertIn("Violão", texto)
        self.assertIn("Oceans", texto)
        self.assertIn("https://www.cifraclub.com.br/hillsong/oceans/", texto)
        self.assertIn("Alvo Mais que a Neve", texto)
        self.assertNotIn("None", texto)

    # ------------------------------------------------------------------
    # Erro
    # ------------------------------------------------------------------

    def test_evento_inexistente_levanta_value_error(self):
        with self.assertRaises(ValueError):
            CompartilhamentoService.gerar_texto_escala(99999)
