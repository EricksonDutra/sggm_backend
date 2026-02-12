from django.db import models


from django.utils.timezone import now


class Musico(models.Model):

    STATUS_CHOICES = [
        ("ATIVO", "Ativo"),
        ("INATIVO", "Inativo"),
        ("AFASTADO", "Afastado Temporariamente"),
    ]

    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)

    instrumento_principal = models.ForeignKey(
        "Instrumento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="musicos"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ATIVO"
    )

    data_inicio_inatividade = models.DateField(blank=True, null=True)
    data_fim_inatividade = models.DateField(blank=True, null=True)
    motivo_inatividade = models.CharField(max_length=255, blank=True)

    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'musicos'
        verbose_name = 'Músico'
        verbose_name_plural = 'Músicos'
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def esta_disponivel(self):
        """
        Verifica se o músico está disponível hoje.
        """
        hoje = now().date()

        if self.status == "ATIVO":
            return True

        if self.status == "AFASTADO":
            if self.data_inicio_inatividade and self.data_fim_inatividade:
                return not (self.data_inicio_inatividade <= hoje <= self.data_fim_inatividade)

        return False



class Musica(models.Model):
    titulo = models.CharField(max_length=100)
    artista = models.CharField(max_length=100)
    tom = models.CharField(max_length=10, blank=True, null=True)
    link_cifra = models.URLField(max_length=200, blank=True, null=True)
    link_youtube = models.URLField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'musicas'
        verbose_name = 'Música'
        verbose_name_plural = 'Músicas'

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

    repertorio = models.ManyToManyField(
        Musica,
        related_name='eventos',
        blank=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'eventos'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ["-data_evento"]

    def __str__(self):
        return f"{self.nome} - {self.data_evento.strftime('%d/%m/%Y')}"



class Escala(models.Model):

    musico = models.ForeignKey(
        Musico,
        on_delete=models.PROTECT, 
        related_name="escalas"
    )

    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name="escalas"
    )

    instrumento_no_evento = models.ForeignKey(
        "Instrumento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    observacao = models.CharField(max_length=255, blank=True)

    confirmado = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'escalas'
        unique_together = ('musico', 'evento')
        verbose_name = 'Escala'
        verbose_name_plural = 'Escalas'
        ordering = ["evento__data_evento"]

    def __str__(self):
        return f"{self.musico.nome} em {self.evento.nome}"



class Instrumento(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'instrumentos'
        verbose_name = 'Instrumento'
        verbose_name_plural = 'Instrumentos'

    def __str__(self):
        return self.nome
