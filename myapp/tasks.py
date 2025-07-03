# myapp/tasks.py

from .models import Notification, Agenda, Soat, RevisionTecnomecanica
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from celery import shared_task
from twilio.rest import Client
from datetime import timedelta
import logging

logger = logging.getLogger('myapp.tasks')
import os
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_CONTENT_SID = os.getenv('TWILIO_CONTENT_SID')
TWILIO_TO_DEFAULT = 'whatsapp:+573203339694'
TWILIO_FROM = 'whatsapp:+14155238886'

TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'
TWILIO_SMS_FROM = '+15802894681'
TWILIO_WHATSAPP_TO_DEFAULT = 'whatsapp:+573203339694'
TWILIO_SMS_TO_DEFAULT = '+573203339694'

@shared_task(bind=True, name='myapp.send_event_start_notification_agenda')
def send_event_start_notification_agenda(self, agenda_id):
    try:
        agenda = Agenda.objects.get(id=agenda_id)
        channel_layer = get_channel_layer()
        colaborador = agenda.agenda_colaborador_id
        
        group_name = f"user_{colaborador.num_documento}"
        message_text = f"El evento '{agenda.agenda_title}' va a iniciar en 2 minutos."
        
        notification = Notification.objects.create(
            user=colaborador,
            type='avisos',
            content=message_text,
            time=timezone.now(),
            status='no iniciado'
        )
        logger.info(f"Notificación creada: {notification.id}")
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "content": {
                    "id": notification.id,
                    "type": notification.type,
                    "content": notification.content,
                    "time": notification.time.isoformat(),
                    "status": notification.status,
                },
            }
        )
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Enviar mensaje por WhatsApp
        to_phone_whatsapp = getattr(colaborador, 'phone', None)
        if to_phone_whatsapp:
            if not to_phone_whatsapp.startswith('whatsapp:'):
                to_phone_whatsapp = f"whatsapp:{to_phone_whatsapp}"
        else:
            to_phone_whatsapp = TWILIO_WHATSAPP_TO_DEFAULT

        whatsapp_message = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            body=message_text,
            to=to_phone_whatsapp
        )
        logger.info(f"Mensaje de WhatsApp enviado: {whatsapp_message.sid}")
        
        # Enviar mensaje por SMS
        to_phone_sms = getattr(colaborador, 'phone', None) or TWILIO_SMS_TO_DEFAULT
        sms_message = client.messages.create(
            from_=TWILIO_SMS_FROM,
            body=message_text,
            to=to_phone_sms
        )
        logger.info(f"Mensaje SMS enviado: {sms_message.sid}")
        
    except Agenda.DoesNotExist:
        logger.error(f"El ID de agenda {agenda_id} no existe.")
    except Exception as e:
        logger.error(f"Error en send_event_start_notification_agenda: {e}")

@shared_task
def check_expiring_documents():
    today = timezone.now().date()
    logger.info("Iniciando verificación de documentos expirantes.")

    soats = Soat.objects.filter(estado=True)
    for soat in soats:
        days_until_expiration = (soat.vigencia_hasta - today).days
        logger.debug(f"SOAT placa {soat.placa} expira en {days_until_expiration} días.")

        if should_notify(days_until_expiration):
            has_new_soat = Soat.objects.filter(
                vehiculo=soat.vehiculo,
                vigencia_desde=soat.vigencia_hasta + timedelta(days=1)
            ).exists()

            if has_new_soat:
                logger.info(f"Vehículo {soat.vehiculo.placa} ya tiene un nuevo SOAT programado. No se notificará.")
                continue

            create_notification(soat.vehiculo.empresa, soat.vehiculo, 'soat', soat.vigencia_hasta)

    revisiones = RevisionTecnomecanica.objects.filter(estado=True)
    for revision in revisiones:
        days_until_expiration = (revision.fecha_vencimiento - today).days
        logger.debug(f"Revisión Tecnomecánica placa {revision.placa} expira en {days_until_expiration} días.")

        if should_notify(days_until_expiration):
            has_new_revision = RevisionTecnomecanica.objects.filter(
                vehiculo=revision.vehiculo,
                fecha_expedicion=revision.fecha_vencimiento + timedelta(days=1)
            ).exists()

            if has_new_revision:
                logger.info(f"Vehículo {revision.vehiculo.placa} ya tiene una nueva Revisión Tecnomecánica programada. No se notificará.")
                continue

            create_notification(revision.vehiculo.empresa, revision.vehiculo, 'revision_tecnomecanica', revision.fecha_vencimiento)

    logger.info("Finalizada verificación de documentos expirantes.")


def should_notify(days_until_expiration):
    return days_until_expiration in [14, 15, 30] or (1 <= days_until_expiration <= 7)


