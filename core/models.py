from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.timezone import now


class Musico(models.Model):

    TIPO_USUARIO_CHOICES = [
        ("MUSICO", "Músico"),
        ("LIDER", "Líder"),
        ("ADMIN", "Administrador"),
    ]

    STATUS_CHOICES = [
        ("ATIVO", "Ativo"),
        ("INATIVO", "Inativo"),
        ("AFASTADO", "Afastado Temporariamente"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="musico", null=True, blank=True
    )
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default="MUSICO",
        verbose_name="Tipo de Usuário",
    )

    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)

    instrumento_principal = models.ForeignKey(
        "Instrumento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="musicos",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ATIVO")

    data_inicio_inatividade = models.DateField(blank=True, null=True)
    data_fim_inatividade = models.DateField(blank=True, null=True)
    motivo_inatividade = models.CharField(max_length=255, blank=True)

    data_cadastro = models.DateTimeField(auto_now_add=True)

    fcm_token = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Token FCM"
    )

    role = models.CharField(
        max_length=20,
        choices=[("MUSICO", "Músico"), ("LIDER", "Líder")],
        default="MUSICO",
    )

    precisa_mudar_senha = models.BooleanField(
        default=True,
        help_text="True se o usuário precisa mudar a senha no próximo login",
    )

    def esta_afastado(self):
        hoje = timezone.now().date()

        if self.status != "AFASTADO":
            return False

        if not self.data_inicio_inatividade or not self.data_fim_inatividade:
            return True

        if self.data_inicio_inatividade and self.data_fim_inatividade:
            return self.data_inicio_inatividade <= hoje <= self.data_fim_inatividade

        return False

    def is_lider(self):
        """Verifica se é líder ou admin"""
        return self.tipo_usuario in ["LIDER", "ADMIN"] or self.user.is_superuser

    def is_admin(self):
        """Verifica se é admin"""
        return self.tipo_usuario == "ADMIN" or self.user.is_superuser

    def clean(self):
        if self.user:
            # Verificar se já existe outro músico com o mesmo usuário
            if Musico.objects.exclude(pk=self.pk).filter(user=self.user).exists():
                raise ValidationError(
                    {"user": "Já existe um músico vinculado a este usuário."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self._sincronizar_grupo()

    def _sincronizar_grupo(self):
        """Sincroniza o grupo Django com o tipo de usuário"""
        from django.contrib.auth.models import Group

        # Remover de todos os grupos relacionados
        grupos_sistema = ["Músicos", "Lideres", "Administradores"]
        self.user.groups.filter(name__in=grupos_sistema).delete()

        # Adicionar ao grupo correto
        if self.tipo_usuario == "MUSICO":
            grupo, _ = Group.objects.get_or_create(name="Músicos")
        elif self.tipo_usuario == "LIDER":
            grupo, _ = Group.objects.get_or_create(name="Lideres")
        elif self.tipo_usuario == "ADMIN":
            grupo, _ = Group.objects.get_or_create(name="Administradores")
            self.user.is_staff = True
            self.user.save()

        self.user.groups.add(grupo)

    class Meta:
        db_table = "musicos"
        verbose_name = "Músico"
        verbose_name_plural = "Músicos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def email(self):
        """Retorna o email do usuário vinculado"""
        return self.user.email if self.user else None

    @email.setter
    def email(self, value):
        self._email = value

    def esta_disponivel(self):
        """
        Verifica se o músico está disponível hoje.
        """
        hoje = now().date()

        if self.status == "ATIVO":
            return True

        if self.status == "INATIVO":
            return False

        if self.status == "AFASTADO":
            if not self.data_inicio_inatividade or not self.data_fim_inatividade:
                return False
            if self.data_inicio_inatividade and self.data_fim_inatividade:
                return not (
                    self.data_inicio_inatividade <= hoje <= self.data_fim_inatividade
                )

        return False


class Musica(models.Model):
    titulo = models.CharField(max_length=100)
    artista = models.ForeignKey(
        "Artista",
        on_delete=models.PROTECT,  # Impede deletar artista com músicas
        related_name="musicas",
        verbose_name="Artista/Banda",
    )
    tom = models.CharField(max_length=10, blank=True, null=True)
    link_cifra = models.URLField(max_length=200, blank=True, null=True)
    link_youtube = models.URLField(max_length=200, blank=True, null=True)
    conteudo_cifra = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "musicas"
        verbose_name = "Música"
        verbose_name_plural = "Músicas"
        unique_together = [["titulo", "artista"]]

    def __str__(self):
        return f"{self.titulo} - {self.artista}"


class Evento(models.Model):

    TIPO_EVENTO = [
        ("CULTO", "Culto"),
        ("CONFERENCIA", "Conferência"),
        ("CELULA", "Célula"),
        ("ESPECIAL", "Especial"),
    ]

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_EVENTO, default="CULTO")
    data_evento = models.DateTimeField()
    local = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)

    data_hora_ensaio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data e Hora do Ensaio",
        help_text="Data e hora do ensaio para este evento (opcional)",
    )

    repertorio = models.ManyToManyField(Musica, related_name="eventos", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validações de negócio"""

        from django.core.exceptions import ValidationError

        if self.data_hora_ensaio and self.data_evento:
            if self.data_hora_ensaio > self.data_evento:
                raise ValidationError(
                    "A data/hora do ensaio não pode ser posterior à data do evento."
                )

    class Meta:
        db_table = "eventos"
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-data_evento"]

    def __str__(self):
        return f"{self.nome} - {self.data_evento.strftime('%d/%m/%Y')}"


class Escala(models.Model):

    musico = models.ForeignKey(Musico, on_delete=models.PROTECT, related_name="escalas")
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="escalas")

    instrumento_no_evento = models.ForeignKey(
        "Instrumento", on_delete=models.SET_NULL, null=True, blank=True
    )

    observacao = models.CharField(max_length=255, blank=True)

    confirmado = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validações de negócio"""
        from django.core.exceptions import ValidationError

        # ✅ Validar se músico está ativo
        if self.musico.status != "ATIVO":
            raise ValidationError(
                "Músico deve estar com status ATIVO para ser escalado"
            )

        # ✅ Validar afastamento
        if hasattr(self.musico, "afastamento_set"):
            afastamentos = self.musico.afastamento_set.filter(
                data_inicio__lte=self.evento.data_evento.date(),
                data_fim__gte=self.evento.data_evento.date(),
            )
            if afastamentos.exists():
                raise ValidationError("Músico está afastado neste período")

    def save(self, *args, **kwargs):
        # ✅ Chamar clean() antes de salvar
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "escalas"
        unique_together = ["musico", "evento"]

        verbose_name = "Escala"
        verbose_name_plural = "Escalas"
        ordering = ["evento__data_evento"]

    def __str__(self):
        return f"{self.musico.nome} em {self.evento.nome}"


class Instrumento(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "instrumentos"
        verbose_name = "Instrumento"
        verbose_name_plural = "Instrumentos"

    def __str__(self):
        return self.nome


class Artista(models.Model):
    """
    Modelo para cadastro de artistas/bandas musicais.
    Evita inconsistências ao cadastrar músicas.
    """

    nome = models.CharField(
        max_length=150, unique=True, verbose_name="Nome do Artista/Banda"
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "artistas"
        verbose_name = "Artista"
        verbose_name_plural = "Artistas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def clean(self):
        """Remove espaços extras e padroniza o nome"""
        if self.nome:
            self.nome = self.nome.strip()


class ComentarioPerformance(models.Model):
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name="comentarios_performance",
    )
    musica = models.ForeignKey(
        Musica,
        on_delete=models.CASCADE,
        related_name="comentarios_performance",
    )
    autor = models.ForeignKey(
        "Musico",
        on_delete=models.SET_NULL,
        null=True,
        related_name="comentarios_feitos",
    )
    texto = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    editado_em = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        if self.evento_id and self.evento.data_evento > timezone.now():
            raise ValidationError(
                "Comentários só podem ser publicados após o início do evento."
            )
        if self.musica_id and self.evento_id:
            if not self.evento.repertorio.filter(pk=self.musica_id).exists():
                raise ValidationError(
                    "Esta música não pertence ao repertório deste evento."
                )

    class Meta:
        db_table = "comentarios_performance"
        verbose_name = "Comentário de Performance"
        verbose_name_plural = "Comentários de Performance"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.autor} sobre {self.musica} em {self.evento}"


class ReacaoComentario(models.Model):
    comentario = models.ForeignKey(
        ComentarioPerformance,
        on_delete=models.CASCADE,
        related_name="reacoes",
    )
    musico = models.ForeignKey(
        Musico,
        on_delete=models.CASCADE,
        related_name="reacoes_dadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reacoes_comentario"
        verbose_name = "Reação"
        verbose_name_plural = "Reações"
        unique_together = ["comentario", "musico"]

    def __str__(self):
        return f"{self.musico.nome} 👍 em comentário {self.comentario.id}"
