from django.db import models


class Musicos(models.Model):
    musicoId = models.AutoField(primary_key=True, db_column='MusicoID')
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    endereco = models.CharField(max_length=255)

    class Meta:
        db_table = 'Musicos'  # Nome exato da tabela no SQL Server


class Eventos(models.Model):
    eventoId = models.AutoField(primary_key=True, db_column='EventoID')
    nome = models.CharField(max_length=100)
    dataEvento = models.DateTimeField()
    local = models.CharField(max_length=100)
    descricao = models.CharField(max_length=500)

    class Meta:
        db_table = 'Eventos'


class Escalas(models.Model):
    escalaId = models.AutoField(primary_key=True, db_column='EscalaID')
    musico = models.ForeignKey(
        Musicos, on_delete=models.CASCADE, related_name="escalas", db_column='MusicoID')
    evento = models.ForeignKey(
        Eventos, on_delete=models.CASCADE, related_name="escalas", db_column='EventoID')
    dataEscala = models.DateTimeField()

    class Meta:
        db_table = 'Escalas'


class Musicas(models.Model):
    musicaId = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200)
    compositor = models.CharField(max_length=200)
    duracao = models.TimeField()

    class Meta:
        db_table = 'Musicas'


class EscalaRepertorio(models.Model):
    escala_repertorioId = models.AutoField(primary_key=True, db_column='EscalaRepertorioId')
    escalaId = models.ForeignKey(
        Escalas, on_delete=models.CASCADE, related_name="escalaRepertorio", db_column='EscalaID')
    musicaId = models.ForeignKey(
        Musicas, on_delete=models.CASCADE, related_name="escalaRepertorio", db_column='MusicaID')

    class Meta:
        db_table = 'EscalaRepertorio'

