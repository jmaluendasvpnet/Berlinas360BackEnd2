from .models import TipoDocumento, Empresas, Roles, Colaboradores, Login, Acciones, Modulos, Permisos, Vehiculos, EventoDocumento, Event, EventParticipant, EventEvidence, Headquarters, Notification, Agenda, Evaluation, TrainingsCategories, Pregunta, RespuestaUsuario, ResultadoParte, CalificacionTotal, InductionDoc, Test, TestDrivers, TestDriversSession, WrittenTest, WrittenTestSession, Siniestro, SiniestroMedia, Department, Servicio, Propietario, Tenedor, Soat, RevisionTecnomecanica, TarjetaOperacion, LicenciaTransito, Poliza, NovedadVehiculo, FichaTecnica, ConductorAsociado, ProcedimientoJuridico, EventoLegal, EventoLegalFile, Mantenimiento, Facturacion, Marca, TipoLinea, ClaseVehiculo, Carroceria, Combustible, TipoOperacion, Ciudad, NivelServicio, Categoria, Color, VehiculoPropietario, VehiculoTenedor
from .serializers import TipoDocumentoSlr, EmpresasSlr, RolesSlr, ColaboradoresSlr, AccionesSlr, LoginSlr, ModulosSlr, EventoDocumentoSlr, PermisosSlr, HeadquartersSlr, VehiculosSlr, EventSerializer, AgendaSlr, EvaluationSlr, TrainingsCategoriesSlr, InductionDocSlr, TestSlr, TestDriversSlr, TestDriversSessionSlr, WrittenTestSlr, WrittenTestSessionSlr, TestDriversDetailSlr, SiniestrosSlr, SiniestroMediaSlr, DepartmentsSlr, EnteAtencionSlr, ServicioSlr, PropietarioSlr, TenedorSlr, SoatSlr, RevisionTecnomecanicaSlr, TarjetaOperacionSlr, LicenciaTransitoSlr, PolizaSlr, NovedadVehiculoSlr, FichaTecnicaSlr, ConductorAsociadoSlr, ProcedimientoJuridicoSerializer, EventoLegalSerializer, MantenimientoSlr, FacturacionSlr, MarcaSlr, TipoLineaSlr, ClaseVehiculoSlr, CarroceriaSlr, CombustibleSlr, TipoOperacionSlr, CiudadSlr, NivelServicioSlr, CategoriaSlr, ColorSlr
from django.db.models import Avg

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status, filters as drf_filters
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework import serializers
from django.db import transaction
import json
import uuid
import os
import requests

class FilterableViewSet(viewsets.ModelViewSet):
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    filterset_fields = '__all__'

    def get_queryset(self):
        queryset = super().get_queryset()
        filter_params = self.request.GET.dict()

        filter_params.pop('page', None)
        filter_params.pop('page_size', None)
        filter_params.pop('fetch_all_for_search', None)
        filter_params.pop('search', None)

        processed = {}
        for k, v in filter_params.items():
            if k.endswith('__isnull'):
                processed[k] = v.lower() == 'true'
            elif v:
                processed[k] = v

        if processed:
            try:
                queryset = queryset.filter(**processed)
            except Exception:
                pass

        return queryset


class FilterableViewSet2(viewsets.ModelViewSet):
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    filterset_fields = []

    def get_queryset(self):
        return super().get_queryset()

class TipoDocumentoViewSet(FilterableViewSet):
    queryset = TipoDocumento.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TipoDocumentoSlr

class EmpresasViewSet(FilterableViewSet):
    queryset = Empresas.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmpresasSlr

class DepartmentsViewSet(FilterableViewSet):
    queryset = Department.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DepartmentsSlr

class RolesViewSet(FilterableViewSet):
    queryset = Roles.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RolesSlr

