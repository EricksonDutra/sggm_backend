from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import Escala, Evento, Instrumento, Musico


class GerenciadorEscala:
    """
    Camada de serviço responsável pelas regras de negócio
    relacionadas à escala de músicos.
    """

    @staticmethod
    @transaction.atomic
    def adicionar_musico_ao_evento(
        evento_id: int, musico_id: int, instrumento_nome: str | None = None
    ) -> Escala:
        """
        Adiciona um músico a um evento respeitando regras de negócio.

        Regras:
        - Não pode duplicar músico no mesmo evento
        - Não pode escalar músico inativo
        - Não pode escalar músico afastado no período
        - Instrumento é opcional
        """

        evento = Evento.objects.filter(id=evento_id).first()
        if not evento:
            raise ValidationError("Evento não encontrado.")

        musico = Musico.objects.filter(id=musico_id).first()
        if not musico:
            raise ValidationError("Músico não encontrado.")

        # duplicidade
        if Escala.objects.filter(evento=evento, musico=musico).exists():
            raise ValidationError("Este músico já está escalado para este evento.")

        # status músico
        if musico.status == "INATIVO":
            raise ValidationError("Não é possível escalar músico inativo.")

        if musico.esta_afastado():
            raise ValidationError("Músico está afastado no período.")

        # instrumento opcional
        instrumento_obj = None
        if instrumento_nome:
            instrumento_obj, _ = Instrumento.objects.get_or_create(
                nome=instrumento_nome
            )

        escala = Escala.objects.create(
            evento=evento, musico=musico, instrumento_no_evento=instrumento_obj
        )

        return escala
