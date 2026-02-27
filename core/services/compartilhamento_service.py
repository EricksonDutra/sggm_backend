from core.models import Evento


class CompartilhamentoService:
    """
    Serviço responsável por gerar o texto de compartilhamento
    da escala de um evento (ex.: envio via WhatsApp).
    """

    @staticmethod
    def gerar_texto_escala(evento_id: int) -> str:
        """
        Gera o texto formatado da escala de um evento para compartilhamento.

        Formato:
            🎵 *NOME DO EVENTO*
            📅 Data: DD/MM/AAAA às HH:MM
            📍 Local: ...
            🕐 Ensaio: DD/MM/AAAA às HH:MM  (somente se houver)

            👥 *Equipe escalada:*
            • Nome — Instrumento

            🎶 *Repertório:*
            • Título - Artista
              🔗 Cifra: <link>        (somente se houver)
              ▶️ YouTube: <link>      (somente se houver)
        """
        try:
            evento = Evento.objects.prefetch_related(
                "escalas__musico",
                "escalas__instrumento_no_evento",
                "repertorio__artista",
            ).get(id=evento_id)
        except Evento.DoesNotExist:
            raise ValueError(f"Evento com id={evento_id} não encontrado.")

        linhas = []

        # Cabeçalho
        linhas.append(f"🎵 *{evento.nome.upper()}*")
        linhas.append(f"📅 Data: {evento.data_evento.strftime('%d/%m/%Y às %H:%M')}")
        linhas.append(f"📍 Local: {evento.local}")

        # Ensaio (opcional)
        if evento.data_hora_ensaio:
            linhas.append(
                f"🕐 Ensaio: {evento.data_hora_ensaio.strftime('%d/%m/%Y às %H:%M')}"
            )

        # Equipe
        escalas = evento.escalas.all()
        if escalas.exists():
            linhas.append("")
            linhas.append("👥 *Equipe escalada:*")
            for escala in escalas:
                instrumento = (
                    escala.instrumento_no_evento.nome
                    if escala.instrumento_no_evento
                    else "Sem instrumento"
                )
                linhas.append(f"• {escala.musico.nome} — {instrumento}")

        # Repertório
        musicas = evento.repertorio.all()
        if musicas.exists():
            linhas.append("")
            linhas.append("🎶 *Repertório:*")
            for musica in musicas:
                artista_nome = str(musica.artista) if musica.artista else None
                if artista_nome:
                    linhas.append(f"• {musica.titulo} - {artista_nome}")
                else:
                    linhas.append(f"• {musica.titulo}")

                if musica.link_cifra:
                    linhas.append(f"  🔗 Cifra: {musica.link_cifra}")
                if musica.link_youtube:
                    linhas.append(f"  ▶️ YouTube: {musica.link_youtube}")

        return "\n".join(linhas)
