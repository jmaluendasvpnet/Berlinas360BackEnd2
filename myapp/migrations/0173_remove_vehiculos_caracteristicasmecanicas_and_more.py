# Generated by Django 5.0 on 2025-03-28 14:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0172_alter_vehiculos_caracteristicasmecanicas_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vehiculos',
            name='caracteristicasMecanicas',
        ),
        migrations.RemoveField(
            model_name='vehiculos',
            name='declaracionImportacion',
        ),
        migrations.RemoveField(
            model_name='vehiculos',
            name='facturaCompra',
        ),
    ]