class ColaboradoresViewSet(FilterableViewSet2):
    queryset = Colaboradores.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ColaboradoresSlr

    @action(detail=False, methods=['get'], url_path='by_department')
    def colaboradores_by_department(self, request):
        rol_id = request.query_params.get('rol_id')
        empresa_id = request.query_params.get('empresa_id')

        if not rol_id or not empresa_id:
            return Response({"error": "Se requieren los parámetros 'rol_id' y 'empresa_id'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rol = Roles.objects.select_related('department_id').get(id=rol_id, empresa_id=empresa_id)
        except Roles.DoesNotExist:
            return Response({"error": "No se encontró el rol con el 'rol_id' y 'empresa_id' proporcionados."}, status=status.HTTP_404_NOT_FOUND)

        department = rol.department_id

        colaboradores = Colaboradores.objects.filter(empresa_id=empresa_id, rol__department_id=department.id_department)

        serializer = self.get_serializer(colaboradores, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='colaboradores_training')
    def colaboradores_training(self, request):
        filter_params = request.query_params.dict()
        colaboradores = Colaboradores.objects.select_related('rol').filter(**filter_params)
        events = Event.objects.prefetch_related('event_required_roles', 'event_training_category').filter(event_type='capacitacion')
        event_dict = {event.id: event for event in events}

        role_to_required_events = {
            role.id: {event.id for event in events if role in event.event_required_roles.all()}
            for role in Roles.objects.all()
        }

        participations = EventParticipant.objects.select_related('colaborador', 'event').filter(event__event_type='capacitacion')
        
        colaborador_to_received_events = {}
        for participation in participations:
            colaborador = participation.colaborador.num_documento
            if colaborador not in colaborador_to_received_events:
                colaborador_to_received_events[colaborador] = set()
            colaborador_to_received_events[colaborador].add((
                participation.event.event_issue,
                participation.event.event_training_category.tr_ctg_abbreviation if participation.event.event_training_category else 'Sin Categoría',
                participation.event.id,
                participation.rating or 'No calificación',
                str(participation.fecha or 'No disponible')
            ))

        all_event_ids = set(event_dict.keys())

        def build_training_data(colaborador):
            required_event_ids = role_to_required_events.get(colaborador.rol.id, set())
            required_trainings = {
                (event.event_issue, event.event_training_category.tr_ctg_abbreviation if event.event_training_category else 'Sin Categoría', event.id)
                for event_id in required_event_ids
                for event in [event_dict[event_id]]
            }
            
            received_trainings = colaborador_to_received_events.get(colaborador.num_documento, set())
            received_simple = {(name, category, event_id) for name, category, event_id, _, _ in received_trainings}
            porcentaje_cumplimiento = (len(received_trainings) / len(required_trainings)) * 100 if required_trainings else 0

            return {
                "cedula": colaborador.num_documento,
                "nombres": f"{colaborador.nombres} {colaborador.apellidos}",
                "porcentajeCumplimiento": porcentaje_cumplimiento,
                "capacitacionesRequeridas": [{'nombre': name, 'categoria': category, 'event_id': event_id} for name, category, event_id in required_trainings],
                "capacitacionesRecibidas": [
                    {'nombre': name, 'categoria': category, 'event_id': event_id, 'rating': rating, 'fecha': fecha}
                    for name, category, event_id, rating, fecha in received_trainings
                ],
                "capacitacionesFaltantes": [
                    {'nombre': name, 'categoria': category, 'event_id': event_id}
                    for name, category, event_id in required_trainings - received_simple
                ],
                "capacitacionesOpcionales": [
                    {'nombre': event.event_issue, 'categoria': event.event_training_category.tr_ctg_abbreviation if event.event_training_category else 'Sin Categoría', 'event_id': event.id}
                    for event_id in all_event_ids - required_event_ids
                    for event in [event_dict[event_id]]
                ]
            }

        data = [build_training_data(colaborador) for colaborador in colaboradores]
        return Response(data)

class LoginViewSet(FilterableViewSet):
    queryset = Login.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoginSlr

class ModulosViewSet(FilterableViewSet):
    queryset = Modulos.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ModulosSlr

class AccionesVS(FilterableViewSet):
    queryset = Acciones.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccionesSlr

    def get_queryset(self):
        return Notification.objects.filter(user__num_documento=self.request.user.documento_num_id)
class PermisosViewSet(FilterableViewSet):
    queryset = Permisos.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PermisosSlr

    @action(detail=False, methods=['post'], url_path='update_role_permissions')
    def update_role_permissions(self, request):
        role_id = request.data.get('role_id')
        module_ids = request.data.get('module_ids', [])
        if not role_id:
            return Response({'detail': 'El campo role_id es requerido.'}, status=400)

        existing_qs = Permisos.objects.filter(rol_id=role_id)
        existing_ids = set(existing_qs.values_list('modulo_id', flat=True))
        to_add = set(module_ids) - existing_ids
        to_remove = existing_ids - set(module_ids)

        Permisos.objects.filter(rol_id=role_id, modulo_id__in=to_remove).delete()
        new_perms = [Permisos(rol_id=role_id, modulo_id=mid, estado_permiso=True) for mid in to_add]
        Permisos.objects.bulk_create(new_perms)

        return Response({'detail': 'Permisos actualizados correctamente.'})

class HeadquartersViewSet(FilterableViewSet2):
    queryset = Headquarters.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = HeadquartersSlr

class NotificationVS(FilterableViewSet):
    queryset = Notification.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = Notification

class VehiculosVS(FilterableViewSet2):
    queryset = Vehiculos.objects.select_related(
        'servicio', 'empresa', 'marca', 'tipoLinea', 'clase',
        'carroceria', 'combustible', 'ciudadBase', 'color'
    ).all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VehiculosSlr

    ordering_fields = [
        'placa',
        'servicio__numeroInterno',
        'modelo',
        'empresa',
        'empresa__nombre',
        'marca',
        'marca__nombre',
        'estado',
        'ciudadBase',
        'ciudadBase__nombre'
    ]
    ordering = ['placa']

    def get_queryset(self):
        queryset = super().get_queryset()
        query_params = self.request.query_params

        for param, value in query_params.items():
            if param.endswith('__in') and value:
                try:
                    queryset = queryset.filter(**{param: value.split(',')})
                except FieldError as e:
                    print(f"Advertencia: Parámetro de filtro inválido '{param}': {e}")
                    pass

        if 'placa__icontains' in query_params:
            filter_value = query_params.get('placa__icontains')
            if filter_value:
                 queryset = queryset.filter(placa__icontains=filter_value)

        if 'servicio__numeroInterno' in query_params:
            filter_value = query_params.get('servicio__numeroInterno')
            if filter_value:
                queryset = queryset.filter(servicio__numeroInterno=filter_value)

        if 'propietarios_relations__propietario__identificacion' in query_params:
            lookup = 'propietarios_relations__propietario__identificacion'
            valor = query_params.get(lookup)
            if valor:
                queryset = queryset.filter(**{lookup: valor})

        if 'empresa' in query_params:
            filter_value = query_params.get('empresa')
            if filter_value and 'empresa__in' not in query_params and 'empresa_id__in' not in query_params :
                queryset = queryset.filter(empresa__id=filter_value)

        if 'marca' in query_params:
            filter_value = query_params.get('marca')
            if filter_value and 'marca__in' not in query_params and 'marca_id__in' not in query_params:
                queryset = queryset.filter(marca__id=filter_value)

        if 'estado' in query_params:
            filter_value = query_params.get('estado')
            if filter_value:
                queryset = queryset.filter(estado=filter_value)

        if 'ciudadBase' in query_params:
            filter_value = query_params.get('ciudadBase')
            if filter_value and 'ciudadBase__in' not in query_params and 'ciudadBase_id__in' not in query_params:
                queryset = queryset.filter(ciudadBase__id=filter_value)

        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        print("Datos recibidos en la solicitud:", request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        print("Errores de validación:", serializer.errors)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            raise

    @action(detail=True, methods=['get'], url_path='propietarios', permission_classes=[permissions.IsAuthenticated])
    def propietarios_del_vehiculo(self, request, pk=None):
        vehiculo = self.get_object()
        propietarios = Propietario.objects.filter(vehiculos_relations__vehiculo=vehiculo).distinct()
        serializer_context = {
            'request': request,
            'placa_vehiculo_actual': vehiculo.placa
        }
        page = self.paginate_queryset(propietarios)
        if page is not None:
            serializer = PropietarioSlr(page, many=True, context=serializer_context)
            return self.get_paginated_response(serializer.data)
        serializer = PropietarioSlr(propietarios, many=True, context=serializer_context)
        return Response(serializer.data)
    

        
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import EventoDocumento, Vehiculos, Empresas
from .serializers import EventoDocumentoSlr

EMAIL_ORIGEN = "jmaluendasbautista@gmail.com"
PASSWORD_EMAIL_ORIGEN = "akpa ecrt crgj uert"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
HOST = 'berlinasdelfonce'
PASS = 'akpa ecrt crgj uert'

class EventoDocumentoViewSet(FilterableViewSet):
    queryset = EventoDocumento.objects.all()
    serializer_class = EventoDocumentoSlr
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        placa = request.data.get('vehiculo')
        tipo_doc = request.data.get('tipo_documento')
        datos_json = request.data.get('datos_json', {})

        vehiculo_obj = get_object_or_404(Vehiculos, pk=placa)
        empresa_obj = vehiculo_obj.empresa

        evento = EventoDocumento.objects.create(
            vehiculo=vehiculo_obj,
            empresa=empresa_obj,
            tipo_documento=tipo_doc,
            datos_json=datos_json
        )

        if 'pdf_file' in request.FILES:
            evento.pdf_file = request.FILES['pdf_file']
            evento.save()

        serializer = self.get_serializer(evento)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if 'vehiculo' in request.data:
            placa = request.data.get('vehiculo')
            vehiculo_obj = get_object_or_404(Vehiculos, pk=placa)
            request.data._mutable = True
            request.data['empresa'] = vehiculo_obj.empresa.id if vehiculo_obj.empresa else None
            request.data._mutable = False

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        evento = self.get_object()
        if isinstance(datos, str):
            try:
                datos = json.loads(datos)
            except json.JSONDecodeError:
                datos = {}

        email_usuario = datos.get('email', '')
        if not email_usuario:
            return Response(
                {'detail': 'Este evento no tiene un email asociado en datos_json.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not evento.pdf_file:
            return Response(
                {'detail': 'No hay PDF asociado a este evento.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tipo_doc = evento.tipo_documento
        asunto = ''
        cuerpo_html = ''
        if tipo_doc == 'hurtoOferta':
            asunto = "Respuesta a Hurto con Oferta"
            cuerpo_html = """
            <html>
            <body>
              <p>Estimado(a),</p>
              <p>Adjuntamos el documento respectivo de la reclamación "Hurto con Oferta".</p>
              <p>Saludos cordiales.</p>
            </body>
            </html>
            """
        elif tipo_doc == 'hurtoSinOfertaGeneral':
            asunto = "Respuesta a Hurto sin Oferta (General)"
            cuerpo_html = """
            <html>
            <body>
              <p>Estimado(a),</p>
              <p>Adjuntamos el documento de su reclamación 'Hurto sin Oferta (General)'.</p>
              <p>Saludos cordiales.</p>
            </body>
            </html>
            """
        elif tipo_doc == 'hurtoSinOferta':
            asunto = "Respuesta a Hurto sin Oferta"
            cuerpo_html = """
            <html>
            <body>
              <p>Estimado(a),</p>
              <p>Adjuntamos el documento con la respuesta de 'Hurto sin Oferta'.</p>
              <p>Saludos cordiales.</p>
            </body>
            </html>
            """
        elif tipo_doc == 'fallaConductor':
            asunto = "Respuesta a Falla Conductor"
            cuerpo_html = """
            <html>
            <body>
              <p>Estimado(a),</p>
              <p>Adjuntamos la respuesta por falla del conductor.</p>
              <p>Saludos cordiales.</p>
            </body>
            </html>
            """
        elif tipo_doc == 'peConResponsabilidad':
            asunto = "Respuesta a PE con Responsabilidad"
            cuerpo_html = """
            <html>
            <body>
              <p>Estimado(a),</p>
              <p>Adjuntamos el documento de 'PE con Responsabilidad (Sí)'.</p>
              <p>Saludos cordiales.</p>
            </body>
            </html>
            """
        elif tipo_doc == 'peConResponsabilidadEvidencia':
            asunto = "Respuesta a PE con Responsabilidad (Sí) c/ Evidencia"
            cuerpo_html = """
            <html>
            <body>
              <p>Estimado(a),</p>
              <p>Adjuntamos el documento de 'PE con Responsabilidad (Sí) c/ Evidencia'.</p>
              <p>Saludos cordiales.</p>
            </body>
            </html>
            """
        elif tipo_doc == 'paso2':
            asunto = "Respuesta Hurto de Equipaje - Paso 2"
            cuerpo_html = """
            <html>
            <body>
              <p>Estimado(a),</p>
              <p>Adjuntamos el documento 'Hurto de Equipaje - Paso 2'.</p>
              <p>Saludos cordiales.</p>
            </body>
            </html>
            """
        else:
            asunto = "Respuesta a su reclamación"
            cuerpo_html = """
            <html>
            <body>
              <p>Estimado(a),</p>
              <p>Adjuntamos el documento respectivo.</p>
              <p>Saludos cordiales.</p>
            </body>
            </html>
            """

        try:
            mensaje = MIMEMultipart()
            mensaje["From"] = EMAIL_ORIGEN
            mensaje["To"] = email_usuario
            mensaje["Subject"] = asunto

            mensaje.attach(MIMEText(cuerpo_html, "html"))

            pdf_path = evento.pdf_file.path
            filename = os.path.basename(pdf_path)
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{filename}"',
            )
            mensaje.attach(part)

            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
                smtp.login(EMAIL_ORIGEN, PASSWORD_EMAIL_ORIGEN)
                smtp.sendmail(EMAIL_ORIGEN, email_usuario, mensaje.as_string())

            return Response({"detail": f"Email enviado correctamente a {email_usuario}."},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"Error al enviar correo: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )        

    @action(detail=True, methods=['patch'])
    def marcar_finalizado(self, request, pk=None):
        evento = self.get_object()
        evento.status = 'finalizado'
        evento.save()
        return Response({'detail': 'El evento se marcó como finalizado.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def contrapropuesta(self, request, pk=None):
        evento_original = self.get_object()

        nuevo_evento = EventoDocumento.objects.create(
            vehiculo=evento_original.vehiculo,
            empresa=evento_original.empresa,
            tipo_documento='contrapropuesta',
            datos_json={
                'referente': evento_original.id,
                'mensaje': 'Contrapropuesta generada',
            }
        )
        serializer = self.get_serializer(nuevo_evento)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ServicioVS(FilterableViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSlr
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        placa = self.request.data.get('vehiculo')
        vehiculo = get_object_or_404(Vehiculos, placa=placa)
        instance, created = Servicio.objects.get_or_create(
            vehiculo=vehiculo,
            defaults=serializer.validated_data
        )
        if not created:
            for attr, value in serializer.validated_data.items():
                setattr(instance, attr, value)
            instance.save()

    def perform_update(self, serializer):
        placa = self.request.data.get('vehiculo')
        vehiculo = get_object_or_404(Vehiculos, placa=placa)
        serializer.save(vehiculo=vehiculo)

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .models import Contrato, Propietario
from .serializers import ContratoSerializer

HOST = 'berlinasdelfonce'
PASS = 'akpa ecrt crgj uert'

class ContratoVS(FilterableViewSet2):
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer

    @action(detail=False, methods=['post'], url_path='enviar-firma')
    def enviar_firma(self, request):
        placa = request.data.get('placa', None)
        if not placa:
            return Response({"detail": "Falta la placa"}, status=status.HTTP_400_BAD_REQUEST)

        owners = Propietario.objects.filter(vehiculos_relations__vehiculo__placa=placa)
        if not owners.exists():
            return Response({"detail": f"No hay propietarios asociados al vehículo {placa}"}, status=status.HTTP_404_NOT_FOUND)

        contrato, created = Contrato.objects.get_or_create(placa=placa)

        url_firma = f"http://localhost:8000/c_v?placa={placa}"
        contrato.link_firma = url_firma
        contrato.save()

        try:
            email_origen = "jmaluendasbautista@gmail.com"
            asunto = "Solicitud de Firma de Contrato"
            ruta_img = "https://saas-cms-admin-sandbox.s3.us-west-2.amazonaws.com/sites/647e59513d04a300028afa72/assets/647e59b33d04a300028afa77/Logo_berlinas_blanco_fondo-transparente_DIGITAL.png"

            for owner in owners:
                if not owner.correo:
                    continue

                mensaje = MIMEMultipart()
                mensaje["From"] = email_origen
                mensaje["To"] = owner.correo
                mensaje["Subject"] = asunto

                cuerpo_html = f"""
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="UTF-8">
                    <title>Solicitud de Firma de Contrato</title>
                </head>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="max-width: 700px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 10px; background-color: #fff; box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);">
                        <div style="text-align: center; background-color: #009944; border-radius: 10px;">
                            <img src="{ruta_img}" alt="Logo" style="max-width: 150px; display: block; margin: 20px auto;">
                        </div>
                        <div style="margin-top: 20px; line-height: 1.6; color: #000;">
                            <p>Estimado(a) <strong>{owner.nombres}</strong>,</p>
                            <p style="color: #000 !important;">
                                Le informamos que su Contrato de Vinculación se encuentra listo para su firma digital.
                                Por favor ingrese al siguiente enlace para revisar y firmar el documento:
                            </p>
                            <p style="text-align: center;">
                                <a style="text-decoration: none; background-color: #009944; color: #fff; padding: 10px 20px; border-radius: 5px;" href="{url_firma}">
                                    Firmar Contrato
                                </a>
                            </p>
                            <p style="color: #000 !important;">
                                Si tiene alguna inquietud o necesita asistencia, por favor responda a este correo.
                            </p>
                            <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;">
                            <p style="color: #009944;"><strong>Cordialmente,</strong></p>
                            <p style="color: #000 !important;">
                                Departamento Jurídico<br>
                                <a style="text-decoration: none; color: #009944;" href="mailto:juridica@berlinasdelfonce.com">juridica@berlinasdelfonce.com</a><br>
                                Celular: <a style="text-decoration: none; color: #009944;" href="https://api.whatsapp.com/send?phone=+573165269210">3165269210</a><br>
                                Teléfono: <a style="text-decoration: none; color: #009944;" href="">(601) 743 5050 ext. 1003</a><br>
                                Cra. 68D No.15-15 Zona Industrial Montevideo<br>
                                Bogotá D.C. - Colombia
                            </p>
                        </div>
                        <div style="margin-top: 30px; font-style: italic; font-size: 10px; color: #888; text-align: center;">
                            <p>© 2025 - Todos los derechos reservados</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                mensaje.attach(MIMEText(cuerpo_html, "html"))

                smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
                smtp.login(email_origen, PASS)
                smtp.sendmail(email_origen, owner.correo, mensaje.as_string())
                smtp.quit()

        except Exception as e:
            return Response(
                {"detail": f"Error al enviar correo: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "detail": "Correos enviados exitosamente", 
            "link_firma": url_firma
        }, status=status.HTTP_200_OK)


class PropietarioVS(FilterableViewSet):
    queryset = Propietario.objects.all()
    serializer_class = PropietarioSlr
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'identificacion'
    lookup_url_kwarg = 'identificacion'
    lookup_value_regex = r'[\w\.-]+'

    def get_queryset(self):
        placa = self.request.query_params.get('vehiculo')
        if placa:
            return Propietario.objects.filter(vehiculos_relations__vehiculo__placa=placa)
        return super().get_queryset()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['placa_vehiculo_actual'] = self.request.query_params.get('vehiculo')
        return context

    def perform_create(self, serializer):
        placa = self.request.data.get('vehiculo')
        porcentaje = self.request.data.get('porcentaje')
        vehiculo = get_object_or_404(Vehiculos, placa=placa)
        identificacion = serializer.validated_data.get('identificacion')
        propietario = Propietario.objects.filter(identificacion=identificacion).first()
        if not propietario:
            propietario = serializer.save()
        VehiculoPropietario.objects.update_or_create(
            vehiculo=vehiculo,
            propietario=propietario,
            defaults={'porcentaje': porcentaje}
        )

    def destroy(self, request, *args, **kwargs):
        identificacion = kwargs.get('identificacion')
        instance = self.get_object()
        placa = request.query_params.get('vehiculo')
        if placa:
            vehiculo = get_object_or_404(Vehiculos, placa=placa)
            VehiculoPropietario.objects.filter(
                vehiculo=vehiculo,
                propietario=instance
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        # Si no se especifica placa, devolvemos 400
        return Response(
            {'detail': 'Debe especificar el parámetro "vehiculo" para eliminar la relación.'},
            status=status.HTTP_400_BAD_REQUEST
        )

            
class TenedorVS(FilterableViewSet):
    queryset = Tenedor.objects.all()
    serializer_class = TenedorSlr
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        placa = self.request.query_params.get('vehiculo')
        if placa:
            qs = qs.filter(vehiculos_relations__vehiculo__vehiculo=placa)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['placa'] = self.request.query_params.get('vehiculo')
        return context

    def perform_create(self, serializer):
        placa = self.request.data.get('vehiculo')
        porcentaje = self.request.data.get('porcentaje')
        vehiculo = get_object_or_404(Vehiculos, placa=placa)
        identificacion = serializer.validated_data.get('identificacion')
        tenedor = Tenedor.objects.filter(identificacion=identificacion).first()
        if tenedor:
            update_fields = {
                k: v for k, v in serializer.validated_data.items()
                if k not in ['vehiculo', 'porcentaje']
            }
            for field, new_value in update_fields.items():
                setattr(tenedor, field, new_value)
            tenedor.save()
        else:
            tenedor = serializer.save()
        from .models import VehiculoTenedor
        VehiculoTenedor.objects.update_or_create(
            vehiculo=vehiculo,
            tenedor=tenedor,
            defaults={'porcentaje': porcentaje}
        )

from .models import (
    Vehiculos, Soat, RevisionTecnomecanica, TarjetaOperacion, LicenciaTransito,
    PolizaContractual, PolizaExtracontractual, PolizaTodoRiesgo, ReporteVencimientosDiario
)
from .serializers import (
    SoatSlr, RevisionTecnomecanicaSlr, TarjetaOperacionSlr, LicenciaTransitoSlr,
    PolizaContractualSlr, PolizaExtracontractualSlr, PolizaTodoRiesgoSlr, ReporteVencimientosDiarioSlr
)
from .tasks import actualizar_estados_y_generar_reportes
import datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework import serializers

class ReporteVencimientosDiarioVS(FilterableViewSet2):
    queryset = ReporteVencimientosDiario.objects.all()
    serializer_class = ReporteVencimientosDiarioSlr

class SoatVS(FilterableViewSet):
    queryset = Soat.objects.all()
    serializer_class = SoatSlr

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            print(f"[{datetime.now()}] SERIALIZER ERRORS: {serializer.errors}")
            raise e 
        except Exception as e:
            print(f"[{datetime.now()}] UNEXPECTED EXCEPTION during is_valid: {str(e)}")
            raise e

        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        placa = serializer.validated_data.get('placa')

        if not placa:
            print(f"[{datetime.now()}] ERROR: Placa no encontrada en serializer.validated_data.")
            raise serializers.ValidationError({"placa": "Placa es requerida y no fue proporcionada."})
            
        try:
            vehiculo = Vehiculos.objects.get(placa=placa)
        except Vehiculos.DoesNotExist:
            print(f"[{datetime.now()}] ERROR: Vehículo con placa {placa} no encontrado en la BD.")
            raise serializers.ValidationError(f'Vehículo con placa {placa} no encontrado.')
        except Exception as e:
            print(f"[{datetime.now()}] ERROR al buscar Vehiculo con placa {placa}: {str(e)}")
            raise serializers.ValidationError(f'Error interno al buscar vehículo con placa {placa}.')

        try:
            serializer.save(vehiculo=vehiculo)
        except Exception as e:
            print(f"[{datetime.now()}] ERROR during serializer.save(): {str(e)}")
            raise serializers.ValidationError(f"Error al guardar el SOAT: {str(e)}")
        
        try:
            actualizar_estados_y_generar_reportes.delay()
        except Exception as e:
            print(f"[{datetime.now()}] WARNING: Failed to dispatch Celery task for placa {placa}: {str(e)}")

    def perform_update(self, serializer):
        placa = serializer.validated_data.get('placa')
        try:
            vehiculo = Vehiculos.objects.get(placa=placa)
        except Vehiculos.DoesNotExist:
            raise serializers.ValidationError(f'Vehículo con placa {placa} no encontrado.')
        serializer.save(vehiculo=vehiculo)

class RevisionTecnomecanicaVS(FilterableViewSet):
    queryset = RevisionTecnomecanica.objects.all()
    serializer_class = RevisionTecnomecanicaSlr

    def perform_create(self, serializer):
        placa = serializer.validated_data.get('placa')
        try:
            vehiculo = Vehiculos.objects.get(placa=placa)
        except Vehiculos.DoesNotExist:
            raise serializers.ValidationError(f'Vehículo con placa {placa} no encontrado.')
        serializer.save(vehiculo=vehiculo)
        actualizar_estados_y_generar_reportes.delay()

    def perform_update(self, serializer):
        placa = serializer.validated_data.get('placa')
        try:
            vehiculo = Vehiculos.objects.get(placa=placa)
        except Vehiculos.DoesNotExist:
            raise serializers.ValidationError(f'Vehículo con placa {placa} no encontrado.')
        serializer.save(vehiculo=vehiculo)

class TarjetaOperacionVS(FilterableViewSet):
    queryset = TarjetaOperacion.objects.all()
    serializer_class = TarjetaOperacionSlr

    def perform_create(self, serializer):
        _create_poliza_instance(serializer, serializer.validated_data, model_name_for_log="TarjetaOperacion")

    def perform_update(self, serializer):
        placa = serializer.validated_data.get('placa')
        if not placa:
            raise serializers.ValidationError({"placa": "Placa es requerida para actualizar."})
        try:
            vehiculo = Vehiculos.objects.get(placa=placa)
        except Vehiculos.DoesNotExist:
            raise serializers.ValidationError(f'Vehículo con placa {placa} no encontrado.')
        serializer.save(vehiculo=vehiculo)
        actualizar_estados_y_generar_reportes.delay()

class LicenciaTransitoVS(FilterableViewSet):
    queryset = LicenciaTransito.objects.all()
    serializer_class = LicenciaTransitoSlr

    def create(self, request, *args, **kwargs):
        print("=== LicenciaTransito Create ===")
        print("DATA:", request.POST)
        print("FILES:", request.FILES)

        data = request.POST.dict()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        placa = serializer.validated_data.get('placa') or serializer.validated_data.get('numero_documento')
        try:
            vehiculo = Vehiculos.objects.get(placa=placa)
        except Vehiculos.DoesNotExist:
            return Response(
                {'placa': f'Vehículo con placa {placa} no encontrado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        soporte_file = request.FILES.get('soporte')
        soporte_path = None
        if soporte_file:
            filename = f'licenses/{uuid.uuid4().hex}_{soporte_file.name}'
            soporte_path = default_storage.save(filename, soporte_file)

        serializer.save(vehiculo=vehiculo, soporte=soporte_path)
        actualizar_estados_y_generar_reportes.delay()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        print("=== LicenciaTransito Update ===")
        print("DATA:", request.POST)
        print("FILES:", request.FILES)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        data = request.POST.dict()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        placa = serializer.validated_data.get('placa') or serializer.validated_data.get('numero_documento')
        try:
            vehiculo = Vehiculos.objects.get(placa=placa)
        except Vehiculos.DoesNotExist:
            return Response(
                {'placa': f'Vehículo con placa {placa} no encontrado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        soporte_file = request.FILES.get('soporte')
        if soporte_file:
            filename = f'licenses/{uuid.uuid4().hex}_{soporte_file.name}'
            soporte_path = default_storage.save(filename, soporte_file)
            serializer.save(vehiculo=vehiculo, soporte=soporte_path)
        else:
            serializer.save(vehiculo=vehiculo)

        actualizar_estados_y_generar_reportes.delay()
        return Response(serializer.data)    

        
def _create_poliza_instance(serializer, request_data, model_name_for_log="Poliza"):
    placa_str_from_vehiculo_key = request_data.get('vehiculo')
    placa_str_from_placa_key = request_data.get('placa')

    final_placa_str = placa_str_from_vehiculo_key or placa_str_from_placa_key

    if not final_placa_str:
        raise serializers.ValidationError({"placa": ["No se proporcionó la placa del vehículo (esperada en el campo 'vehiculo' o 'placa' del payload)."]})

    try:
        vehiculo_instance = Vehiculos.objects.get(placa=final_placa_str)
    except Vehiculos.DoesNotExist:
        raise serializers.ValidationError({"detail": f"Vehículo con placa {final_placa_str} no encontrado."})
    except Exception as e:
        raise serializers.ValidationError({"detail": f"Error interno al buscar vehículo: {str(e)}"})

    try:
        serializer.save(vehiculo=vehiculo_instance)
    except Exception as e:
        if hasattr(e, 'detail'):
            raise serializers.ValidationError(e.detail)
        raise serializers.ValidationError({"detail": f"Error al guardar {model_name_for_log.lower()}: {str(e)}"})
    
    try:
        actualizar_estados_y_generar_reportes.delay()
    except Exception as e:
        print(f"[{datetime.now()}] WARNING: Failed to dispatch Celery task for placa {final_placa_str}: {str(e)}")

class PolizaContractualVS(FilterableViewSet):
    queryset = PolizaContractual.objects.all()
    serializer_class = PolizaContractualSlr

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            _create_poliza_instance(serializer, request.data, model_name_for_log="PolizaContractual")
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error interno del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class PolizaExtracontractualVS(FilterableViewSet):
    queryset = PolizaExtracontractual.objects.all()
    serializer_class = PolizaExtracontractualSlr

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            _create_poliza_instance(serializer, request.data, model_name_for_log="PolizaExtracontractual")
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error interno del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class PolizaTodoRiesgoVS(FilterableViewSet):
    queryset = PolizaTodoRiesgo.objects.all()
    serializer_class = PolizaTodoRiesgoSlr

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            _create_poliza_instance(serializer, request.data, model_name_for_log="PolizaTodoRiesgo")
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error interno del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
class PolizaVS(FilterableViewSet):
    queryset = Poliza.objects.all()
    serializer_class = PolizaSlr

class NovedadVehiculoVS(FilterableViewSet):
    queryset = NovedadVehiculo.objects.all()
    serializer_class = NovedadVehiculoSlr

class FichaTecnicaVS(FilterableViewSet):
    queryset = FichaTecnica.objects.all()
    serializer_class = FichaTecnicaSlr

class ConductorAsociadoVS(FilterableViewSet):
    queryset = ConductorAsociado.objects.all()
    serializer_class = ConductorAsociadoSlr

class ProcedimientoJuridicoViewSet(FilterableViewSet):
    queryset = ProcedimientoJuridico.objects.all()
    serializer_class = ProcedimientoJuridicoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        vehiculo_placa = self.request.query_params.get('vehiculo')
        if vehiculo_placa:
            qs = qs.filter(vehiculo__placa=vehiculo_placa)
        return qs


class EventoLegalViewSet(FilterableViewSet2):
    queryset = EventoLegal.objects.all().prefetch_related('archivos')
    serializer_class = EventoLegalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        vehiculo_placa = self.request.query_params.get('vehiculo')
        if vehiculo_placa:
            qs = qs.filter(vehiculo__placa=vehiculo_placa)
        return qs.order_by('-fecha_creacion')

    def create(self, request, *args, **kwargs):
        vehiculo_placa = request.data.get('vehiculo')
        tipo_evento = request.data.get('tipo_evento')
        archivos = request.FILES.getlist('pdf_soporte')

        if not vehiculo_placa or not tipo_evento:
            return Response(
                {"detail": "Faltan parámetros (vehiculo, tipo_evento)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vehiculo = Vehiculos.objects.get(placa=vehiculo_placa)
        except Vehiculos.DoesNotExist:
            return Response(
                {"detail": "No existe vehículo con esa placa."},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_event_types = [choice[0] for choice in EventoLegal.TIPO_EVENTO_CHOICES]
        if tipo_evento not in valid_event_types:
            return Response(
                {"detail": f"Tipo de evento '{tipo_evento}' no es válido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        evento = EventoLegal.objects.create(
            vehiculo=vehiculo,
            tipo_evento=tipo_evento,
        )

        files_created = []
        for archivo in archivos:
            file_instance = EventoLegalFile.objects.create(
                evento_legal=evento,
                archivo=archivo
            )
            files_created.append(file_instance)

        serializer = self.get_serializer(evento)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        evento = self.get_object()
        archivos = request.FILES.getlist('pdf_soporte')

        if not archivos:
             return Response(
                 {"detail": "No se proporcionaron archivos para agregar."},
                 status=status.HTTP_400_BAD_REQUEST
             )

        files_created = []
        for archivo in archivos:
            file_instance = EventoLegalFile.objects.create(
                evento_legal=evento,
                archivo=archivo
            )
            files_created.append(file_instance)

        serializer = self.get_serializer(evento)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MantenimientoVS(FilterableViewSet):
    queryset = Mantenimiento.objects.all()
    serializer_class = MantenimientoSlr

class FacturacionVS(FilterableViewSet):
    queryset = Facturacion.objects.all()
    serializer_class = FacturacionSlr

from django.db.models import Exists, OuterRef
class MarcaVS(FilterableViewSet):
    serializer_class = MarcaSlr
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre']

    def get_queryset(self):
        fetch_all_for_search = self.request.query_params.get('fetch_all_for_search', 'false').lower() == 'true'
        
        specific_filters_present = any(
            key not in ['page', 'page_size', 'ordering', 'fetch_all_for_search', 'search'] 
            and self.request.query_params[key]
            for key in self.request.query_params
        )

        if fetch_all_for_search or specific_filters_present:
            return Marca.objects.all()
        else:
            return Marca.objects.filter(Exists(Vehiculos.objects.filter(marca=OuterRef('pk')))).distinct()

class TipoLineaVS(FilterableViewSet):
    serializer_class = TipoLineaSlr
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre']

    def get_queryset(self):
        fetch_all_for_search = self.request.query_params.get('fetch_all_for_search', 'false').lower() == 'true'
        specific_filters_present = any(
            key not in ['page', 'page_size', 'ordering', 'fetch_all_for_search', 'search']
            and self.request.query_params[key]
            for key in self.request.query_params
        )
        if fetch_all_for_search or specific_filters_present:
            return TipoLinea.objects.all()
        else:
            return TipoLinea.objects.filter(Exists(Vehiculos.objects.filter(tipoLinea=OuterRef('pk')))).distinct()

class ClaseVehiculoVS(FilterableViewSet):
    queryset = ClaseVehiculo.objects.all()
    serializer_class = ClaseVehiculoSlr
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre']

class CarroceriaVS(FilterableViewSet):
    serializer_class = CarroceriaSlr
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre']
    
    def get_queryset(self):
        fetch_all_for_search = self.request.query_params.get('fetch_all_for_search', 'false').lower() == 'true'
        specific_filters_present = any(
            key not in ['page', 'page_size', 'ordering', 'fetch_all_for_search', 'search']
            and self.request.query_params[key]
            for key in self.request.query_params
        )
        if fetch_all_for_search or specific_filters_present:
            return Carroceria.objects.all()
        else:
            return Carroceria.objects.filter(Exists(Vehiculos.objects.filter(carroceria=OuterRef('pk')))).distinct()


class CombustibleVS(FilterableViewSet):
    queryset = Combustible.objects.all()
    serializer_class = CombustibleSlr
    permission_classes = [permissions.IsAuthenticated]

class TipoOperacionVS(FilterableViewSet):
    queryset = TipoOperacion.objects.all()
    serializer_class = TipoOperacionSlr
    permission_classes = [permissions.IsAuthenticated]

class CiudadVS(FilterableViewSet):
    queryset = Ciudad.objects.all()
    serializer_class = CiudadSlr
    permission_classes = [permissions.IsAuthenticated]

class NivelServicioVS(FilterableViewSet):
    queryset = NivelServicio.objects.all()
    serializer_class = NivelServicioSlr
    permission_classes = [permissions.IsAuthenticated]

class CategoriaVS(FilterableViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSlr
    permission_classes = [permissions.IsAuthenticated]

class ColorVS(FilterableViewSet):
    serializer_class = ColorSlr
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre']

    def get_queryset(self):
        fetch_all_for_search = self.request.query_params.get('fetch_all_for_search', 'false').lower() == 'true'
        specific_filters_present = any(
            key not in ['page', 'page_size', 'ordering', 'fetch_all_for_search', 'search']
            and self.request.query_params[key]
            for key in self.request.query_params
        )
        if fetch_all_for_search or specific_filters_present:
            return Color.objects.all()
        else:
            return Color.objects.filter(Exists(Vehiculos.objects.filter(color=OuterRef('pk')))).distinct()


from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Prefetch
from .models import (
    Evaluation, Part, Section, Question, Option,
    MatchingPair, OrderingItem, MultiSelectOption,
    HotspotCoordinate, FillBlank
)
from .serializers import EvaluationSerializer, MinimalEvaluationSerializer

class EvaluationViewSet(FilterableViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return MinimalEvaluationSerializer
        return EvaluationSerializer

    def get_queryset(self):
        if self.action == 'list':
            return Evaluation.objects.select_related('created_by').only(
                'id', 'title', 'description', 'global_time_limit',
                'randomize_questions', 'randomize_answers',
                'created_by', 'created_at', 'updated_at'
            )
        else:
            return Evaluation.objects.select_related('created_by').prefetch_related(
                'parts',
                'parts__questions',
                'parts__sections',
                'parts__sections__questions',
                'sections',
                'sections__questions',
                'questions',
                'questions__options',
                'questions__matching_pairs',
                'questions__ordering_items',
                'questions__multi_select_options',
                'questions__hotspot_coordinates',
                'questions__fill_blanks'
            )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as exc:
            return Response({"errors": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"errors": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except ValidationError as exc:
            return Response({"errors": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"errors": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

from datetime import datetime, timedelta
class AgendaViewSet(FilterableViewSet):
    queryset = Agenda.objects.all()
    serializer_class = AgendaSlr
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='work_schedule')
    def work_schedule(self, request):
        colaborador_id = request.query_params.get('agenda_colaborador_id')
        if not colaborador_id:
            return Response({"error": "agenda_colaborador_id es requerido"}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Agenda.objects.filter(
            agenda_colaborador_id=colaborador_id,
            agenda_type='work'
        )
        
        agenda_start_date_gte = request.query_params.get('agenda_start_date__gte')
        agenda_start_date_lte = request.query_params.get('agenda_start_date__lte')
        
        if agenda_start_date_gte:
            queryset = queryset.filter(agenda_start_date__gte=agenda_start_date_gte)
        if agenda_start_date_lte:
            queryset = queryset.filter(agenda_start_date__lte=agenda_start_date_lte)
        
        schedules = queryset
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='supervised_work_schedule')
    def supervised_work_schedule(self, request):
        rol_id = request.query_params.get('rol_id')
        empresa_id = request.query_params.get('empresa_id')
        week_start_date = request.query_params.get('week_start_date')

        if not rol_id or not empresa_id or not week_start_date:
            return Response({"error": "Se requieren los parámetros 'rol_id', 'empresa_id' y 'week_start_date'."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rol = Roles.objects.select_related('department_id').get(id=rol_id, empresa_id=empresa_id)
        except Roles.DoesNotExist:
            return Response({"error": "No se encontró el rol con el 'rol_id' y 'empresa_id' proporcionados."}, status=status.HTTP_404_NOT_FOUND)
        
        department = rol.department_id

        colaboradores = Colaboradores.objects.filter(empresa=empresa_id, rol__department=department.id_department)
        colaborador_ids = colaboradores.values_list('num_documento', flat=True)
        
        try:
            week_start = datetime.strptime(week_start_date, '%Y-%m-%d').date()
            week_end = week_start + timedelta(days=6)
        except ValueError:
            return Response({"error": "Formato de fecha inválido para 'week_start_date'. Use 'YYYY-MM-DD'."}, status=status.HTTP_400_BAD_REQUEST)
        
        agendas = Agenda.objects.filter(
            agenda_colaborador_id__in=colaborador_ids,
            agenda_start_date__gte=week_start,
            agenda_start_date__lte=week_end,
            agenda_type='work',
        )
        
        serializer = self.get_serializer(agendas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
class EventsViewSet(FilterableViewSet):
    queryset = Event.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EventSerializer

    def destroy(self, request, *args, **kwargs):
        event = self.get_object()
        Agenda.objects.filter(agenda_colaborador_id=event.event_responsible).delete()
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], url_path='upload_evidences', parser_classes=[MultiPartParser, FormParser])
    def upload_evidences(self, request, pk=None):
        event = self.get_object()
        files = request.FILES.getlist('files')

        if not files:
            return Response({'error': 'No se proporcionaron archivos.'}, status=status.HTTP_400_BAD_REQUEST)

        file_urls = []
        for file in files:
            filename = default_storage.save(f'events_evidences/{file.name}', file)
            file_url = default_storage.url(filename)

            evidence = EventEvidence.objects.create(
                event=event,
                evidence_file=filename,
                evidence_type=file.content_type
            )

            file_urls.append({
                'id': evidence.id,
                'url': file_url,
                'type': evidence.evidence_type
            })

        return Response({'evidences': file_urls}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='trainings')
    def get_event_trainings(self, request, pk=None):
        event = self.get_object()
        training_data = event.get_trainings_for_roles()
        return Response(training_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='events_by_collaborator')
    def events_by_collaborator(self, request):
        colaborador_id = request.query_params.get('colaborador_id')
        event_type = request.query_params.get('event_type', None) 

        if not colaborador_id:
            return Response({'error': 'colaborador_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            colaborador = Colaboradores.objects.get(num_documento=colaborador_id)
            participations = EventParticipant.objects.filter(colaborador=colaborador)
            event_ids = participations.values_list('event_id', flat=True)
            events = Event.objects.filter(id__in=event_ids).distinct()
            if event_type:
                events = events.filter(event_type=event_type)
            serializer = EventSerializer(events, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Colaboradores.DoesNotExist:
            return Response({'error': 'Colaborador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='attendance')
    def get_event_attendance(self, request, pk=None):
        event = self.get_object()
        event_attendance_data = event.get_event_attendance()
        return Response(event_attendance_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='attendance_drivers')
    def get_event_attendance_drivers(self, request, pk=None):
        event = self.get_object()
        event_attendance_data = event.get_event_attendance_drivers()
        return Response(event_attendance_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'], url_path='register_attendance')
    def register_attendance(self, request, pk=None):
        event = self.get_object()
        user_id = request.data.get('user_id')
        rating = request.data.get('rating', None)
        fecha = request.data.get('fecha', None)

        colaborador = Colaboradores.objects.get(num_documento=user_id)
        if EventParticipant.objects.filter(event=event, colaborador=colaborador).exists():
            return Response({'status': 'El usuario ya ha sido registrado previamente para este evento.'}, status=status.HTTP_400_BAD_REQUEST)

        EventParticipant.objects.create(
            event=event,
            colaborador=colaborador,
            rating=rating,
            fecha=fecha
        )

        return Response({'status': 'Asistencia registrada exitosamente'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'], url_path='update_evaluation')
    def update_event_evaluation(self, request, pk=None):
        event = self.get_object()
        evaluation_id = request.data.get('evaluation_id')

        if evaluation_id:
            try:
                evaluation = Evaluation.objects.get(id_evaluation=evaluation_id)
                event.event_evaluation = evaluation
                event.save()
                return Response({'status': 'Evaluación actualizada exitosamente'}, status=status.HTTP_200_OK)
            except Evaluation.DoesNotExist:
                return Response({'error': 'Evaluación no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'ID de evaluación no proporcionado'}, status=status.HTTP_400_BAD_REQUEST)

class TrainingsCategoriesViewSet(FilterableViewSet):
    queryset = TrainingsCategories.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrainingsCategoriesSlr

class EnviarRespuestasViewSet(FilterableViewSet):
    def post(self, request, *args, **kwargs):
        usuario = request.user
        respuestas = request.data.get('respuestas', [])

        for respuesta_data in respuestas:
            pregunta_id = respuesta_data.get('pregunta')
            respuesta_seleccionada = respuesta_data.get('respuesta_seleccionada')

            pregunta = Pregunta.objects.get(id=pregunta_id)
            RespuestaUsuario.objects.create(
                usuario=usuario,
                pregunta=pregunta,
                respuesta_seleccionada=respuesta_seleccionada
            )

        partes = set([respuesta_data.get('parte') for respuesta_data in respuestas])

        for parte_id in partes:
            preguntas_en_parte = Pregunta.objects.filter(parte_id=parte_id)
            respuestas_usuario = RespuestaUsuario.objects.filter(usuario=usuario, pregunta__parte_id=parte_id)

            correctas = respuestas_usuario.filter(es_correcta=True).count()
            total_preguntas = preguntas_en_parte.count()

            calificacion = (correctas / total_preguntas) * 100

            ResultadoParte.objects.update_or_create(
                usuario=usuario,
                parte_id=parte_id,
                defaults={'calificacion': calificacion}
            )

        calificaciones = ResultadoParte.objects.filter(usuario=usuario).aggregate(promedio=Avg('calificacion'))
        promedio_total = calificaciones['promedio']

        CalificacionTotal.objects.update_or_create(
            usuario=usuario,
            defaults={'promedio': promedio_total}
        )

        return Response({'mensaje': 'Respuestas registradas correctamente', 'promedio_total': promedio_total}, status=status.HTTP_201_CREATED)
class InductionDocViewSet(FilterableViewSet):
    serializer_class = InductionDocSlr
    queryset = InductionDoc.objects.all().select_related('responsable_induccion', 'cedula_empleado', 'lugar')

    def get_queryset(self):
        queryset = super().get_queryset()
        cedula_empleado = self.request.query_params.get('cedula_empleado', None)
        if cedula_empleado is not None:
            queryset = queryset.filter(cedula_empleado__num_documento=cedula_empleado)
        return queryset

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        induction_doc = get_object_or_404(queryset, cedula_empleado__num_documento=pk)
        serializer = self.get_serializer(induction_doc)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        colaborador = serializer.instance.cedula_empleado
        self.update_colaborador(colaborador, request.data)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        print(request.data)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        colaborador = serializer.instance.cedula_empleado
        self.update_colaborador(colaborador, request.data)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def update_colaborador(self, colaborador, data):
        nombre_empleado = data.get('nombre_empleado')
        cargo_id = data.get('cargo')
        firma_empleado = data.get('firma_empleado')
        face_ids = data.get('face_ids')
        exp_documento = data.get('exp_documento')
        email = data.get('email')

        if nombre_empleado:
            nombres, apellidos = self.separar_nombres_apellidos(nombre_empleado)
            colaborador.nombres = nombres
            colaborador.apellidos = apellidos

        if cargo_id:
            rol = Roles.objects.filter(id=cargo_id).first()
            if rol:
                colaborador.rol = rol

        if firma_empleado:
            colaborador.signature = firma_empleado

        if face_ids:
            colaborador.face_ids = face_ids

        if exp_documento:
            colaborador.exp_documento = exp_documento

        if email:
            colaborador.email = email

        colaborador.save()

    def separar_nombres_apellidos(self, nombre_completo):
        nombres = []
        apellidos = []
        palabras = nombre_completo.split()
        num_palabras = len(palabras)

        if num_palabras == 2:
            nombres = [palabras[0]]
            apellidos = [palabras[1]]
        elif num_palabras == 3:
            nombres = [palabras[0]]
            apellidos = palabras[1:]
        elif num_palabras == 4:
            nombres = palabras[:2]
            apellidos = palabras[2:]
        elif num_palabras >= 5:
            nombres = palabras[:3]
            apellidos = palabras[3:]
        else:
            nombres = palabras

        return ' '.join(nombres), ' '.join(apellidos)
    
class TestViewSet(FilterableViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSlr

class TestDriversViewSet(FilterableViewSet):
    queryset = TestDrivers.objects.all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TestDriversDetailSlr
        return TestDriversSlr

class TestDriversSessionViewSet(FilterableViewSet):
    queryset = TestDriversSession.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TestDriversSessionSlr
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_completed:
            return Response({'message': 'El test ya ha sido completado.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_completed:
            return Response({'message': 'No se puede actualizar, el test ya ha sido completado.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_completed:
            return Response({'message': 'No se puede actualizar parcialmente, el test ya ha sido completado.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

class WrittenTestViewSet(FilterableViewSet):
    queryset = WrittenTest.objects.all()
    serializer_class = WrittenTestSlr

class WrittenTestSessionVS(FilterableViewSet):
    queryset = WrittenTestSession.objects.all()
    serializer_class = WrittenTestSessionSlr

from rest_framework import permissions, status, viewsets, mixins
from django.core.files.storage import default_storage
from .utils import WHISPER_MODEL
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
import requests
import json
import uuid
import os
from .models import (
    Siniestro, SiniestroMedia, SiniestroLog,
    EnteAtencion, Colaboradores, Vehiculos,
    Empresas, Tercero, ActaConciliacion, Ipat,
    ProcesoDefinicion, EtapaDefinicion, SubEtapaDefinicion, ActuacionDefinicion,
    Victima, VictimaProceso, HistorialActuacion, SiniestroHistorialActuacion, SiniestroProceso
)
from .serializers import (
    SiniestrosSlr, SiniestroMediaSlr, SiniestroLogSlr,
    EnteAtencionSlr, TerceroSlr, ActaConciliacionSlr, IpatSlr,
    ColaboradoresSlr, VehiculosSlr, EmpresasSlr,
    ProcesoDefinicionSlr, EtapaDefinicionSlr, SubEtapaDefinicionSlr, ActuacionDefinicionSlr,
    VictimaSlr, VictimaProcesoSlr, HistorialActuacionSlr, SiniestroHistorialActuacionSlr, SiniestroProcesoSlr
)    

from django.contrib.auth import get_user_model
class SiniestroVS(FilterableViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SiniestrosSlr
    filterset_fields = [
        f.name for f in Siniestro._meta.get_fields()
        if f.name != 'datos_adicionales'
    ]

    def get_queryset(self):
        return Siniestro.objects.all().prefetch_related(
            'entes_atendieron', 'media', 'logs', 'terceros',
            'victimas__proceso_estado__historial_actuaciones__actuacion_definicion__sub_etapa_definicion__etapa_definicion',
            'victimas__proceso_estado__proceso_definicion_actual__etapas__sub_etapas__actuaciones',
            'victimas__proceso_estado__etapa_definicion_actual',
            'victimas__proceso_estado__sub_etapa_definicion_actual',
            'victimas__proceso_estado__actuacion_definicion_siguiente',
            'acta_conciliacion', 'ipat_record',
            'proceso_detalle_siniestro__historial_actuaciones_siniestro__actuacion_definicion__sub_etapa_definicion__etapa_definicion', 
            'proceso_detalle_siniestro__proceso_definicion_actual__etapas__sub_etapas__actuaciones', 
            'proceso_detalle_siniestro__etapa_definicion_actual', 
            'proceso_detalle_siniestro__sub_etapa_definicion_actual', 
            'proceso_detalle_siniestro__actuacion_definicion_siguiente'
        ).select_related(
            'colaborador', 'vehiculo', 'empresa', 
            'proceso_detalle_siniestro' 
        )

    def determine_zona(self, latitud, longitud):
        try:
            api_key = settings.Maps_API_KEY
            url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitud},{longitud}&key={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for result in data.get('results', []):
                    types_in_result = []
                    for comp in result.get('address_components', []):
                        comp_types = comp.get('types', [])
                        types_in_result.extend(comp_types)
                    if 'locality' in types_in_result or 'sublocality' in types_in_result:
                        return 'Urbana'
                return 'Rural'
            return 'Urbana'
        except:
            return 'Urbana'

    def process_audio_file(self, audio_file):
        file_extension = audio_file.name.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = default_storage.save(f"siniestros_media/{unique_filename}", audio_file)
        full_path = default_storage.path(file_path)

        result = WHISPER_MODEL.transcribe(full_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
        return result["text"]

    def save_audio_media(self, siniestro, audio_file):
        file_extension = audio_file.name.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        saved_path = default_storage.save(f"siniestros_media/{unique_filename}", audio_file)
        SiniestroMedia.objects.create(
            siniestro=siniestro,
            file_url=saved_path,
            tipo='audio'
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        placa = request.data.get('placa')
        documento_conductor = request.data.get('documento_conductor')

        vehiculo_instance = None
        colaborador_instance = None
        empresa_instance = None

        if placa:
            try:
                vehiculo_instance = Vehiculos.objects.get(placa=placa)
            except Vehiculos.DoesNotExist:
                return Response({"error": f"El vehículo con placa {placa} no existe."}, status=status.HTTP_400_BAD_REQUEST)
        
        if documento_conductor:
            try:
                colaborador_instance = Colaboradores.objects.get(num_documento=documento_conductor)
                if colaborador_instance.empresa:
                    empresa_instance = colaborador_instance.empresa
            except Colaboradores.DoesNotExist:
                return Response({"error": f"El colaborador con documento {documento_conductor} no existe."}, status=status.HTTP_400_BAD_REQUEST)

        siniestro_data_copy = request.data.copy()

        if vehiculo_instance:
            siniestro_data_copy['vehiculo'] = vehiculo_instance.pk
        if colaborador_instance:
            siniestro_data_copy['colaborador'] = colaborador_instance.pk
        if empresa_instance:
            siniestro_data_copy['empresa'] = empresa_instance.pk
        
        if 'latitud' in siniestro_data_copy and 'longitud' in siniestro_data_copy and siniestro_data_copy['latitud'] and siniestro_data_copy['longitud']:
            siniestro_data_copy['zona'] = self.determine_zona(siniestro_data_copy['latitud'], siniestro_data_copy['longitud'])
        
        serializer = self.get_serializer(data=siniestro_data_copy)
        if serializer.is_valid():
            siniestro_instance = serializer.save() 
            
            SiniestroLog.objects.create(
                siniestro=siniestro_instance,
                user=colaborador_instance,
                action="Siniestro creado."
            )
            return Response(self.get_serializer(siniestro_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        
        user_for_log = None
        user_id_from_request = data.pop('user_id', None)

        if user_id_from_request:
            actual_user_id = user_id_from_request[0] if isinstance(user_id_from_request, list) and user_id_from_request else user_id_from_request
            try:
                user_for_log = Colaboradores.objects.get(num_documento=actual_user_id)
            except Colaboradores.DoesNotExist:
                pass
        
        # if not user_for_log and request.user.is_authenticated:
        #     try:
        #         user_model_instance = get_object_or_404(get_user_model(), username=request.user.username)
        #         user_for_log = Colaboradores.objects.get(num_documento=user_model_instance.username) 
        #     except (Colaboradores.DoesNotExist, get_user_model().DoesNotExist):
        #          pass


        if 'descripcion_audio' in request.FILES:
            try:
                transcription = self.process_audio_file(request.FILES['descripcion_audio'])
                if instance.descripcion:
                    data['descripcion'] = instance.descripcion + "\n" + transcription
                else:
                    data['descripcion'] = transcription
                self.save_audio_media(instance, request.FILES['descripcion_audio'])
                SiniestroLog.objects.create(
                    siniestro=instance,
                    user=user_for_log,
                    action="Audio descripción procesada y actualizada."
                )
            except Exception as e:
                return Response({"error": f"Error al procesar audio: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        latitud_str = data.get('latitud')
        longitud_str = data.get('longitud')

        if latitud_str and longitud_str:
            try:
                new_lat = float(latitud_str)
                new_lng = float(longitud_str)
                if (instance.latitud is None or float(instance.latitud) != new_lat) or \
                   (instance.longitud is None or float(instance.longitud) != new_lng):
                    data['latitud'] = new_lat
                    data['longitud'] = new_lng
                    data['zona'] = self.determine_zona(new_lat, new_lng)
                    SiniestroLog.objects.create(
                        siniestro=instance,
                        user=user_for_log,
                        action="Ubicación actualizada."
                    )
            except ValueError:
                return Response({"error": "Latitud y longitud deben ser números válidos."}, status=status.HTTP_400_BAD_REQUEST)


        entes_ids_data = data.pop('entes_atendieron', None) 
        if entes_ids_data is None:
             entes_ids_data = data.pop('entes_atendieron_ids', None)

        if entes_ids_data is not None:
            final_entes_ids = []
            if isinstance(entes_ids_data, list) and len(entes_ids_data) > 0 and isinstance(entes_ids_data[0], str):
                try:
                    parsed_list = json.loads(entes_ids_data[0])
                    if isinstance(parsed_list, list):
                        final_entes_ids = parsed_list
                except json.JSONDecodeError:
                    final_entes_ids = [x.strip() for item in entes_ids_data for x in item.split(',') if x.strip()]

            elif isinstance(entes_ids_data, list):
                final_entes_ids = entes_ids_data
            elif isinstance(entes_ids_data, str):
                if entes_ids_data.startswith('[') and entes_ids_data.endswith(']'):
                    try:
                        final_entes_ids = json.loads(entes_ids_data)
                    except json.JSONDecodeError:
                        final_entes_ids = [x.strip() for x in entes_ids_data.split(',') if x.strip()]
                else:
                     final_entes_ids = [x.strip() for x in entes_ids_data.split(',') if x.strip()]
            
            try:
                valid_entes_ids = [int(eid) for eid in final_entes_ids if str(eid).isdigit()]
                instance.entes_atendieron.set(valid_entes_ids)
            except (ValueError, TypeError) as e:
                print(f"Error setting entes_atendieron: {e}, data: {final_entes_ids}")


        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        SiniestroLog.objects.create(
            siniestro=instance,
            user=user_for_log,
            action="Siniestro actualizado."
        )
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        siniestro_id = request.query_params.get('id')
        if siniestro_id:
            queryset = queryset.filter(id=siniestro_id)
            if not queryset.exists():
                 return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def _get_effective_action_status_siniestro(self, actuacion_def_id, historial_actuaciones_qs):
        relevant_logs = historial_actuaciones_qs.filter(actuacion_definicion_id=actuacion_def_id).order_by('-timestamp_registro')
        if not relevant_logs.exists():
            return 'pendiente'
        
        latest_log = relevant_logs.first()
        
        if latest_log.status_actuacion == 'omitida_temporalmente':
            resolving_actions = historial_actuaciones_qs.filter(resuelve_omision_de=latest_log.id, status_actuacion='completada')
            if resolving_actions.exists():
                 return 'completada'
        
        return latest_log.status_actuacion

    def _calculate_next_siniestro_state(self, siniestro_proceso_instance):
        proceso_def = siniestro_proceso_instance.proceso_definicion_actual
        if not proceso_def:
            siniestro_proceso_instance.estado_general = 'no_iniciado'
            siniestro_proceso_instance.etapa_definicion_actual = None
            siniestro_proceso_instance.sub_etapa_definicion_actual = None
            siniestro_proceso_instance.actuacion_definicion_siguiente = None
            siniestro_proceso_instance.save()
            return

        historial_qs = siniestro_proceso_instance.historial_actuaciones_siniestro.all()
        
        etapas_ordenadas = sorted(list(proceso_def.etapas.all()), key=lambda e: e.orden)

        for etapa_def_iter in etapas_ordenadas:
            sub_etapas_ordenadas = sorted(list(etapa_def_iter.sub_etapas.all()), key=lambda se: se.orden)
            for sub_etapa_def_iter in sub_etapas_ordenadas:
                actuaciones_ordenadas = sorted(list(sub_etapa_def_iter.actuaciones.all()), key=lambda a: a.orden)
                for actuacion_def_iter in actuaciones_ordenadas:
                    effective_status = self._get_effective_action_status_siniestro(actuacion_def_iter.id, historial_qs)
                    if effective_status == 'pendiente':
                        siniestro_proceso_instance.etapa_definicion_actual = etapa_def_iter
                        siniestro_proceso_instance.sub_etapa_definicion_actual = sub_etapa_def_iter
                        siniestro_proceso_instance.actuacion_definicion_siguiente = actuacion_def_iter
                        siniestro_proceso_instance.estado_general = 'en_progreso'
                        siniestro_proceso_instance.save()
                        return
        
        for etapa_def_iter in etapas_ordenadas:
            sub_etapas_ordenadas = sorted(list(etapa_def_iter.sub_etapas.all()), key=lambda se: se.orden)
            for sub_etapa_def_iter in sub_etapas_ordenadas:
                actuaciones_ordenadas = sorted(list(sub_etapa_def_iter.actuaciones.all()), key=lambda a: a.orden)
                for actuacion_def_iter in actuaciones_ordenadas:
                    effective_status = self._get_effective_action_status_siniestro(actuacion_def_iter.id, historial_qs)
                    if effective_status == 'en_espera':
                        siniestro_proceso_instance.etapa_definicion_actual = etapa_def_iter
                        siniestro_proceso_instance.sub_etapa_definicion_actual = sub_etapa_def_iter
                        siniestro_proceso_instance.actuacion_definicion_siguiente = actuacion_def_iter
                        siniestro_proceso_instance.estado_general = 'en_progreso'
                        siniestro_proceso_instance.save()
                        return
        
        for etapa_def_iter in etapas_ordenadas:
            sub_etapas_ordenadas = sorted(list(etapa_def_iter.sub_etapas.all()), key=lambda se: se.orden)
            for sub_etapa_def_iter in sub_etapas_ordenadas:
                actuaciones_ordenadas = sorted(list(sub_etapa_def_iter.actuaciones.all()), key=lambda a: a.orden)
                for actuacion_def_iter in actuaciones_ordenadas:
                    effective_status = self._get_effective_action_status_siniestro(actuacion_def_iter.id, historial_qs)
                    if effective_status == 'omitida_temporalmente':
                        siniestro_proceso_instance.etapa_definicion_actual = etapa_def_iter
                        siniestro_proceso_instance.sub_etapa_definicion_actual = sub_etapa_def_iter
                        siniestro_proceso_instance.actuacion_definicion_siguiente = actuacion_def_iter
                        siniestro_proceso_instance.estado_general = 'en_progreso'
                        siniestro_proceso_instance.save()
                        return
        
        siniestro_proceso_instance.estado_general = 'terminado'
        last_etapa = None
        if etapas_ordenadas:
            last_etapa = etapas_ordenadas[-1]
            siniestro_proceso_instance.etapa_definicion_actual = last_etapa
            last_subetapa = None
            sub_etapas_last_etapa = sorted(list(last_etapa.sub_etapas.all()), key=lambda se: se.orden)
            if sub_etapas_last_etapa:
                last_subetapa = sub_etapas_last_etapa[-1]
                siniestro_proceso_instance.sub_etapa_definicion_actual = last_subetapa
                actuaciones_last_subetapa = sorted(list(last_subetapa.actuaciones.all()), key=lambda a: a.orden)
                if actuaciones_last_subetapa:
                    siniestro_proceso_instance.actuacion_definicion_siguiente = actuaciones_last_subetapa[-1]
                else:
                    siniestro_proceso_instance.actuacion_definicion_siguiente = None
            else:
                siniestro_proceso_instance.sub_etapa_definicion_actual = None
                siniestro_proceso_instance.actuacion_definicion_siguiente = None
        else:
            siniestro_proceso_instance.etapa_definicion_actual = None
            siniestro_proceso_instance.sub_etapa_definicion_actual = None
            siniestro_proceso_instance.actuacion_definicion_siguiente = None
        siniestro_proceso_instance.save()

    @action(detail=True, methods=['post'], url_path='iniciar-proceso-general')
    @transaction.atomic
    def iniciar_proceso_general(self, request, pk=None):
        siniestro_instance = self.get_object()
        siniestro_proceso, created = SiniestroProceso.objects.get_or_create(siniestro=siniestro_instance)
        
        proceso_definicion_id = request.data.get('proceso_definicion_id')
        
        if not proceso_definicion_id:
            return Response({"error": "proceso_definicion_id es requerido."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            proceso_def = ProcesoDefinicion.objects.get(id=proceso_definicion_id)
        except ProcesoDefinicion.DoesNotExist:
            return Response({"error": "ProcesoDefinicion no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if siniestro_proceso.estado_general != 'no_iniciado' and not created:
            if siniestro_proceso.proceso_definicion_actual == proceso_def :
                self._calculate_next_siniestro_state(siniestro_proceso)
                serializer = SiniestroProcesoSlr(siniestro_proceso, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                 return Response({"error": "El siniestro ya tiene un proceso general diferente en curso."}, status=status.HTTP_400_BAD_REQUEST)

        siniestro_proceso.proceso_definicion_actual = proceso_def
        siniestro_proceso.etapa_definicion_actual = None
        siniestro_proceso.sub_etapa_definicion_actual = None
        siniestro_proceso.actuacion_definicion_siguiente = None
        siniestro_proceso.estado_general = 'en_progreso'
        siniestro_proceso.save() 
        
        self._calculate_next_siniestro_state(siniestro_proceso)
        
        serializer = SiniestroProcesoSlr(siniestro_proceso, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='registrar-actuacion-general')
    @transaction.atomic
    def registrar_actuacion_general(self, request, pk=None):
        siniestro_instance = self.get_object()
        try:
            siniestro_proceso = SiniestroProceso.objects.get(siniestro=siniestro_instance)
        except SiniestroProceso.DoesNotExist:
             return Response({"error": "El proceso general para este siniestro no ha sido iniciado."}, status=status.HTTP_400_BAD_REQUEST)

        if siniestro_proceso.estado_general == 'terminado':
            return Response({"error": "El proceso general para este siniestro ya ha terminado."}, status=status.HTTP_400_BAD_REQUEST)
        if siniestro_proceso.estado_general == 'no_iniciado' or not siniestro_proceso.proceso_definicion_actual:
            return Response({"error": "El proceso general debe ser iniciado antes de registrar actuaciones."}, status=status.HTTP_400_BAD_REQUEST)

        request_data = request.data.copy()
        request_data['siniestro_proceso'] = siniestro_proceso.id

        historial_serializer = SiniestroHistorialActuacionSlr(data=request_data, context={'request': request, 'view': self})
        historial_serializer.is_valid(raise_exception=True)
        
        actuacion_def = historial_serializer.validated_data['actuacion_definicion']
        
        if actuacion_def.sub_etapa_definicion.etapa_definicion.proceso_definicion != siniestro_proceso.proceso_definicion_actual:
            return Response(
                {"error": "La actuación no pertenece al proceso general actual del siniestro."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document_file = historial_serializer.validated_data.get('documento')
        original_doc_name = document_file.name if document_file else None

        login_user_instance = None
        if request.user.is_authenticated:
            try:
                UserModel = get_user_model()
                if isinstance(request.user, UserModel):
                    login_user_instance = request.user
            except Exception:
                pass


        historial_instance = historial_serializer.save(
            creado_por=login_user_instance, 
            documento_nombre_original=original_doc_name
        )
        
        if actuacion_def.terminaProceso and historial_instance.status_actuacion in ['completada', 'omitida_permanentemente']:
            siniestro_proceso.estado_general = 'terminado'
            siniestro_proceso.etapa_definicion_actual = actuacion_def.sub_etapa_definicion.etapa_definicion
            siniestro_proceso.sub_etapa_definicion_actual = actuacion_def.sub_etapa_definicion
            siniestro_proceso.actuacion_definicion_siguiente = actuacion_def
            siniestro_proceso.save()
        else:
            self._calculate_next_siniestro_state(siniestro_proceso)
            
        return Response(SiniestroHistorialActuacionSlr(historial_instance, context={'request': request, 'view': self}).data, status=status.HTTP_201_CREATED)


class SiniestroMediaVS(FilterableViewSet):
    queryset = SiniestroMedia.objects.all()
    serializer_class = SiniestroMediaSlr
    permission_classes = [permissions.IsAuthenticated]

class EnteAtencionVS(FilterableViewSet):
    queryset = EnteAtencion.objects.all()
    serializer_class = EnteAtencionSlr
    permission_classes = [permissions.IsAuthenticated]

class TerceroVS(FilterableViewSet):
    queryset = Tercero.objects.all()
    serializer_class = TerceroSlr
    permission_classes = [permissions.IsAuthenticated]

class ActaConciliacionVS(FilterableViewSet):
    queryset = ActaConciliacion.objects.all()
    serializer_class = ActaConciliacionSlr
    permission_classes = [permissions.IsAuthenticated]

class IpatVS(FilterableViewSet2):
    queryset = Ipat.objects.all()
    serializer_class = IpatSlr
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['siniestro']

    def get_queryset(self):
        queryset = super().get_queryset()
        siniestro = self.request.query_params.get('siniestro')
        if siniestro is not None:
            queryset = queryset.filter(siniestro=siniestro)
        return queryset

    def process_audio_file(self, audio_file):
        ext = audio_file.name.split('.')[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        path = default_storage.save(f"ipat_audio/{filename}", audio_file)
        full = default_storage.path(path)
        result = WHISPER_MODEL.transcribe(full)
        if os.path.exists(full):
            os.remove(full)
        return result["text"]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        payload = {}

        scalar_keys = [
            'siniestro', 'clase_evento','clase_evento_otro','choque_con','clase_vehiculo','objeto_fijo',
            'alineacion_horizontal','alineacion_vertical','utilizacion_vial',
            'calzadas','carriles','superficie_rodadura','superficie_rodadura_otro',
            'condicion_vial','condicion_vial_otra','iluminacion','iluminacion_detalle'
        ]
        for key in scalar_keys:
            if key in data:
                payload[key] = data.get(key)
        
        json_field_keys = [
            'diseno_via','opciones_geometricas', 'lugar_impacto', 'impact_visual', 
            'impact_visual_lines','testigos', 'elementos_laterales','estado_vial',
            'controles_transito', 'control_items','control_other','control_sub_items',
            'hipotesis_conductor','hipotesis_vehiculo', 'hipotesis_via',
            'hipotesis_peaton','hipotesis_pasajero', 'area', 'sector', 'zona',
            'croquis_lines', 'condicion_climatica'
        ]
        for key in json_field_keys:
            if key in data:
                try:
                    if isinstance(data.get(key), (dict, list)):
                        payload[key] = data.get(key)
                    elif isinstance(data.get(key), str) and data.get(key):
                        payload[key] = json.loads(data.get(key))
                    elif not data.get(key) and key in ['impact_visual_lines', 'control_items', 'control_other', 'control_sub_items']:
                        payload[key] = {}
                    elif not data.get(key):
                        payload[key] = []
                except (json.JSONDecodeError, TypeError) as e:
                    payload[key] = {} if key in ['impact_visual_lines', 'control_items', 'control_other', 'control_sub_items'] else []

        preguntas = []
        i = 0
        while True:
            qk_value = data.get(f"interrogatorio_conductor[{i}][question]")
            if f"interrogatorio_conductor[{i}][question]" not in data and f"interrogatorio_conductor[{i}][answerText]" not in data and f"interrogatorio_conductor[{i}][answerAudio]" not in request.FILES :
                break
            
            question = qk_value if qk_value is not None else ""
            answer = data.get(f"interrogatorio_conductor[{i}][answerText]", "")
            audio_file_key = f"interrogatorio_conductor[{i}][answerAudio]"
            audio  = request.FILES.get(audio_file_key)

            if audio:
                try:
                    answer = self.process_audio_file(audio)
                except Exception as e:
                    answer = f"Error procesando audio: {answer}"
            
            preguntas.append({"question": question, "answerText": answer})
            i += 1
        if preguntas or "interrogatorio_conductor" in data :
            payload['interrogatorio_conductor'] = preguntas

        if 'impact_visual_svg' in request.FILES:
            payload['impact_visual_svg'] = request.FILES['impact_visual_svg']

        serializer = self.get_serializer(data=payload)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    def update(self, request, *args, **kwargs):
        data = request.data.copy()
        instance = self.get_object()
        payload = {}

        scalar_keys = [
            'clase_evento','clase_evento_otro','choque_con','clase_vehiculo','objeto_fijo',
            'alineacion_horizontal','alineacion_vertical','utilizacion_vial',
            'calzadas','carriles','superficie_rodadura','superficie_rodadura_otro',
            'condicion_vial','condicion_vial_otra','iluminacion','iluminacion_detalle'
        ]
        for key in scalar_keys:
            val = data.get(key)
            if val is not None and str(val).lower() != 'undefined':
                payload[key] = val

        json_keys = [
            'diseno_via','opciones_geometricas', 'lugar_impacto', 'impact_visual',
            'impact_visual_lines','testigos', 'elementos_laterales','estado_vial',
            'controles_transito', 'control_items','control_other','control_sub_items',
            'hipotesis_conductor','hipotesis_vehiculo', 'hipotesis_via',
            'hipotesis_peaton','hipotesis_pasajero', 'area', 'sector', 'zona',
            'croquis_lines', 'condicion_climatica'
        ]
        for key in json_keys:
            raw = data.get(key)
            if raw is not None and str(raw).lower() != 'undefined':
                try:
                    if isinstance(raw, (dict, list)):
                        payload[key] = raw
                    elif isinstance(raw, str) and raw:
                        payload[key] = json.loads(raw)
                    elif not raw and key in ['impact_visual_lines', 'control_items', 'control_other', 'control_sub_items']:
                        payload[key] = {}
                    elif not raw:
                        payload[key] = []
                except (json.JSONDecodeError, TypeError) as e:
                    pass

        preguntas = []
        i = 0
        is_interrogatorio_update = any(k.startswith("interrogatorio_conductor[") for k in data.keys()) or any(k.startswith("interrogatorio_conductor[") for k in request.FILES.keys())

        if is_interrogatorio_update:
            while True:
                q_key_exists = f"interrogatorio_conductor[{i}][question]" in data
                a_text_key_exists = f"interrogatorio_conductor[{i}][answerText]" in data
                a_audio_key_exists = f"interrogatorio_conductor[{i}][answerAudio]" in request.FILES

                if not q_key_exists and not a_text_key_exists and not a_audio_key_exists:
                    break
                
                question = data.get(f"interrogatorio_conductor[{i}][question]", "")
                answer = data.get(f"interrogatorio_conductor[{i}][answerText]", "")
                audio_file_key = f"interrogatorio_conductor[{i}][answerAudio]"
                audio  = request.FILES.get(audio_file_key)
                
                if audio:
                    try:
                        answer = self.process_audio_file(audio)
                    except Exception as e:
                        answer = f"Error procesando audio: {answer}"

                preguntas.append({"question": question, "answerText": answer})
                i += 1
            payload['interrogatorio_conductor'] = preguntas
        
        if 'impact_visual_svg' in request.FILES:
            payload['impact_visual_svg'] = request.FILES['impact_visual_svg']
        elif data.get('impact_visual_svg') == '' or (data.get('impact_visual_svg') is None and 'impact_visual_svg' in data):
            if instance.impact_visual_svg:
                instance.impact_visual_svg.delete(save=False)
            payload['impact_visual_svg'] = None

        serializer = self.get_serializer(instance, data=payload, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)

class ProcesoDefinicionVS(FilterableViewSet):
    queryset = ProcesoDefinicion.objects.all().prefetch_related('etapas__sub_etapas__actuaciones')
    serializer_class = ProcesoDefinicionSlr
    permission_classes = [permissions.IsAuthenticated]

class EtapaDefinicionVS(FilterableViewSet):
    queryset = EtapaDefinicion.objects.all()
    serializer_class = EtapaDefinicionSlr
    permission_classes = [permissions.IsAuthenticated]

class SubEtapaDefinicionVS(FilterableViewSet):
    queryset = SubEtapaDefinicion.objects.all()
    serializer_class = SubEtapaDefinicionSlr
    permission_classes = [permissions.IsAuthenticated]

class ActuacionDefinicionVS(FilterableViewSet):
    queryset = ActuacionDefinicion.objects.all()
    serializer_class = ActuacionDefinicionSlr
    permission_classes = [permissions.IsAuthenticated]

class VictimaVS(FilterableViewSet):
    queryset = Victima.objects.all()
    serializer_class = VictimaSlr
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        victima = serializer.save()
        VictimaProceso.objects.get_or_create(victima=victima)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
class VictimaProcesoVS(viewsets.ModelViewSet):
    queryset = VictimaProceso.objects.all().select_related(
        'victima', 'proceso_definicion_actual',
        'etapa_definicion_actual', 'sub_etapa_definicion_actual',
        'actuacion_definicion_siguiente'
    ).prefetch_related(
        'historial_actuaciones__actuacion_definicion__sub_etapa_definicion__etapa_definicion__proceso_definicion',
        'proceso_definicion_actual__etapas__sub_etapas__actuaciones'
    )
    serializer_class = VictimaProcesoSlr
    permission_classes = [permissions.IsAuthenticated]

    def _get_effective_action_status(self, actuacion_def_id, historial_actuaciones_qs):
        relevant_logs = historial_actuaciones_qs.filter(actuacion_definicion_id=actuacion_def_id).order_by('-timestamp_registro')
        if not relevant_logs.exists():
            return 'pendiente'
        
        latest_log = relevant_logs.first()
        
        if latest_log.status_actuacion == 'omitida_temporalmente':
            if latest_log.resuelve_omision_de and latest_log.resuelve_omision_de.status_actuacion == 'completada':
                 return 'completada' 
        
        return latest_log.status_actuacion


    def _calculate_next_victim_state(self, victima_proceso_instance):
        proceso_def = victima_proceso_instance.proceso_definicion_actual
        if not proceso_def:
            victima_proceso_instance.estado_general = 'no_iniciado'
            victima_proceso_instance.etapa_definicion_actual = None
            victima_proceso_instance.sub_etapa_definicion_actual = None
            victima_proceso_instance.actuacion_definicion_siguiente = None
            victima_proceso_instance.save()
            return

        historial_qs = victima_proceso_instance.historial_actuaciones.all()
        
        etapas_ordenadas = sorted(list(proceso_def.etapas.all()), key=lambda e: e.orden)

        for etapa_def_iter in etapas_ordenadas:
            sub_etapas_ordenadas = sorted(list(etapa_def_iter.sub_etapas.all()), key=lambda se: se.orden)
            for sub_etapa_def_iter in sub_etapas_ordenadas:
                actuaciones_ordenadas = sorted(list(sub_etapa_def_iter.actuaciones.all()), key=lambda a: a.orden)
                for actuacion_def_iter in actuaciones_ordenadas:
                    effective_status = self._get_effective_action_status(actuacion_def_iter.id, historial_qs)
                    if effective_status == 'pendiente':
                        victima_proceso_instance.etapa_definicion_actual = etapa_def_iter
                        victima_proceso_instance.sub_etapa_definicion_actual = sub_etapa_def_iter
                        victima_proceso_instance.actuacion_definicion_siguiente = actuacion_def_iter
                        victima_proceso_instance.estado_general = 'en_progreso'
                        victima_proceso_instance.save()
                        return
        
        for etapa_def_iter in etapas_ordenadas:
            sub_etapas_ordenadas = sorted(list(etapa_def_iter.sub_etapas.all()), key=lambda se: se.orden)
            for sub_etapa_def_iter in sub_etapas_ordenadas:
                actuaciones_ordenadas = sorted(list(sub_etapa_def_iter.actuaciones.all()), key=lambda a: a.orden)
                for actuacion_def_iter in actuaciones_ordenadas:
                    effective_status = self._get_effective_action_status(actuacion_def_iter.id, historial_qs)
                    if effective_status == 'en_espera':
                        victima_proceso_instance.etapa_definicion_actual = etapa_def_iter
                        victima_proceso_instance.sub_etapa_definicion_actual = sub_etapa_def_iter
                        victima_proceso_instance.actuacion_definicion_siguiente = actuacion_def_iter
                        victima_proceso_instance.estado_general = 'en_progreso'
                        victima_proceso_instance.save()
                        return
        
        for etapa_def_iter in etapas_ordenadas:
            sub_etapas_ordenadas = sorted(list(etapa_def_iter.sub_etapas.all()), key=lambda se: se.orden)
            for sub_etapa_def_iter in sub_etapas_ordenadas:
                actuaciones_ordenadas = sorted(list(sub_etapa_def_iter.actuaciones.all()), key=lambda a: a.orden)
                for actuacion_def_iter in actuaciones_ordenadas:
                    effective_status = self._get_effective_action_status(actuacion_def_iter.id, historial_qs)
                    if effective_status == 'omitida_temporalmente':
                        victima_proceso_instance.etapa_definicion_actual = etapa_def_iter
                        victima_proceso_instance.sub_etapa_definicion_actual = sub_etapa_def_iter
                        victima_proceso_instance.actuacion_definicion_siguiente = actuacion_def_iter
                        victima_proceso_instance.estado_general = 'en_progreso'
                        victima_proceso_instance.save()
                        return
        
        victima_proceso_instance.estado_general = 'terminado'
        last_etapa = None
        if etapas_ordenadas:
            last_etapa = etapas_ordenadas[-1]
            victima_proceso_instance.etapa_definicion_actual = last_etapa
            last_subetapa = None
            sub_etapas_last_etapa = sorted(list(last_etapa.sub_etapas.all()), key=lambda se: se.orden)
            if sub_etapas_last_etapa:
                last_subetapa = sub_etapas_last_etapa[-1]
                victima_proceso_instance.sub_etapa_definicion_actual = last_subetapa
                actuaciones_last_subetapa = sorted(list(last_subetapa.actuaciones.all()), key=lambda a: a.orden)
                if actuaciones_last_subetapa:
                    victima_proceso_instance.actuacion_definicion_siguiente = actuaciones_last_subetapa[-1]
                else:
                    victima_proceso_instance.actuacion_definicion_siguiente = None
            else:
                victima_proceso_instance.sub_etapa_definicion_actual = None
                victima_proceso_instance.actuacion_definicion_siguiente = None
        else:
            victima_proceso_instance.etapa_definicion_actual = None
            victima_proceso_instance.sub_etapa_definicion_actual = None
            victima_proceso_instance.actuacion_definicion_siguiente = None
        victima_proceso_instance.save()

    @action(detail=True, methods=['post'], url_path='iniciar-proceso')
    @transaction.atomic
    def iniciar_proceso(self, request, pk=None):
        victima_proceso = self.get_object()
        proceso_definicion_id = request.data.get('proceso_definicion_id')
        
        if not proceso_definicion_id:
            return Response({"error": "proceso_definicion_id es requerido."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            proceso_def = ProcesoDefinicion.objects.get(id=proceso_definicion_id)
        except ProcesoDefinicion.DoesNotExist:
            return Response({"error": "ProcesoDefinicion no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if victima_proceso.estado_general != 'no_iniciado':
            if victima_proceso.proceso_definicion_actual == proceso_def :
                self._calculate_next_victim_state(victima_proceso)
                serializer = self.get_serializer(victima_proceso)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                 return Response({"error": "La víctima ya tiene un proceso diferente en curso."}, status=status.HTTP_400_BAD_REQUEST)


        victima_proceso.proceso_definicion_actual = proceso_def
        victima_proceso.etapa_definicion_actual = None
        victima_proceso.sub_etapa_definicion_actual = None
        victima_proceso.actuacion_definicion_siguiente = None
        victima_proceso.estado_general = 'en_progreso'
        
        self._calculate_next_victim_state(victima_proceso)
        
        serializer = self.get_serializer(victima_proceso)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='registrar-actuacion')
    @transaction.atomic
    def registrar_actuacion(self, request, pk=None):
        victima_proceso = self.get_object()

        if victima_proceso.estado_general == 'terminado':
            return Response({"error": "El proceso para esta víctima ya ha terminado."}, status=status.HTTP_400_BAD_REQUEST)
        if victima_proceso.estado_general == 'no_iniciado' or not victima_proceso.proceso_definicion_actual:
            return Response({"error": "El proceso debe ser iniciado antes de registrar actuaciones."}, status=status.HTTP_400_BAD_REQUEST)

        request_data = request.data.copy()
        request_data['victima_proceso'] = victima_proceso.id

        serializer = HistorialActuacionSlr(data=request_data, context={'request': request, 'view': self})
        serializer.is_valid(raise_exception=True)
        
        actuacion_def = serializer.validated_data['actuacion_definicion']
        
        if actuacion_def.sub_etapa_definicion.etapa_definicion.proceso_definicion != victima_proceso.proceso_definicion_actual:
            return Response(
                {"error": "La actuación no pertenece al proceso actual de la víctima."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document_file = serializer.validated_data.get('documento')
        original_doc_name = document_file.name if document_file else None

        login_user_instance = None
        if request.user.is_authenticated:
            try:
                UserModel = get_user_model()
                if isinstance(request.user, UserModel):
                    login_user_instance = request.user
            except Exception:
                pass


        historial_instance = serializer.save(
            victima_proceso=victima_proceso,
            creado_por=login_user_instance, 
            documento_nombre_original=original_doc_name
        )
        
        if actuacion_def.terminaProceso and historial_instance.status_actuacion in ['completada', 'omitida_permanentemente']:
            victima_proceso.estado_general = 'terminado'
            victima_proceso.etapa_definicion_actual = actuacion_def.sub_etapa_definicion.etapa_definicion
            victima_proceso.sub_etapa_definicion_actual = actuacion_def.sub_etapa_definicion
            victima_proceso.actuacion_definicion_siguiente = actuacion_def
            victima_proceso.save()
        else:
            self._calculate_next_victim_state(victima_proceso)
            
        return Response(HistorialActuacionSlr(historial_instance, context={'request': request, 'view': self}).data, status=status.HTTP_201_CREATED)

class HistorialActuacionVS(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet):
    queryset = HistorialActuacion.objects.all().select_related(
        'victima_proceso__victima',
        'actuacion_definicion__sub_etapa_definicion__etapa_definicion',
        'creado_por'
    )
    serializer_class = HistorialActuacionSlr
    permission_classes = [permissions.IsAuthenticated]

    def _get_calculate_next_state_func_victim(self):
        temp_vp_vs = VictimaProcesoVS() 
        return temp_vp_vs._calculate_next_victim_state

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        original_doc_name = instance.documento_nombre_original 
        if 'documento' in serializer.validated_data:
            document_file = serializer.validated_data.get('documento')
            if document_file:
                original_doc_name = document_file.name
            else: 
                original_doc_name = None
        
        historial_instance = serializer.save(documento_nombre_original=original_doc_name)
        
        victima_proceso = historial_instance.victima_proceso
        actuacion_def = historial_instance.actuacion_definicion
        if actuacion_def.terminaProceso and historial_instance.status_actuacion in ['completada', 'omitida_permanentemente']:
            victima_proceso.estado_general = 'terminado'
            victima_proceso.etapa_definicion_actual = actuacion_def.sub_etapa_definicion.etapa_definicion
            victima_proceso.sub_etapa_definicion_actual = actuacion_def.sub_etapa_definicion
            victima_proceso.actuacion_definicion_siguiente = actuacion_def
            victima_proceso.save()
        else:
            calculate_func = self._get_calculate_next_state_func_victim()
            calculate_func(victima_proceso)
            
        return Response(serializer.data)

    @transaction.atomic
    def perform_destroy(self, instance):
        victima_proceso = instance.victima_proceso
        instance.delete()
        calculate_func = self._get_calculate_next_state_func_victim()
        calculate_func(victima_proceso)


class SiniestroHistorialActuacionVS(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet):
    queryset = SiniestroHistorialActuacion.objects.all().select_related(
        'siniestro_proceso__siniestro',
        'actuacion_definicion__sub_etapa_definicion__etapa_definicion',
        'creado_por'
    )
    serializer_class = SiniestroHistorialActuacionSlr
    permission_classes = [permissions.IsAuthenticated]

    def _get_calculate_next_state_func_siniestro(self):
        temp_s_vs = SiniestroVS()
        return temp_s_vs._calculate_next_siniestro_state

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        original_doc_name = instance.documento_nombre_original 
        if 'documento' in serializer.validated_data:
            document_file = serializer.validated_data.get('documento')
            if document_file:
                original_doc_name = document_file.name
            else: 
                original_doc_name = None
        
        historial_instance = serializer.save(documento_nombre_original=original_doc_name)
        
        siniestro_proceso = historial_instance.siniestro_proceso
        actuacion_def = historial_instance.actuacion_definicion
        if actuacion_def.terminaProceso and historial_instance.status_actuacion in ['completada', 'omitida_permanentemente']:
            siniestro_proceso.estado_general = 'terminado'
            siniestro_proceso.etapa_definicion_actual = actuacion_def.sub_etapa_definicion.etapa_definicion
            siniestro_proceso.sub_etapa_definicion_actual = actuacion_def.sub_etapa_definicion
            siniestro_proceso.actuacion_definicion_siguiente = actuacion_def
            siniestro_proceso.save()
        else:
            calculate_func = self._get_calculate_next_state_func_siniestro()
            calculate_func(siniestro_proceso)
            
        return Response(serializer.data)

    @transaction.atomic
    def perform_destroy(self, instance):
        siniestro_proceso = instance.siniestro_proceso
        instance.delete()
        calculate_func = self._get_calculate_next_state_func_siniestro()
        calculate_func(siniestro_proceso)