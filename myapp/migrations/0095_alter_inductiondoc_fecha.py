# Generated by Django 5.0 on 2024-10-16 23:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0094_alter_inductiondoc_fecha_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inductiondoc',
            name='fecha',
            field=models.DateField(blank=True, null=True),
        ),
    ]
