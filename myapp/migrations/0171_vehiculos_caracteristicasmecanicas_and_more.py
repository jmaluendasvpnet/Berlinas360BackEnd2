# Generated by Django 5.0 on 2025-03-28 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0170_remove_eventolegal_pdf_soporte_eventolegalfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehiculos',
            name='caracteristicasMecanicas',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vehiculos',
            name='declaracionImportacion',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vehiculos',
            name='facturaCompra',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
