# Generated by Django 5.0 on 2025-06-04 19:14

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0199_remove_fichatecnicahomologacioncarroceria_excel_documento_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='VehiculoLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modelo_afectado', models.CharField(max_length=100)),
                ('instancia_pk', models.CharField(max_length=100)),
                ('accion', models.CharField(max_length=20)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('cambios', models.JSONField(blank=True, null=True)),
                ('vehiculo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='myapp.vehiculos')),
            ],
        ),
    ]
