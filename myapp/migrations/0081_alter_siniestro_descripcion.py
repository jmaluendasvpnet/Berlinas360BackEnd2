# Generated by Django 5.0 on 2024-10-03 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0080_siniestro_siniestromedia'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siniestro',
            name='descripcion',
            field=models.TextField(null=True),
        ),
    ]
