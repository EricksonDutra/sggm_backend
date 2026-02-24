from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import ComentarioPerformance, Musico


@receiver(post_save, sender=User)
def criar_perfil_musico(sender, instance, created, **kwargs):
    """Cria automaticamente um perfil de músico quando um User é criado"""
    if created and not hasattr(instance, "musico"):
        # Verifica se o usuário está no grupo Músicos
        if instance.groups.filter(name="Músicos").exists():
            Musico.objects.create(
                user=instance,
                nome=instance.get_full_name() or instance.username,
                status="ATIVO",
            )


@receiver(post_save, sender=ComentarioPerformance)
def notificar_escalados_feedback(sender, instance, created, **kwargs):
    """Notifica escalados do evento quando um novo feedback é publicado."""
    if not created:
        return

    from core.services import NotificationService

    escalados = instance.evento.escalas.select_related("musico").all()
    tokens_musicos = [
        e.musico for e in escalados if e.musico.fcm_token and e.musico != instance.autor
    ]

    for musico in tokens_musicos:
        NotificationService.enviar_notificacao_feedback(
            musico=musico,
            comentario=instance,
        )
