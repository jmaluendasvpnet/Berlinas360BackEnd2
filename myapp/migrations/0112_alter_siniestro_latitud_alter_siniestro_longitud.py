# Generated by Django 5.0 on 2024-11-26 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0111_alter_siniestro_entes_atendieron'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siniestro',
            name='latitud',
            field=models.DecimalField(decimal_places=19, max_digits=22),
        ),
        migrations.AlterField(
            model_name='siniestro',
            name='longitud',
            field=models.DecimalField(decimal_places=19, max_digits=22),
        ),
    ]
