# Generated by Django 5.0 on 2025-03-28 14:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0174_vehiculos_caracteristicasmecanicas_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehiculos',
            name='tipoLinea',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.tipolinea'),
        ),
    ]