def create_notification(empresa, vehiculo, doc_type, expiration_date):
    if doc_type == 'soat':
        content = f"El SOAT del vehículo con placa {vehiculo.placa} está próximo a expirar el {expiration_date}."
    elif doc_type == 'revision_tecnomecanica':
        content = f"La Revisión Tecnomecánica del vehículo con placa {vehiculo.placa} está próxima a expirar el {expiration_date}."
    else:
        content = "Un documento de su vehículo está próximo a expirar."

    colaboradores_con_login = empresa.colaboradores_set.filter(login__isnull=False)

    for colaborador in colaboradores_con_login:
        notification = Notification.objects.create(
            user=colaborador,
            type='avisos',
            content=content,
            time=timezone.now(),
            status='no iniciado'
        )
        logger.info(f"Notificación creada para usuario {colaborador.num_documento}: {content}")

        send_notification_via_ws(colaborador, notification)

def send_notification_via_ws(user, notification):
    channel_layer = get_channel_layer()
    group_name = f"user_{user.num_documento}"

    notification_data = {
        "id": notification.id,
        "type": notification.type,
        "content": notification.content,
        "time": notification.time.isoformat(),
        "status": notification.status,
    }

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "content": notification_data,
        }
    )
    logger.info(f"Notificación enviada al grupo {group_name} para el usuario {user.num_documento}.")

from django.utils import timezone
from django.db.models import Q
import datetime
from dateutil.relativedelta import relativedelta

from celery import shared_task

from .models import (
    Empresas, Vehiculos, Soat, RevisionTecnomecanica, TarjetaOperacion,
    PolizaContractual, PolizaExtracontractual,
    ReporteVencimientosDiario, LicenciaTransito,
)


def actualizar_estados_documentos(model_class, today_date, fecha_fin_field, fecha_inicio_field=None):
    q_expired = Q(**{f"{fecha_fin_field}__isnull": False, f"{fecha_fin_field}__lt": today_date})
    if fecha_inicio_field:
        q_not_yet_active = Q(**{f"{fecha_inicio_field}__isnull": False, f"{fecha_inicio_field}__gt": today_date})
        query_deactivate = Q(estado=True) & (q_expired | q_not_yet_active)
    else:
        query_deactivate = Q(estado=True) & q_expired
    model_class.objects.filter(query_deactivate).update(estado=False)

    q_not_expired = Q(**{f"{fecha_fin_field}__isnull": True}) | Q(**{f"{fecha_fin_field}__gte": today_date})
    if fecha_inicio_field:
        q_started = Q(**{f"{fecha_inicio_field}__isnull": True}) | Q(**{f"{fecha_inicio_field}__lte": today_date})
        query_activate = Q(estado=False) & q_not_expired & q_started
    else:
        query_activate = Q(estado=False) & q_not_expired
    model_class.objects.filter(query_activate).update(estado=True)


