# Generated by Django 5.0 on 2025-05-18 08:29

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0195_procesodefinicion_remove_siniestro_numero_victimas_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='actuaciondefinicion',
            unique_together={('sub_etapa_definicion', 'nombre'), ('sub_etapa_definicion', 'orden')},
        ),
        migrations.AlterUniqueTogether(
            name='etapadefinicion',
            unique_together={('proceso_definicion', 'nombre'), ('proceso_definicion', 'orden')},
        ),
        migrations.AlterUniqueTogether(
            name='subetapadefinicion',
            unique_together={('etapa_definicion', 'nombre'), ('etapa_definicion', 'orden')},
        ),
        migrations.AlterField(
            model_name='historialactuacion',
            name='actuacion_definicion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_victimas', to='myapp.actuaciondefinicion'),
        ),
        migrations.AlterField(
            model_name='historialactuacion',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='historial_victimas_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='siniestro',
            name='colaborador',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='siniestros_colaborador', to='myapp.colaboradores'),
        ),
        migrations.AlterField(
            model_name='siniestro',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='siniestros_empresa', to='myapp.empresas'),
        ),
        migrations.AlterField(
            model_name='siniestro',
            name='entes_atendieron',
            field=models.ManyToManyField(blank=True, related_name='siniestros_atendidos', to='myapp.enteatencion'),
        ),
        migrations.AlterField(
            model_name='siniestro',
            name='vehiculo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='siniestros_vehiculo', to='myapp.vehiculos'),
        ),
        migrations.AlterField(
            model_name='siniestrolog',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logs_siniestro_user', to='myapp.colaboradores'),
        ),
        migrations.AlterField(
            model_name='victimaproceso',
            name='actuacion_definicion_siguiente',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='victima_actuaciones_siguientes', to='myapp.actuaciondefinicion'),
        ),
        migrations.AlterField(
            model_name='victimaproceso',
            name='etapa_definicion_actual',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='victima_etapas_actuales', to='myapp.etapadefinicion'),
        ),
        migrations.AlterField(
            model_name='victimaproceso',
            name='proceso_definicion_actual',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='victima_procesos_actuales', to='myapp.procesodefinicion'),
        ),
        migrations.AlterField(
            model_name='victimaproceso',
            name='sub_etapa_definicion_actual',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='victima_subetapas_actuales', to='myapp.subetapadefinicion'),
        ),
        migrations.CreateModel(
            name='SiniestroProceso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_general', models.CharField(choices=[('no_iniciado', 'No Iniciado'), ('en_progreso', 'En Progreso'), ('terminado', 'Terminado')], default='no_iniciado', max_length=20)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('actuacion_definicion_siguiente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='siniestros_actuaciones_siguientes', to='myapp.actuaciondefinicion')),
                ('etapa_definicion_actual', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='siniestros_etapas_actuales', to='myapp.etapadefinicion')),
                ('proceso_definicion_actual', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='siniestros_procesos_actuales', to='myapp.procesodefinicion')),
                ('siniestro', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='proceso_detalle_siniestro', to='myapp.siniestro')),
                ('sub_etapa_definicion_actual', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='siniestros_subetapas_actuales', to='myapp.subetapadefinicion')),
            ],
        ),
        migrations.CreateModel(
            name='SiniestroHistorialActuacion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fecha_actuacion', models.DateField()),
                ('fecha_vigencia', models.DateField(blank=True, null=True)),
                ('notas', models.TextField(blank=True, null=True)),
                ('documento', models.FileField(blank=True, null=True, upload_to='documentos_actuaciones_siniestros/')),
                ('documento_nombre_original', models.CharField(blank=True, max_length=255, null=True)),
                ('timestamp_registro', models.DateTimeField(auto_now_add=True)),
                ('status_actuacion', models.CharField(choices=[('completada', 'Completada'), ('omitida_temporalmente', 'Omitida Temporalmente'), ('omitida_permanentemente', 'Omitida Permanentemente'), ('en_espera', 'En Espera'), ('pendiente', 'Pendiente')], max_length=30)),
                ('actuacion_definicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_siniestros', to='myapp.actuaciondefinicion')),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='historial_siniestros_creados', to=settings.AUTH_USER_MODEL)),
                ('resuelve_omision_de', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accion_resolutoria_siniestro', to='myapp.siniestrohistorialactuacion')),
                ('siniestro_proceso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_actuaciones_siniestro', to='myapp.siniestroproceso')),
            ],
        ),
        migrations.AddField(
            model_name='siniestro',
            name='proceso_estado_general',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='siniestro_directo', to='myapp.siniestroproceso'),
        ),
    ]
