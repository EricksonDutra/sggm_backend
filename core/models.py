from django.db import models


class Musico(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)

    instrumento_principal = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'musicos'
        verbose_name = 'Músico'
        verbose_name_plural = 'Músicos'

    def __str__(self):
        return self.nome


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
    nome = models.CharField(max_length=100)
    data_evento = models.DateTimeField()
    local = models.CharField(max_length=100)
    descricao = models.CharField(max_length=500, blank=True)

    repertorio = models.ManyToManyField(
        Musica, related_name='eventos', blank=True)

    class Meta:
        db_table = 'eventos'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return f"{self.nome} - {self.data_evento.strftime('%d/%m/%Y')}"


class Escala(models.Model):
    musico = models.ForeignKey(
        Musico, on_delete=models.CASCADE, related_name="escalas")
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="escalas")

    instrumento_no_evento = models.CharField(max_length=50, blank=True)

    observacao = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'escalas'
        unique_together = ('musico', 'evento')
        verbose_name = 'Escala'
        verbose_name = 'Escalas'

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
