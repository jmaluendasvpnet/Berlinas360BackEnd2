# Generated by Django 5.0 on 2024-09-02 00:02

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0031_remove_evaluation_eva_event_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='events',
            name='event_participants',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(unique=True), blank=True, default=list, null=True, size=None),
        ),
    ]
