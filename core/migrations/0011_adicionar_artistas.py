import django.db.models.deletion
from django.db import migrations, models


def criar_artistas_existentes(apps, schema_editor):
    """
    Migra artistas existentes do campo CharField para o novo modelo
    """
    Musica = apps.get_model("core", "Musica")
    Artista = apps.get_model("core", "Artista")

    # Obter artistas únicos
    artistas_unicos = Musica.objects.values_list("artista", flat=True).distinct()

    # Criar registros de artistas
    for nome_artista in artistas_unicos:
        if nome_artista:  # Ignorar valores vazios
            Artista.objects.get_or_create(nome=nome_artista.strip())


def migrar_artistas_para_fk(apps, schema_editor):
    """
    Popula o campo artista_fk com base no campo artista (CharField)
    """
    Musica = apps.get_model("core", "Musica")
    Artista = apps.get_model("core", "Artista")

    for musica in Musica.objects.all():
        if musica.artista:
            # Buscar o artista correspondente
            artista = Artista.objects.filter(nome=musica.artista.strip()).first()
            if artista:
                musica.artista_fk = artista
                musica.save(update_fields=["artista_fk"])


def reverter_migrar_artistas(apps, schema_editor):
    """
    Função reversa: copia o nome do artista de volta para o campo CharField
    """
    Musica = apps.get_model("core", "Musica")

    for musica in Musica.objects.all():
        if musica.artista_fk:
            musica.artista = musica.artista_fk.nome
            musica.save(update_fields=["artista"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_musico_precisa_mudar_senha"),  # Ajustar para a última migration
    ]

    operations = [
        # 1. Criar modelo Artista
        migrations.CreateModel(
            name="Artista",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nome",
                    models.CharField(
                        max_length=150,
                        unique=True,
                        verbose_name="Nome do Artista/Banda",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "artistas",
                "verbose_name": "Artista",
                "verbose_name_plural": "Artistas",
                "ordering": ["nome"],
            },
        ),
        # 2. Criar artistas a partir dos dados existentes
        migrations.RunPython(
            criar_artistas_existentes, reverse_code=migrations.RunPython.noop
        ),
        # 3. Adicionar novo campo artista_fk temporário
        migrations.AddField(
            model_name="musica",
            name="artista_fk",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="musicas_temp",
                to="core.artista",
                verbose_name="Artista/Banda",
            ),
        ),
        # 4. Popular o novo campo com base no antigo
        migrations.RunPython(
            migrar_artistas_para_fk, reverse_code=reverter_migrar_artistas
        ),
        # 5. Remover campo antigo (CharField)
        migrations.RemoveField(
            model_name="musica",
            name="artista",
        ),
        # 6. Renomear campo novo para 'artista'
        migrations.RenameField(
            model_name="musica",
            old_name="artista_fk",
            new_name="artista",
        ),
        # 7. Tornar o campo obrigatório (remover null=True)
        migrations.AlterField(
            model_name="musica",
            name="artista",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="musicas",
                to="core.artista",
                verbose_name="Artista/Banda",
            ),
        ),
        # 8. Adicionar constraint de unique_together
        migrations.AlterUniqueTogether(
            name="musica",
            unique_together={("titulo", "artista")},
        ),
    ]
