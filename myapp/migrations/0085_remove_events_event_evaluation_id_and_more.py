# Generated by Django 5.0 on 2024-10-11 13:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0084_colaboradores_exp_documento'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='events',
            name='event_evaluation_id',
        ),
        migrations.RemoveField(
            model_name='events',
            name='event_required_roles',
        ),
        migrations.RemoveField(
            model_name='events',
            name='event_training_category',
        ),
        migrations.RemoveField(
            model_name='trainings',
            name='training_category',
        ),
        migrations.RemoveField(
            model_name='trainings',
            name='training_evaluation_id',
        ),
        migrations.RemoveField(
            model_name='trainings',
            name='training_required_for',
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id_event', models.AutoField(primary_key=True, serialize=False)),
                ('event_name', models.CharField(max_length=255)),
                ('event_record_number', models.CharField(blank=True, max_length=255, null=True)),
                ('event_date', models.DateField(blank=True, null=True)),
                ('event_start_date', models.DateTimeField(blank=True, null=True)),
                ('event_end_date', models.DateTimeField(blank=True, null=True)),
                ('event_city', models.CharField(blank=True, max_length=255, null=True)),
                ('event_place', models.CharField(blank=True, max_length=255, null=True)),
                ('event_aim', models.TextField(blank=True, null=True)),
                ('event_issue', models.TextField(blank=True, null=True)),
                ('event_agenda', models.TextField(blank=True, null=True)),
                ('event_development', models.TextField(blank=True, null=True)),
                ('event_type', models.CharField(choices=[('reunion', 'Reunión'), ('capacitacion', 'Capacitación')], default='reunion', max_length=20)),
                ('event_evaluation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.evaluation')),
                ('event_required_roles', models.ManyToManyField(related_name='events_required_evaluation', to='myapp.roles')),
                ('event_responsible', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events_responsible', to='myapp.colaboradores')),
                ('event_training_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to='myapp.trainingscategories')),
            ],
        ),
        migrations.CreateModel(
            name='EventAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_name', models.CharField(max_length=255)),
                ('action_deadline', models.DateField(blank=True, null=True)),
                ('action_responsible', models.CharField(max_length=255)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='myapp.event')),
            ],
        ),
        migrations.CreateModel(
            name='EventEvidence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evidence_file', models.FileField(blank=True, null=True, upload_to='event_evidences/')),
                ('description', models.TextField(blank=True, null=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidences', to='myapp.event')),
            ],
        ),
        migrations.CreateModel(
            name='EventGuest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guest_name', models.CharField(max_length=255)),
                ('guest_company', models.CharField(blank=True, max_length=255, null=True)),
                ('guest_position', models.CharField(blank=True, max_length=255, null=True)),
                ('guest_signature', models.TextField(blank=True, null=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guests', to='myapp.event')),
            ],
        ),
        migrations.CreateModel(
            name='EventParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.CharField(blank=True, max_length=255, null=True)),
                ('fecha', models.DateField(blank=True, null=True)),
                ('colaborador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.colaboradores')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='myapp.event')),
            ],
        ),
        migrations.DeleteModel(
            name='ColaboradoresTrainings',
        ),
        migrations.DeleteModel(
            name='Events',
        ),
        migrations.DeleteModel(
            name='Trainings',
        ),
    ]
