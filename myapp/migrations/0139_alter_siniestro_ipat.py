# Generated by Django 4.2.17 on 2025-02-05 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0138_siniestro_ipat"),
    ]

    operations = [
        migrations.AlterField(
            model_name="siniestro",
            name="ipat",
            field=models.BooleanField(default=False),
        ),
    ]
