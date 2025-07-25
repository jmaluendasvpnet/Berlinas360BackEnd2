# Generated by Django 5.0 on 2025-04-04 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0177_rename_manager_signature_empresas_email_informacion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventodocumento',
            name='status',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('finalizado', 'Finalizado')], default='pendiente', max_length=50),
        ),
        migrations.AlterField(
            model_name='eventodocumento',
            name='tipo_documento',
            field=models.CharField(choices=[('hurtoOferta', 'Hurto con Oferta'), ('hurtoSinOfertaGeneral', 'Hurto sin Oferta (General)'), ('hurtoSinOferta', 'Hurto sin Oferta'), ('fallaConductor', 'Falla Conductor'), ('peConResponsabilidad', 'PE con Responsabilidad (Sí)'), ('peConResponsabilidadEvidencia', 'PE con Responsabilidad (Sí) c/ Evidencia'), ('paso2', 'Hurto de Equipaje - Paso 2'), ('contrapropuesta', 'Contrapropuesta')], max_length=50),
        ),
    ]