@shared_task
def actualizar_estados_y_generar_reportes():
    ReporteVencimientosDiario.objects.all().delete()
    today = timezone.now().date()

    actualizar_estados_documentos(Soat, today, 'vigencia_hasta', 'vigencia_desde')
    actualizar_estados_documentos(RevisionTecnomecanica, today, 'fecha_vencimiento', 'fecha_expedicion')
    actualizar_estados_documentos(TarjetaOperacion, today, 'fechaFinVigencia', 'fechaInicialVigencia')
    actualizar_estados_documentos(PolizaContractual, today, 'fecha_fin_vigencia', 'fecha_inicio_vigencia')
    actualizar_estados_documentos(PolizaExtracontractual, today, 'fecha_fin_vigencia', 'fecha_inicio_vigencia')

    empresas = Empresas.objects.all()
    two_years_ago = today - relativedelta(years=2)

    for empresa in empresas:
        vehiculos_empresa_activos = Vehiculos.objects.filter(empresa=empresa, estado='ACTIVO').prefetch_related(
            'soat_docs', 'revisiones_tecnomecanicas', 'tarjetas_operacion',
            'polizas_contractuales', 'polizas_extracontractuales', 'licencias_transito_docs'
        )

        total_vehiculos_revisados_empresa = vehiculos_empresa_activos.count()
        count_sin_soat = 0
        count_sin_tecno = 0
        count_sin_tarjeta_op = 0
        count_sin_poliza_contractual = 0
        count_sin_poliza_extracontractual = 0

        vehiculos_con_algun_problema_ids = set()
        report_detalle_vehiculos = {}

        for vehiculo in vehiculos_empresa_activos:
            placa_vehiculo = vehiculo.placa
            vencimientos_del_vehiculo = []
            tiene_problema_vehiculo = False

            # SOAT
            if not vehiculo.soat_docs.filter(estado=True).exists():
                count_sin_soat += 1
                tiene_problema_vehiculo = True
                latest_doc = vehiculo.soat_docs.order_by('-vigencia_hasta').first()
                detalle = {'documento': 'SOAT', 'mensaje': 'No tiene SOAT activo.'}
                if latest_doc:
                    detalle['ultimo_numero_poliza'] = latest_doc.numero_poliza
                    detalle['ultima_vigencia_hasta'] = latest_doc.vigencia_hasta.isoformat() if latest_doc.vigencia_hasta else None
                vencimientos_del_vehiculo.append(detalle)

            # Revisión Tecnomecánica (solo si ya pasaron 2 años de matrícula)
            licencia = vehiculo.licencias_transito_docs.order_by('-fecha_matricula').first()
            if licencia and licencia.fecha_matricula and licencia.fecha_matricula <= two_years_ago:
                if not vehiculo.revisiones_tecnomecanicas.filter(estado=True).exists():
                    count_sin_tecno += 1
                    tiene_problema_vehiculo = True
                    latest_doc = vehiculo.revisiones_tecnomecanicas.order_by('-fecha_vencimiento').first()
                    detalle = {'documento': 'Revisión Tecnomecánica', 'mensaje': 'No tiene Revisión Tecnomecánica activa.'}
                    if latest_doc:
                        detalle['ultimo_no_certificado'] = latest_doc.no_certificado
                        detalle['ultima_fecha_vencimiento'] = latest_doc.fecha_vencimiento.isoformat() if latest_doc.fecha_vencimiento else None
                    vencimientos_del_vehiculo.append(detalle)

            # Tarjeta de Operación
            if not vehiculo.tarjetas_operacion.filter(estado=True).exists():
                count_sin_tarjeta_op += 1
                tiene_problema_vehiculo = True
                latest_doc = vehiculo.tarjetas_operacion.order_by('-fechaFinVigencia').first()
                detalle = {'documento': 'Tarjeta de Operación', 'mensaje': 'No tiene Tarjeta de Operación activa.'}
                if latest_doc:
                    detalle['ultimo_numero'] = latest_doc.numero
                    detalle['ultima_fecha_fin_vigencia'] = latest_doc.fechaFinVigencia.isoformat() if latest_doc.fechaFinVigencia else None
                vencimientos_del_vehiculo.append(detalle)

            # Póliza Contractual
            if not vehiculo.polizas_contractuales.filter(estado=True).exists():
                count_sin_poliza_contractual += 1
                tiene_problema_vehiculo = True
                latest_doc = vehiculo.polizas_contractuales.order_by('-fecha_fin_vigencia').first()
                detalle = {'documento': 'Póliza Contractual', 'mensaje': 'No tiene Póliza Contractual activa.'}
                if latest_doc:
                    detalle['ultimo_numero_poliza'] = latest_doc.numero_poliza
                    detalle['ultima_fecha_fin_vigencia'] = latest_doc.fecha_fin_vigencia.isoformat() if latest_doc.fecha_fin_vigencia else None
                vencimientos_del_vehiculo.append(detalle)

            # Póliza Extracontractual
            if not vehiculo.polizas_extracontractuales.filter(estado=True).exists():
                count_sin_poliza_extracontractual += 1
                tiene_problema_vehiculo = True
                latest_doc = vehiculo.polizas_extracontractuales.order_by('-fecha_fin_vigencia').first()
                detalle = {'documento': 'Póliza Extracontractual', 'mensaje': 'No tiene Póliza Extracontractual activa.'}
                if latest_doc:
                    detalle['ultimo_numero_poliza'] = latest_doc.numero_poliza
                    detalle['ultima_fecha_fin_vigencia'] = latest_doc.fecha_fin_vigencia.isoformat() if latest_doc.fecha_fin_vigencia else None
                vencimientos_del_vehiculo.append(detalle)

            if tiene_problema_vehiculo:
                vehiculos_con_algun_problema_ids.add(vehiculo.pk)

            if vencimientos_del_vehiculo:
                report_detalle_vehiculos[placa_vehiculo] = vencimientos_del_vehiculo

        report_data_empresa = {
            'empresa_id': empresa.id,
            'empresa_nombre': empresa.nombre_empresa,
            'fecha_reporte': today.isoformat(),
            'resumen_vencimientos': {
                'total_vehiculos_empresa_activos': total_vehiculos_revisados_empresa,
                'vehiculos_sin_soat_activo': count_sin_soat,
                'vehiculos_sin_revision_tecnomecanica_activa': count_sin_tecno,
                'vehiculos_sin_tarjeta_operacion_activa': count_sin_tarjeta_op,
                'vehiculos_sin_poliza_contractual_activa': count_sin_poliza_contractual,
                'vehiculos_sin_poliza_extracontractual_activa': count_sin_poliza_extracontractual,
                'total_vehiculos_con_algun_documento_vencido_o_faltante': len(vehiculos_con_algun_problema_ids),
            },
            'vehiculos_con_vencimientos_detalle': report_detalle_vehiculos
        }

        ReporteVencimientosDiario.objects.update_or_create(
            empresa=empresa,
            fecha_reporte=today,
            defaults={'datos_reporte': report_data_empresa}
        )
