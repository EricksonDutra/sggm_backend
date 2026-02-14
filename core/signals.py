from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Musico


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
