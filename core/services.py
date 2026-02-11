from django.core.exceptions import ValidationError

from .models import Escala, Evento, Musico


class GerenciadorEscala:

    @staticmethod
    def adicionar_musico_ao_evento(evento_id: int, musico_id: int, instrumento: str = ""):
        """
        Caso de Uso: Adicionar músico na escala.
        O instrumento padrão é uma string vazia, não None.
        """
        try:
            evento = Evento.objects.get(id=evento_id)
            musico = Musico.objects.get(id=musico_id)

            if Escala.objects.filter(evento=evento, musico=musico).exists():
                raise ValidationError(
                    "Este músico já está escalado para este evento.")

            escala = Escala.objects.create(
                evento=evento,
                musico=musico,
                instrumento_no_evento=instrumento
            )
            return escala

        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f"Erro ao escalar músico: {str(e)}")
