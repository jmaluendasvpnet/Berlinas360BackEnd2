# Generated by Django 5.0 on 2025-03-02 14:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0155_remove_colaboradores_vehiculo'),
    ]

    operations = [
        migrations.AddField(
            model_name='colaboradores',
            name='vehiculo',
            field=models.ForeignKey(blank=True, db_column='vehiculo', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='myapp.vehiculos'),
        ),
    ]
