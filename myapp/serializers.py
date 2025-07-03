from .models import TipoDocumento, Empresas, Roles, EventoDocumento, Colaboradores, Login, Acciones, Modulos, Permisos, Vehiculos, Event, EventParticipant, EventGuest, EventAction, EventEvidence, Headquarters, Notification, Agenda, Evaluation, TrainingsCategories, Pregunta, RespuestaUsuario, ResultadoParte, CalificacionTotal, InductionDoc, Test, Section2, Question, TestDrivers, TestDriversSession, WrittenTest, WrittenTestSession, Siniestro, SiniestroMedia, Ipat, Department, EnteAtencion, Servicio, Propietario, Tenedor, Soat, RevisionTecnomecanica, TarjetaOperacion, LicenciaTransito, Poliza, NovedadVehiculo, FichaTecnica, ConductorAsociado, ProcedimientoJuridico, EventoLegalFile, EventoLegal, Mantenimiento, Facturacion, Marca, TipoLinea, ClaseVehiculo, Carroceria, Combustible, TipoOperacion, Ciudad, NivelServicio, Categoria, Color, ProcesoDefinicion, EtapaDefinicion, SubEtapaDefinicion, ActuacionDefinicion, Victima, VictimaProceso, HistorialActuacion
from rest_framework import serializers
import json

class TipoDocumentoSlr(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = '__all__'

class DepartmentsSlr(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = serializers.ALL_FIELDS

class EmpresasSlr(serializers.ModelSerializer):
    class Meta:
        model = Empresas
        fields = '__all__'

class RolesSlr(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = serializers.ALL_FIELDS

class ColaboradoresSlr(serializers.ModelSerializer):
    class Meta:
        model = Colaboradores
        fields = '__all__'

class MarcaSlr(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ['id', 'nombre']

class TipoLineaSlr(serializers.ModelSerializer):
    class Meta:
        model = TipoLinea
        fields = ['id', 'nombre']

class ClaseVehiculoSlr(serializers.ModelSerializer):
    class Meta:
        model = ClaseVehiculo
        fields = ['id', 'nombre']

class CarroceriaSlr(serializers.ModelSerializer):
    class Meta:
        model = Carroceria
        fields = ['id', 'nombre']

class CombustibleSlr(serializers.ModelSerializer):
    class Meta:
        model = Combustible
        fields = ['id', 'nombre']

class TipoOperacionSlr(serializers.ModelSerializer):
    class Meta:
        model = TipoOperacion
        fields = ['id', 'nombre']

class CiudadSlr(serializers.ModelSerializer):
    class Meta:
        model = Ciudad
        fields = ['id', 'nombre']

class NivelServicioSlr(serializers.ModelSerializer):
    class Meta:
        model = NivelServicio
        fields = ['id', 'nombre']

class CategoriaSlr(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre']

class ColorSlr(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'nombre']


class ServicioSlr(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = '__all__'
        read_only_fields = ['id_servicio', 'vehiculo']

from .models import Contrato

class ContratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contrato
        fields = '__all__'

class PropietarioSlr(serializers.ModelSerializer):
    porcentaje = serializers.SerializerMethodField()
    identificacion = serializers.CharField(validators=[]) 

    class Meta:
        model = Propietario
        fields = [
            'tipoDocumento',
            'identificacion',
            'direccion',
            'ciudad',
            'departamento',
            'nombres',
            'apellidos',
            'fechaIngreso',
            'telefono',
            'correo',
            'porcentaje',
        ]
        extra_kwargs = {
            'identificacion': {'validators': []},
        }

    def get_porcentaje(self, obj):
        placa_vehiculo_actual = self.context.get('placa_vehiculo_actual')
        
        if placa_vehiculo_actual:
            vp = obj.vehiculos_relations.filter(vehiculo__placa=placa_vehiculo_actual).first()
            if vp:
                return vp.porcentaje
        
        elif self.context.get('request'):
            request = self.context.get('request')
            pass

        return None

class TenedorSlr(serializers.ModelSerializer):
    porcentaje = serializers.SerializerMethodField()
    identificacion = serializers.CharField(validators=[])

    class Meta:
        model = Tenedor
        fields = [
            'id_tenedor',
            'tipoDocumento',
            'identificacion',
            'nombres',
            'apellidos',
            'fechaIngreso',
            'telefono',
            'correo',
            'porcentaje',
        ]
        extra_kwargs = {
            'identificacion': {'validators': []},
        }

    def get_porcentaje(self, obj):
        request = self.context.get('request', None)
        if request:
            placa = request.query_params.get('vehiculos_relations__vehiculo')
            if placa:
                vt = obj.vehiculos_relations.filter(vehiculo__placa=placa).first()
                if vt:
                    return vt.porcentaje
        return None
    
class VehiculosSlr(serializers.ModelSerializer):
    placa = serializers.CharField(max_length=7)
    facturaCompra = serializers.FileField(required=False, allow_null=True)
    declaracionImportacion = serializers.FileField(required=False, allow_null=True)
    caracteristicasMecanicas = serializers.FileField(required=False, allow_null=True)
    marca = serializers.PrimaryKeyRelatedField(queryset=Marca.objects.all())
    tipoLinea = serializers.PrimaryKeyRelatedField(queryset=TipoLinea.objects.all(), required=False)
    clase = serializers.PrimaryKeyRelatedField(queryset=ClaseVehiculo.objects.all())
    carroceria = serializers.PrimaryKeyRelatedField(queryset=Carroceria.objects.all())
    combustible = serializers.PrimaryKeyRelatedField(queryset=Combustible.objects.all())
    ciudadBase = serializers.PrimaryKeyRelatedField(queryset=Ciudad.objects.all())
    color = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    numero_interno = serializers.SerializerMethodField()
    class Meta:
        model = Vehiculos
        fields = [
            'placa', 'empresa', 'marca', 'tipoLinea', 'paxLt', 'paxRl',
            'clase', 'carroceria', 'numeroMotor', 'tipoMotor', 'combustible',
            'chasis', 'serie', 'vin', 'ciudadBase', 'modelo', 'numeroEjes',
            'cilindraje', 'licenciaTransito', 'estado', 'color', 'unionTemporal',
            'facturaCompra', 'declaracionImportacion', 'caracteristicasMecanicas',
            'numero_interno'
        ]
    def get_numero_interno(self, obj: Vehiculos) -> int | None:
        try:
            if obj.servicio:
                return obj.servicio.numeroInterno
        except Servicio.DoesNotExist:
            return None
        except AttributeError:
            return None
        return None


class EventoDocumentoSlr(serializers.ModelSerializer):
    class Meta:
        model = EventoDocumento
        fields = '__all__'

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
from .models import (
    Vehiculos, Soat, RevisionTecnomecanica, TarjetaOperacion, LicenciaTransito,
    PolizaContractual, PolizaExtracontractual, PolizaTodoRiesgo,
    Aseguradora, TipoDocumentoVehiculo, ReporteVencimientosDiario
)
class ReporteVencimientosDiarioSlr(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre_empresa', read_only=True)
    class Meta:
        model = ReporteVencimientosDiario
        fields = ['id', 'empresa', 'empresa_nombre', 'fecha_reporte', 'datos_reporte', 'creado_en']
        read_only_fields = ['id', 'creado_en', 'empresa_nombre']

class AseguradoraSlr(serializers.ModelSerializer):
    class Meta:
        model = Aseguradora
        fields = ['id', 'nombre', 'nit']

class TipoDocumentoVehiculoSlr(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumentoVehiculo
        fields = ['id', 'nombre']       
class SoatSlr(serializers.ModelSerializer):
    class Meta:
        model = Soat
        fields = '__all__'

class RevisionTecnomecanicaSlr(serializers.ModelSerializer):
    class Meta:
        model = RevisionTecnomecanica
        fields = '__all__'

class TarjetaOperacionSlr(serializers.ModelSerializer):
    class Meta:
        model = TarjetaOperacion
        fields = '__all__'

class LicenciaTransitoSlr(serializers.ModelSerializer):
    class Meta:
        model = LicenciaTransito
        fields = '__all__'


from rest_framework import serializers
from .models import (
    Vehiculos, Soat, RevisionTecnomecanica, TarjetaOperacion, LicenciaTransito,
    PolizaContractual, PolizaExtracontractual, PolizaTodoRiesgo,
    Aseguradora, TipoDocumentoVehiculo
)

class AseguradoraSlr(serializers.ModelSerializer):
    class Meta:
        model = Aseguradora
        fields = ['id', 'nombre', 'nit']

class TipoDocumentoVehiculoSlr(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumentoVehiculo
        fields = ['id', 'nombre']

class SoatSlr(serializers.ModelSerializer):
    aseguradora_details = AseguradoraSlr(source='aseguradora', read_only=True)
    tipo_documento_vehiculo_details = TipoDocumentoVehiculoSlr(source='tipo_documento_vehiculo', read_only=True)

    class Meta:
        model = Soat
        fields = '__all__'
        read_only_fields = ('id', 'vehiculo')

class RevisionTecnomecanicaSlr(serializers.ModelSerializer):
    tipo_documento_vehiculo_details = TipoDocumentoVehiculoSlr(source='tipo_documento_vehiculo', read_only=True)
    class Meta:
        model = RevisionTecnomecanica
        fields = '__all__'
        read_only_fields = ('id', 'vehiculo')

class TarjetaOperacionSlr(serializers.ModelSerializer):
    tipo_documento_vehiculo_details = TipoDocumentoVehiculoSlr(source='tipo_documento_vehiculo', read_only=True)
    aseguradora_details = AseguradoraSlr(source='aseguradora', read_only=True)
    class Meta:
        model = TarjetaOperacion
        fields = '__all__'
        read_only_fields = ('id', 'vehiculo')

class LicenciaTransitoSlr(serializers.ModelSerializer):
    placa = serializers.CharField(write_only=True)

    class Meta:
        model = LicenciaTransito
        fields = [
            'id',
            'vehiculo',
            'placa',
            'numero_documento',
            'fecha_expedicion',
            'fecha_matricula',
            'soporte',
            'estado',
        ]
        read_only_fields = ('id', 'vehiculo', 'soporte')

    def create(self, validated_data):
        validated_data.pop('placa', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('placa', None)
        return super().update(instance, validated_data)


class PolizaContractualSlr(serializers.ModelSerializer):
    aseguradora_details = AseguradoraSlr(source='aseguradora', read_only=True)
    tipo_documento_vehiculo_details = TipoDocumentoVehiculoSlr(source='tipo_documento_vehiculo', read_only=True)

    class Meta:
        model = PolizaContractual
        fields = '__all__'
        read_only_fields = ('id', 'vehiculo')

class PolizaExtracontractualSlr(serializers.ModelSerializer):
    aseguradora_details = AseguradoraSlr(source='aseguradora', read_only=True)
    tipo_documento_vehiculo_details = TipoDocumentoVehiculoSlr(source='tipo_documento_vehiculo', read_only=True)

    class Meta:
        model = PolizaExtracontractual
        fields = '__all__'
        read_only_fields = ('id', 'vehiculo')

class PolizaTodoRiesgoSlr(serializers.ModelSerializer):
    aseguradora_details = AseguradoraSlr(source='aseguradora', read_only=True)
    tipo_documento_vehiculo_details = TipoDocumentoVehiculoSlr(source='tipo_documento_vehiculo', read_only=True)

    class Meta:
        model = PolizaTodoRiesgo
        fields = '__all__'
        read_only_fields = ('id', 'vehiculo')
        
class PolizaSlr(serializers.ModelSerializer):
    class Meta:
        model = Poliza
        fields = '__all__'

class NovedadVehiculoSlr(serializers.ModelSerializer):
    class Meta:
        model = NovedadVehiculo
        fields = '__all__'

class FichaTecnicaSlr(serializers.ModelSerializer):
    class Meta:
        model = FichaTecnica
        fields = '__all__'

class ConductorAsociadoSlr(serializers.ModelSerializer):
    class Meta:
        model = ConductorAsociado
        fields = '__all__'

class ProcedimientoJuridicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedimientoJuridico
        fields = '__all__'

class EventoLegalFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoLegalFile
        fields = ['id', 'archivo', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']

class EventoLegalSerializer(serializers.ModelSerializer):
    archivos = EventoLegalFileSerializer(many=True, read_only=True)

    class Meta:
        model = EventoLegal
        fields = [
            'id',
            'vehiculo',
            'tipo_evento',
            'fecha_creacion',
            'archivos',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'archivos']


class MantenimientoSlr(serializers.ModelSerializer):
    class Meta:
        model = Mantenimiento
        fields = '__all__'

class FacturacionSlr(serializers.ModelSerializer):
    class Meta:
        model = Facturacion
        fields = '__all__'

class LoginSlr(serializers.ModelSerializer):
    class Meta:
        model = Login
        fields = serializers.ALL_FIELDS

class AccionesSlr(serializers.ModelSerializer):
    class Meta:
        model = Acciones
        fields = serializers.ALL_FIELDS
class ModulosSlr(serializers.ModelSerializer):
    class Meta:
        model = Modulos
        fields = serializers.ALL_FIELDS

class PermisosSlr(serializers.ModelSerializer):
    class Meta:
        model = Permisos
        fields = serializers.ALL_FIELDS

class AgendaSlr(serializers.ModelSerializer):
    colaborador = ColaboradoresSlr(source='agenda_colaborador', read_only=True)
    
    class Meta:
        model = Agenda
        fields = '__all__'

class HeadquartersSlr(serializers.ModelSerializer):
    class Meta:
        model = Headquarters
        fields = '__all__'
class NotificationSlr(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
class EvaluationSlr(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = ['id_evaluation', 'eva_title', 'eva_description', 'eva_questions']

class EventParticipantSerializer(serializers.ModelSerializer):
    colaborador = serializers.PrimaryKeyRelatedField(queryset=Colaboradores.objects.all())
    class Meta:
        model = EventParticipant
        fields = ['colaborador', 'rating', 'fecha']

class EventGuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventGuest
        fields = ['guest_name', 'guest_company', 'guest_position', 'guest_signature']

class EventActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventAction
        fields = ['action_name', 'action_deadline', 'action_responsible']

class EventEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventEvidence
        fields = ['evidence_file', 'evidence_type']

class EventSerializer(serializers.ModelSerializer):
    participants = EventParticipantSerializer(many=True, required=False)
    guests = EventGuestSerializer(many=True, required=False)
    actions = EventActionSerializer(many=True, required=False)
    evidences = EventEvidenceSerializer(many=True, read_only=True)
    event_required_roles = serializers.PrimaryKeyRelatedField(
        queryset=Roles.objects.all(), many=True, required=False
    )
    event_required_colaboradores = serializers.PrimaryKeyRelatedField(
        queryset=Colaboradores.objects.all(), many=True, required=False
    )
    event_training_category = serializers.PrimaryKeyRelatedField(
        queryset=TrainingsCategories.objects.all(), allow_null=True, required=False
    )

    event_place = serializers.PrimaryKeyRelatedField(
        queryset=Headquarters.objects.all()
    )
    
    event_place_details = HeadquartersSlr(source='event_place', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'event_record_number', 'event_date', 'event_start_date', 'event_end_date', 
            'event_place', 'event_place_details', 'event_aim', 'event_issue', 'event_agenda', 
            'event_development', 'event_responsible', 'event_evaluation', 
            'event_required_roles', 'event_required_colaboradores', 'event_training_category',
            'participants', 'guests', 'actions', 'evidences', 'event_type', 'is_virtual'
        ]

    def update(self, instance, validated_data):
        participants_data = validated_data.pop('participants', [])
        guests_data = validated_data.pop('guests', [])
        actions_data = validated_data.pop('actions', [])
        evidences_data = validated_data.pop('evidences', [])
        event_required_roles_data = validated_data.pop('event_required_roles', [])
        event_required_colaboradores_data = validated_data.pop('event_required_colaboradores', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if event_required_roles_data:
            instance.event_required_roles.set(event_required_roles_data)

        if event_required_colaboradores_data:
            instance.event_required_colaboradores.set(event_required_colaboradores_data)

        instance.participants.all().delete()
        for participant_data in participants_data:
            EventParticipant.objects.create(event=instance, **participant_data)

        instance.guests.all().delete()
        for guest_data in guests_data:
            EventGuest.objects.create(event=instance, **guest_data)

        instance.actions.all().delete()
        for action_data in actions_data:
            EventAction.objects.create(event=instance, **action_data)

        instance.evidences.all().delete()
        for evidence_data in evidences_data:
            EventEvidence.objects.create(event=instance, **evidence_data)

        if instance.event_responsible:
            Agenda.objects.filter(
                agenda_colaborador_id=instance.event_responsible,
                agenda_title=f"Evento: {instance.event_aim}"
            ).delete()
            Agenda.objects.create(
                agenda_colaborador_id=instance.event_responsible,
                agenda_title=f"Evento: {instance.event_aim}",
                agenda_start_date=instance.event_start_date.date(),
                agenda_end_date=instance.event_end_date.date(),
                agenda_start_time=instance.event_start_date.time(),
                agenda_end_time=instance.event_end_date.time(),
                agenda_color="#00FF00"
            )

        return instance

    def create(self, validated_data):
        participants_data = validated_data.pop('participants', [])
        guests_data = validated_data.pop('guests', [])
        actions_data = validated_data.pop('actions', [])
        evidences_data = validated_data.pop('evidences', [])
        event_required_roles_data = validated_data.pop('event_required_roles', [])
        event_required_colaboradores_data = validated_data.pop('event_required_colaboradores', [])

        event = Event.objects.create(**validated_data)
        event.event_required_roles.set(event_required_roles_data)
        event.event_required_colaboradores.set(event_required_colaboradores_data)

        for participant_data in participants_data:
            EventParticipant.objects.create(event=event, **participant_data)

        for guest_data in guests_data:
            EventGuest.objects.create(event=event, **guest_data)

        for action_data in actions_data:
            EventAction.objects.create(event=event, **action_data)

        for evidence_data in evidences_data:
            EventEvidence.objects.create(event=event, **evidence_data)

        if event.event_responsible:
            Agenda.objects.create(
                agenda_colaborador_id=event.event_responsible,
                agenda_title=f"Evento: {event.event_aim}",
                agenda_start_date=event.event_start_date.date(),
                agenda_end_date=event.event_end_date.date(),
                agenda_start_time=event.event_start_date.time(),
                agenda_end_time=event.event_end_date.time(),
                agenda_color="#00FF00"
            )

        return event

class TrainingsCategoriesSlr(serializers.ModelSerializer):
    class Meta:
        model = TrainingsCategories
        fields = '__all__'

class PreguntaSlr(serializers.ModelSerializer):
    class Meta:
        model = Pregunta
        fields = ['id', 'texto', 'opciones', 'imagen', 'video']

class RespuestaUsuarioSlr(serializers.ModelSerializer):
    class Meta:
        model = RespuestaUsuario
        fields = ['pregunta', 'respuesta_seleccionada']

class ParteCalificacionSlr(serializers.ModelSerializer):
    class Meta:
        model = ResultadoParte
        fields = ['parte', 'calificacion']

class CalificacionTotalSlr(serializers.ModelSerializer):
    class Meta:
        model = CalificacionTotal
        fields = ['usuario', 'promedio']

class InductionDocSlr(serializers.ModelSerializer):
    cedula_empleado = serializers.PrimaryKeyRelatedField(queryset=Colaboradores.objects.all())
    responsable_induccion = serializers.PrimaryKeyRelatedField(
        queryset=Colaboradores.objects.all(), allow_null=True
    )
    lugar = serializers.PrimaryKeyRelatedField(queryset=Headquarters.objects.all(), allow_null=True)

    nombre_empleado = serializers.SerializerMethodField()
    cargo = serializers.SerializerMethodField()
    firma_capacitador = serializers.SerializerMethodField()
    firma_empleado_display = serializers.SerializerMethodField()

    class Meta:
        model = InductionDoc
        fields = [
            'id',
            'cedula_empleado',
            'nombre_empleado',
            'responsable_induccion',
            'firma_capacitador',
            'cargo',
            'firma_empleado',
            'vfanswers',
            'vfanswers2',
            'vfanswers3',
            'abcanswers',
            'abcanswers2',
            'abcanswers3',
            'lugar',
            'fecha',
            'horafin_social',
            'horafin_pesv',
            'observaciones_vi',
            'observaciones_iv',
            'cumplimiento_objetivos',
            'claridad_conceptos',
            'desarrollo_personal',
            'trabajo_actual',
            'conocimiento_tema',
            'habilidades_comunicacion',
            'capacidad_orientar',
            'transmision_ideas',
            'manejo_tiempo',
            'generacion_empatia',
            'puntualidad',
            'material_usado',
            'recursos_empleados',
            'instalaciones',
            'aspectos_logisticos',
            'sino1',
            'sino2',
            'sino3',
            'sino4',
            'sino5',
            'sino6',
            'sino7',
            'sino8',
            'sino9',
            'sino10',
            'sino11',
            'sino12',
            'sino13',
            'sino14',
            'sino15',
            'sino16',
            'sino17',
            'sino18',
            'sino19',
            'firma_empleado',
            'firma_capacitador',
            'huella_soci2',
            'nombre_autorizacion',
            'firma_autorizacion',
            'ciudad_fecha_autorizacion',
            'firma_empleado_display'
        ]
        read_only_fields = [
            'nombre_empleado', 'cargo', 'firma_capacitador',
            'fecha', 'firma_empleado_display'
        ]

    def get_nombre_empleado(self, obj):
        return f"{obj.cedula_empleado.nombres} {obj.cedula_empleado.apellidos}" if obj.cedula_empleado else None

    def get_cargo(self, obj):
        return obj.cedula_empleado.rol.detalle_rol if obj.cedula_empleado and obj.cedula_empleado.rol else None

    def get_firma_capacitador(self, obj):
        return obj.responsable_induccion.signature if obj.responsable_induccion else None

    def get_firma_empleado_display(self, obj):
        return obj.firma_empleado
class QuestionSlr(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question', 'type', 'description', 'image_src', 'options', 'correct_answer', 'correct_answers', 'images']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if isinstance(representation['options'], str):
            representation['options'] = json.loads(representation['options'])
        if isinstance(representation['correct_answers'], str):
            representation['correct_answers'] = json.loads(representation['correct_answers'])
        return representation

class Section2Slr(serializers.ModelSerializer):
    questions = QuestionSlr(many=True)

    class Meta:
        model = Section2
        fields = ['id_section', 'title', 'description', 'questions']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if 'questions' in representation:
            representation['questions'] = sorted(representation['questions'], key=lambda x: x['id'])
        return representation

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        section = Section2.objects.create(**validated_data)
        for question_data in questions_data:
            Question.objects.create(section=section, **question_data)
        return section

class TestSlr(serializers.ModelSerializer):
    sections = Section2Slr(many=True)

    class Meta:
        model = Test
        fields = ['id_test', 'title', 'description', 'created_at', 'sections']

    def create(self, validated_data):
        sections_data = validated_data.pop('sections')
        test = Test.objects.create(**validated_data)
        for section_data in sections_data:
            questions_data = section_data.pop('questions')
            section = Section2.objects.create(test_id=test, **section_data)
            for question_data in questions_data:
                Question.objects.create(section=section, **question_data)
        return test
    
class TestDriversDetailSlr(serializers.ModelSerializer):
    colaborador_evaluador = ColaboradoresSlr(read_only=True)
    empresa_solicitante = EmpresasSlr(read_only=True)
    lugar = HeadquartersSlr(read_only=True)

    class Meta:
        model = TestDrivers
        fields = [
            'id_test_driver',
            'colaborador_evaluador',
            'name_driver',
            'dni_driver',
            'empresa_solicitante',
            'vehiculo',
            'lugar',
            'fecha_solicitud',
            'estado',
            'resultados',
            'observaciones',
            'recomendacion',
            'calificaciones',
            'license_category',
            'experience_time',
            'signature_driver',
        ]

class TestDriversSlr(serializers.ModelSerializer):
    empresa_solicitante = serializers.PrimaryKeyRelatedField(queryset=Empresas.objects.all())
    vehiculo = serializers.PrimaryKeyRelatedField(queryset=Vehiculos.objects.all())
    lugar = serializers.PrimaryKeyRelatedField(queryset=Headquarters.objects.all(), required=False)
    colaborador_evaluador = serializers.PrimaryKeyRelatedField(queryset=Colaboradores.objects.all(), required=False)
    calificaciones = serializers.JSONField(required=False)

    class Meta:
        model = TestDrivers
        fields = [
            'id_test_driver',
            'colaborador_evaluador',
            'name_driver',
            'dni_driver',
            'empresa_solicitante',
            'vehiculo',
            'lugar',
            'fecha_solicitud',
            'estado',
            'resultados',
            'observaciones',
            'recomendacion',
            'calificaciones',
            'license_category',
            'experience_time',
            'signature_driver',
        ]

class TestDriversSessionSlr(serializers.ModelSerializer):
    session_details = serializers.SerializerMethodField()

    class Meta:
        model = TestDriversSession
        fields = ['id', 'evaluator', 'evaluation_request', 'data', 'last_updated', 'is_completed', 'session_details']

    def get_session_details(self, obj):
        return obj.fetch_session_details()
    
class WrittenTestSlr(serializers.ModelSerializer):
    class Meta:
        model = WrittenTest
        fields = '__all__'

class WrittenTestSessionSlr(serializers.ModelSerializer):
    class Meta:
        model = WrittenTestSession
        fields = ['id', 'evaluation_request', 'user_responses', 'current_section', 'score']

from rest_framework import serializers
from .models import (
    Siniestro,
    SiniestroMedia,
    SiniestroLog,
    EnteAtencion,
    Colaboradores,
    Vehiculos,
    Empresas,
    Tercero,
    ActaConciliacion,
    Ipat,
    SiniestroHistorialActuacion,
    SiniestroProceso
)

class EnteAtencionSlr(serializers.ModelSerializer):
    class Meta:
        model = EnteAtencion
        fields = '__all__'

class SiniestroMediaSlr(serializers.ModelSerializer):
    class Meta:
        model = SiniestroMedia
        fields = '__all__'

class SiniestroLogSlr(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    media = SiniestroMediaSlr(read_only=True)

    class Meta:
        model = SiniestroLog
        fields = ['id', 'user', 'action', 'timestamp', 'media']

    def get_user(self, obj):
        if obj.user:
            return {
                "id": obj.user.num_documento,
                "nombre": f"{obj.user.nombres} {obj.user.apellidos}"
            }
        return None

class TerceroSlr(serializers.ModelSerializer):
    class Meta:
        model = Tercero
        fields = '__all__'
        
class ActaConciliacionSlr(serializers.ModelSerializer):
    class Meta:
        model = ActaConciliacion
        fields = '__all__'

class IpatSlr(serializers.ModelSerializer):
    class Meta:
        model = Ipat
        fields = '__all__'

class EtapaDefinicionForPathSlr(serializers.ModelSerializer):
    class Meta:
        model = EtapaDefinicion
        fields = ['id', 'nombre', 'codigoEtapa']

class SubEtapaDefinicionForPathSlr(serializers.ModelSerializer):
    etapa_definicion = EtapaDefinicionForPathSlr(read_only=True)
    class Meta:
        model = SubEtapaDefinicion
        fields = ['id', 'nombre', 'codigoSubEtapa', 'etapa_definicion']

class ActuacionDefinicionForHistorialSlr(serializers.ModelSerializer):
    sub_etapa_definicion = SubEtapaDefinicionForPathSlr(read_only=True)
    class Meta:
        model = ActuacionDefinicion
        fields = ['id', 'nombre', 'descripcion', 'terminaProceso', 'estadoResultado', 'codigoActuacion', 'orden', 'sub_etapa_definicion']

class ActuacionDefinicionSlr(serializers.ModelSerializer):
    class Meta:
        model = ActuacionDefinicion
        fields = ['id', 'nombre', 'descripcion', 'terminaProceso', 'estadoResultado', 'codigoActuacion', 'orden']

class SubEtapaDefinicionSlr(serializers.ModelSerializer):
    actuaciones = ActuacionDefinicionSlr(many=True, read_only=True)
    etapa_definicion = EtapaDefinicionForPathSlr(read_only=True)
    class Meta:
        model = SubEtapaDefinicion
        fields = ['id', 'nombre', 'codigoSubEtapa', 'orden', 'actuaciones', 'etapa_definicion']

class EtapaDefinicionSlr(serializers.ModelSerializer):
    sub_etapas = SubEtapaDefinicionSlr(many=True, read_only=True)
    proceso_definicion = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = EtapaDefinicion
        fields = ['id', 'nombre', 'codigoEtapa', 'orden', 'sub_etapas', 'proceso_definicion']

class ProcesoDefinicionSlr(serializers.ModelSerializer):
    etapas = EtapaDefinicionSlr(many=True, read_only=True)
    class Meta:
        model = ProcesoDefinicion
        fields = ['id', 'nombre', 'codigoProceso', 'etapas']


class VictimaSlr(serializers.ModelSerializer):
    class Meta:
        model = Victima
        fields = ['id', 'siniestro', 'tipo', 'nombre', 'cedula', 'contacto', 'nombreContacto', 'parentesco', 'fecha_creacion']

class HistorialActuacionSlr(serializers.ModelSerializer):
    actuacion_definicion = ActuacionDefinicionForHistorialSlr(read_only=True)
    actuacion_definicion_id = serializers.PrimaryKeyRelatedField(
        queryset=ActuacionDefinicion.objects.all(), source='actuacion_definicion', write_only=True
    )
    documento_url = serializers.SerializerMethodField()
    creado_por_detalle = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HistorialActuacion
        fields = [
            'id', 'victima_proceso', 'actuacion_definicion', 'actuacion_definicion_id',
            'fecha_actuacion', 'fecha_vigencia', 'notas', 'documento',
            'documento_url',
            'documento_nombre_original', 'timestamp_registro', 'status_actuacion',
            'resuelve_omision_de', 'creado_por', 'creado_por_detalle'
        ]
        read_only_fields = ['timestamp_registro', 'creado_por', 'documento_nombre_original']

    def get_documento_url(self, obj):
        if obj.documento and hasattr(obj.documento, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.documento.url)
            return obj.documento.url
        return None

    def get_creado_por_detalle(self, obj):
        if obj.creado_por:
            try:
                colaborador = Colaboradores.objects.get(pk=obj.creado_por.documento_num_id)
                return f"{colaborador.nombres} {colaborador.apellidos}"
            except Colaboradores.DoesNotExist:
                if hasattr(obj.creado_por, 'get_username'):
                    return obj.creado_por.get_username()
                return str(obj.creado_por)
            except AttributeError:
                if hasattr(obj.creado_por, 'get_username'):
                    return obj.creado_por.get_username()
                return str(obj.creado_por)
        return None

class VictimaProcesoSlr(serializers.ModelSerializer):
    victima = VictimaSlr(read_only=True)
    victima_id = serializers.PrimaryKeyRelatedField(
        queryset=Victima.objects.all(), source='victima', write_only=True, allow_null=True
    )
    proceso_definicion_actual = ProcesoDefinicionSlr(read_only=True)
    proceso_definicion_actual_id = serializers.PrimaryKeyRelatedField(
        queryset=ProcesoDefinicion.objects.all(), source='proceso_definicion_actual', write_only=True, required=False, allow_null=True
    )
    etapa_definicion_actual = EtapaDefinicionSlr(read_only=True)
    sub_etapa_definicion_actual = SubEtapaDefinicionSlr(read_only=True)
    actuacion_definicion_siguiente = ActuacionDefinicionSlr(read_only=True)
    historial_actuaciones = HistorialActuacionSlr(many=True, read_only=True)

    class Meta:
        model = VictimaProceso
        fields = [
            'id', 'victima', 'victima_id', 'proceso_definicion_actual', 'proceso_definicion_actual_id',
            'etapa_definicion_actual', 'sub_etapa_definicion_actual',
            'actuacion_definicion_siguiente', 'estado_general', 'fecha_actualizacion',
            'historial_actuaciones'
        ]

class SiniestroHistorialActuacionSlr(serializers.ModelSerializer):
    actuacion_definicion = ActuacionDefinicionForHistorialSlr(read_only=True)
    actuacion_definicion_id = serializers.PrimaryKeyRelatedField(
        queryset=ActuacionDefinicion.objects.all(), source='actuacion_definicion', write_only=True
    )
    documento_url = serializers.SerializerMethodField()
    creado_por_detalle = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SiniestroHistorialActuacion
        fields = [
            'id', 'siniestro_proceso', 'actuacion_definicion', 'actuacion_definicion_id',
            'fecha_actuacion', 'fecha_vigencia', 'notas', 'documento',
            'documento_url',
            'documento_nombre_original', 'timestamp_registro', 'status_actuacion',
            'resuelve_omision_de', 'creado_por', 'creado_por_detalle'
        ]
        read_only_fields = ['timestamp_registro', 'creado_por', 'documento_nombre_original']

    def get_documento_url(self, obj):
        if obj.documento and hasattr(obj.documento, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.documento.url)
            return obj.documento.url
        return None

    def get_creado_por_detalle(self, obj):
        if obj.creado_por:
            try:
                colaborador = Colaboradores.objects.get(pk=obj.creado_por.documento_num_id)
                return f"{colaborador.nombres} {colaborador.apellidos}"
            except Colaboradores.DoesNotExist:
                if hasattr(obj.creado_por, 'get_username'):
                    return obj.creado_por.get_username()
                return str(obj.creado_por)
            except AttributeError:
                if hasattr(obj.creado_por, 'get_username'):
                    return obj.creado_por.get_username()
                return str(obj.creado_por)
        return None


class SiniestroProcesoSlr(serializers.ModelSerializer):
    siniestro_id = serializers.PrimaryKeyRelatedField(read_only=True)
    proceso_definicion_actual = ProcesoDefinicionSlr(read_only=True)
    proceso_definicion_actual_id = serializers.PrimaryKeyRelatedField(
        queryset=ProcesoDefinicion.objects.all(), source='proceso_definicion_actual', write_only=True, required=False, allow_null=True
    )
    etapa_definicion_actual = EtapaDefinicionSlr(read_only=True)
    sub_etapa_definicion_actual = SubEtapaDefinicionSlr(read_only=True)
    actuacion_definicion_siguiente = ActuacionDefinicionSlr(read_only=True)
    historial_actuaciones_siniestro = SiniestroHistorialActuacionSlr(many=True, read_only=True)

    class Meta:
        model = SiniestroProceso
        fields = [
            'id', 'siniestro_id', 'proceso_definicion_actual', 'proceso_definicion_actual_id',
            'etapa_definicion_actual', 'sub_etapa_definicion_actual',
            'actuacion_definicion_siguiente', 'estado_general', 'fecha_actualizacion',
            'historial_actuaciones_siniestro'
        ]


class SiniestrosSlr(serializers.ModelSerializer):
    media = SiniestroMediaSlr(many=True, read_only=True)
    entes_atendieron = EnteAtencionSlr(many=True, read_only=True)
    entes_atendieron_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, allow_empty=True
    )
    logs = SiniestroLogSlr(many=True, read_only=True)
    colaborador_data = ColaboradoresSlr(source='colaborador', read_only=True)
    vehiculo_data = VehiculosSlr(source='vehiculo', read_only=True)
    empresa_data = EmpresasSlr(source='empresa', read_only=True)
    acta_conciliacion = ActaConciliacionSlr(read_only=True)
    terceross = TerceroSlr(many=True, read_only=True, source='terceros')
    ipat_doc = IpatSlr(read_only=True, source='ipat_record')
    victimas_detalle = serializers.SerializerMethodField(read_only=True)
    numero_victimas = serializers.IntegerField(source='numero_victimas_calculado', read_only=True)
    proceso_detalle_siniestro = SiniestroProcesoSlr(read_only=True)
    datos_adicionales = serializers.JSONField(required=False)

    class Meta:
        model = Siniestro
        fields = [
            'id', 'descripcion', 'tipo_evento', 'gravedad', 'entes_atendieron', 'entes_atendieron_ids',
            'latitud', 'longitud', 'zona', 'fecha_creacion', 'colaborador', 'vehiculo',
            'empresa', 'ipat', 'inmovilizacion', 'direccion_text', 'media', 'logs',
            'acta_conciliacion', 'terceross', 'ipat_doc', 'numero_victimas', 'victimas_detalle',
            'proceso_detalle_siniestro',
            'colaborador_data', 'vehiculo_data', 'empresa_data', 'datos_adicionales'
        ]
        extra_kwargs = {
            'colaborador': {'write_only': True, 'required': False, 'allow_null':True},
            'vehiculo': {'write_only': True, 'required': False, 'allow_null':True},
            'empresa': {'write_only': True, 'required': False, 'allow_null':True},
        }


    def get_victimas_detalle(self, obj):
        procesos = []
        for victima_instance in obj.victimas.all():
            try:
                if hasattr(victima_instance, 'proceso_estado') and victima_instance.proceso_estado is not None:
                    procesos.append(victima_instance.proceso_estado)
            except VictimaProceso.DoesNotExist:
                continue
        
        return VictimaProcesoSlr(procesos, many=True, context=self.context).data


    def create(self, validated_data):
        entes_ids = validated_data.pop('entes_atendieron_ids', [])
        siniestro = Siniestro.objects.create(**validated_data)
        if entes_ids:
            siniestro.entes_atendieron.set(entes_ids)
        SiniestroProceso.objects.create(siniestro=siniestro)
        return siniestro

    def update(self, instance, validated_data):
        entes_ids = validated_data.pop('entes_atendieron_ids', None)
        if entes_ids is not None:
            instance.entes_atendieron.set(entes_ids)

        return super().update(instance, validated_data)
    

from rest_framework import serializers
from .models import (
    Evaluation, Part, Section, Question, Option,
    MatchingPair, OrderingItem, MultiSelectOption,
    HotspotCoordinate, FillBlank
)

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'is_correct', 'order']
        read_only_fields = ['id']

class MatchingPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchingPair
        fields = ['id', 'left', 'right', 'order']
        read_only_fields = ['id']

class OrderingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderingItem
        fields = ['id', 'text', 'order']
        read_only_fields = ['id']

class MultiSelectOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultiSelectOption
        fields = ['id', 'text', 'is_correct', 'order']
        read_only_fields = ['id']

class HotspotCoordinateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotspotCoordinate
        fields = ['id', 'x', 'y']
        read_only_fields = ['id']

class FillBlankSerializer(serializers.ModelSerializer):
    class Meta:
        model = FillBlank
        fields = ['id', 'blank_index', 'correct_text']
        read_only_fields = ['id']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, required=False)
    matching_pairs = MatchingPairSerializer(many=True, required=False)
    ordering_items = OrderingItemSerializer(many=True, required=False)
    multi_select_options = MultiSelectOptionSerializer(many=True, required=False)
    hotspot_coordinates = HotspotCoordinateSerializer(many=True, required=False)
    fill_blanks = FillBlankSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = [
            'id', 'type', 'text', 'media', 'media_url', 'order',
            'score', 'feedback_correct', 'feedback_incorrect',
            'correct_answer', 'open_answer',
            'options', 'matching_pairs', 'ordering_items',
            'multi_select_options', 'rating_value',
            'hotspot_coordinates', 'fill_blanks',
            'file_answer', 'scenario_text', 'time_limit'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        question_type = data.get('type')
        if question_type == 'multiple_choice':
            options = data.get('options', [])
            if len(options) < 2:
                raise serializers.ValidationError("Se requieren al menos dos opciones.")
            if not any(opt['is_correct'] for opt in options):
                raise serializers.ValidationError("Al menos una opción debe ser correcta.")
        elif question_type == 'true_false':
            if data.get('correct_answer') is None:
                raise serializers.ValidationError("Se requiere una respuesta correcta.")
        elif question_type == 'open_answer':
            if not data.get('open_answer'):
                raise serializers.ValidationError("Se requiere una respuesta abierta.")
        elif question_type == 'matching':
            pairs = data.get('matching_pairs', [])
            if len(pairs) < 2:
                raise serializers.ValidationError("Se requieren al menos dos pares de matching.")
        elif question_type == 'ordering':
            items = data.get('ordering_items', [])
            if len(items) < 2:
                raise serializers.ValidationError("Se requieren al menos dos elementos para ordenar.")
        elif question_type == 'multiple_selection':
            options = data.get('multi_select_options', [])
            if len(options) < 2:
                raise serializers.ValidationError("Se requieren al menos dos opciones.")
            if not any(opt['is_correct'] for opt in options):
                raise serializers.ValidationError("Al menos una opción debe ser correcta.")
        elif question_type == 'rating':
            if not data.get('rating_value'):
                raise serializers.ValidationError("Se requiere un valor de rating.")
        elif question_type == 'hotspot':
            coords = data.get('hotspot_coordinates', [])
            if len(coords) < 1:
                raise serializers.ValidationError("Se requiere al menos una coordenada para hotspot.")
        elif question_type == 'fill_in_blanks':
            blanks = data.get('fill_blanks', [])
            if len(blanks) < 1:
                raise serializers.ValidationError("Se requiere al menos un espacio para rellenar.")
        elif question_type == 'scenario':
            if not data.get('scenario_text'):
                raise serializers.ValidationError("Se requiere texto de escenario.")
        elif question_type == 'timed':
            if not data.get('time_limit'):
                raise serializers.ValidationError("Se requiere un límite de tiempo.")
        return data

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        matching_pairs_data = validated_data.pop('matching_pairs', [])
        ordering_items_data = validated_data.pop('ordering_items', [])
        multi_select_options_data = validated_data.pop('multi_select_options', [])
        hotspot_coordinates_data = validated_data.pop('hotspot_coordinates', [])
        fill_blanks_data = validated_data.pop('fill_blanks', [])

        question = Question.objects.create(**validated_data)

        Option.objects.bulk_create(
            [Option(question=question, **opt) for opt in options_data]
        )
        MatchingPair.objects.bulk_create(
            [MatchingPair(question=question, **p) for p in matching_pairs_data]
        )
        OrderingItem.objects.bulk_create(
            [OrderingItem(question=question, **i) for i in ordering_items_data]
        )
        MultiSelectOption.objects.bulk_create(
            [MultiSelectOption(question=question, **ms) for ms in multi_select_options_data]
        )
        HotspotCoordinate.objects.bulk_create(
            [HotspotCoordinate(question=question, **hc) for hc in hotspot_coordinates_data]
        )
        FillBlank.objects.bulk_create(
            [FillBlank(question=question, **fb) for fb in fill_blanks_data]
        )

        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        matching_pairs_data = validated_data.pop('matching_pairs', None)
        ordering_items_data = validated_data.pop('ordering_items', None)
        multi_select_options_data = validated_data.pop('multi_select_options', None)
        hotspot_coordinates_data = validated_data.pop('hotspot_coordinates', None)
        fill_blanks_data = validated_data.pop('fill_blanks', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if options_data is not None:
            existing_options = {o.id: o for o in instance.options.all()}
            new_options = []
            update_options = []
            sent_ids = []
            for opt_data in options_data:
                oid = opt_data.get('id')
                if oid and oid in existing_options:
                    opt = existing_options[oid]
                    opt.text = opt_data.get('text', opt.text)
                    opt.is_correct = opt_data.get('is_correct', opt.is_correct)
                    opt.order = opt_data.get('order', opt.order)
                    update_options.append(opt)
                    sent_ids.append(oid)
                else:
                    new_options.append(Option(question=instance, **opt_data))
            Option.objects.bulk_create(new_options)
            if update_options:
                Option.objects.bulk_update(update_options, ['text', 'is_correct', 'order'])
            for eid, existing_opt in existing_options.items():
                if eid not in sent_ids:
                    existing_opt.delete()

        if matching_pairs_data is not None:
            existing_pairs = {mp.id: mp for mp in instance.matching_pairs.all()}
            new_pairs = []
            update_pairs = []
            sent_ids = []
            for pair_data in matching_pairs_data:
                pid = pair_data.get('id')
                if pid and pid in existing_pairs:
                    pair = existing_pairs[pid]
                    pair.left = pair_data.get('left', pair.left)
                    pair.right = pair_data.get('right', pair.right)
                    pair.order = pair_data.get('order', pair.order)
                    update_pairs.append(pair)
                    sent_ids.append(pid)
                else:
                    new_pairs.append(MatchingPair(question=instance, **pair_data))
            MatchingPair.objects.bulk_create(new_pairs)
            if update_pairs:
                MatchingPair.objects.bulk_update(update_pairs, ['left','right','order'])
            for eid, existing_pair in existing_pairs.items():
                if eid not in sent_ids:
                    existing_pair.delete()

        if ordering_items_data is not None:
            existing_items = {oi.id: oi for oi in instance.ordering_items.all()}
            new_items = []
            update_items = []
            sent_ids = []
            for item_data in ordering_items_data:
                iid = item_data.get('id')
                if iid and iid in existing_items:
                    item = existing_items[iid]
                    item.text = item_data.get('text', item.text)
                    item.order = item_data.get('order', item.order)
                    update_items.append(item)
                    sent_ids.append(iid)
                else:
                    new_items.append(OrderingItem(question=instance, **item_data))
            OrderingItem.objects.bulk_create(new_items)
            if update_items:
                OrderingItem.objects.bulk_update(update_items, ['text','order'])
            for eid, existing_item in existing_items.items():
                if eid not in sent_ids:
                    existing_item.delete()

        if multi_select_options_data is not None:
            existing_multi = {m.id: m for m in instance.multi_select_options.all()}
            new_multi = []
            update_multi = []
            sent_ids = []
            for ms_data in multi_select_options_data:
                msid = ms_data.get('id')
                if msid and msid in existing_multi:
                    ms = existing_multi[msid]
                    ms.text = ms_data.get('text', ms.text)
                    ms.is_correct = ms_data.get('is_correct', ms.is_correct)
                    ms.order = ms_data.get('order', ms.order)
                    update_multi.append(ms)
                    sent_ids.append(msid)
                else:
                    new_multi.append(MultiSelectOption(question=instance, **ms_data))
            MultiSelectOption.objects.bulk_create(new_multi)
            if update_multi:
                MultiSelectOption.objects.bulk_update(update_multi, ['text','is_correct','order'])
            for eid, existing_ms in existing_multi.items():
                if eid not in sent_ids:
                    existing_ms.delete()

        if hotspot_coordinates_data is not None:
            existing_coords = {c.id: c for c in instance.hotspot_coordinates.all()}
            new_coords = []
            update_coords = []
            sent_ids = []
            for coord_data in hotspot_coordinates_data:
                cid = coord_data.get('id')
                if cid and cid in existing_coords:
                    coord = existing_coords[cid]
                    coord.x = coord_data.get('x', coord.x)
                    coord.y = coord_data.get('y', coord.y)
                    update_coords.append(coord)
                    sent_ids.append(cid)
                else:
                    new_coords.append(HotspotCoordinate(question=instance, **coord_data))
            HotspotCoordinate.objects.bulk_create(new_coords)
            if update_coords:
                HotspotCoordinate.objects.bulk_update(update_coords, ['x','y'])
            for eid, existing_coord in existing_coords.items():
                if eid not in sent_ids:
                    existing_coord.delete()

        if fill_blanks_data is not None:
            existing_blanks = {fb.id: fb for fb in instance.fill_blanks.all()}
            new_blanks = []
            update_blanks = []
            sent_ids = []
            for fb_data in fill_blanks_data:
                fbid = fb_data.get('id')
                if fbid and fbid in existing_blanks:
                    fb = existing_blanks[fbid]
                    fb.blank_index = fb_data.get('blank_index', fb.blank_index)
                    fb.correct_text = fb_data.get('correct_text', fb.correct_text)
                    update_blanks.append(fb)
                    sent_ids.append(fbid)
                else:
                    new_blanks.append(FillBlank(question=instance, **fb_data))
            FillBlank.objects.bulk_create(new_blanks)
            if update_blanks:
                FillBlank.objects.bulk_update(update_blanks, ['blank_index','correct_text'])
            for eid, existing_fb in existing_blanks.items():
                if eid not in sent_ids:
                    existing_fb.delete()

        return instance

class SectionSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Section
        fields = [
            'id', 'title', 'description', 'media', 'media_url',
            'order', 'questions', 'part', 'evaluation'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        section = Section.objects.create(**validated_data)
        for question_data in questions_data:
            QuestionSerializer().create({**question_data, 'section': section})
        return section

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if questions_data is not None:
            existing_qs = {q.id: q for q in instance.questions.all()}
            new_qs = []
            sent_ids = []
            for q_data in questions_data:
                qid = q_data.get('id')
                if qid and qid in existing_qs:
                    QuestionSerializer().update(existing_qs[qid], q_data)
                    sent_ids.append(qid)
                else:
                    new_qs.append(q_data)
            for qid, q_obj in existing_qs.items():
                if qid not in sent_ids:
                    q_obj.delete()
            for qd in new_qs:
                QuestionSerializer().create({**qd, 'section': instance})

        return instance

class PartSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    sections = SectionSerializer(many=True, required=False)

    class Meta:
        model = Part
        fields = [
            'id', 'title', 'description', 'order', 'score',
            'questions', 'sections', 'evaluation'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        sections_data = validated_data.pop('sections', [])
        part = Part.objects.create(**validated_data)

        for question_data in questions_data:
            QuestionSerializer().create({**question_data, 'part': part})
        for section_data in sections_data:
            SectionSerializer().create({
                **section_data,
                'part': part,
                'evaluation': part.evaluation
            })

        return part

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        sections_data = validated_data.pop('sections', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if questions_data is not None:
            existing_qs = {q.id: q for q in instance.questions.all()}
            new_qs = []
            sent_ids = []
            for q_data in questions_data:
                qid = q_data.get('id')
                if qid and qid in existing_qs:
                    QuestionSerializer().update(existing_qs[qid], q_data)
                    sent_ids.append(qid)
                else:
                    new_qs.append(q_data)
            for qid, q_obj in existing_qs.items():
                if qid not in sent_ids:
                    q_obj.delete()
            for qd in new_qs:
                QuestionSerializer().create({**qd, 'part': instance})

        if sections_data is not None:
            existing_sections = {s.id: s for s in instance.sections.all()}
            new_sections = []
            sent_ids = []
            for s_data in sections_data:
                sid = s_data.get('id')
                if sid and sid in existing_sections:
                    SectionSerializer().update(existing_sections[sid], {
                        **s_data, 'part': instance, 'evaluation': instance.evaluation
                    })
                    sent_ids.append(sid)
                else:
                    new_sections.append(s_data)
            for sid, s_obj in existing_sections.items():
                if sid not in sent_ids:
                    s_obj.delete()
            for sd in new_sections:
                SectionSerializer().create({
                    **sd, 'part': instance, 'evaluation': instance.evaluation
                })

        return instance



class MinimalEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = [
            'id', 'title', 'description', 'global_time_limit',
            'randomize_questions', 'randomize_answers',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class EvaluationSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    sections = SectionSerializer(many=True, required=False)
    parts = PartSerializer(many=True, required=False)

    class Meta:
        model = Evaluation
        fields = [
            'id', 'title', 'description', 'global_time_limit',
            'randomize_questions', 'randomize_answers',
            'questions', 'sections', 'parts',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate(self, data):
        return data

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        sections_data = validated_data.pop('sections', [])
        parts_data = validated_data.pop('parts', [])
        evaluation = Evaluation.objects.create(**validated_data)

        for question_data in questions_data:
            QuestionSerializer().create({
                **question_data,
                'evaluation': evaluation
            })
        for section_data in sections_data:
            SectionSerializer().create({
                **section_data,
                'evaluation': evaluation
            })
        for part_data in parts_data:
            PartSerializer().create({
                **part_data,
                'evaluation': evaluation
            })
        return evaluation

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        sections_data = validated_data.pop('sections', None)
        parts_data = validated_data.pop('parts', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if questions_data is not None:
            existing_qs = {q.id: q for q in instance.questions.all()}
            new_qs = []
            sent_ids = []
            for q_data in questions_data:
                qid = q_data.get('id')
                if qid and qid in existing_qs:
                    QuestionSerializer().update(existing_qs[qid], q_data)
                    sent_ids.append(qid)
                else:
                    new_qs.append(q_data)
            for qid, q_obj in existing_qs.items():
                if qid not in sent_ids:
                    q_obj.delete()
            for qd in new_qs:
                QuestionSerializer().create({**qd, 'evaluation': instance})

        if sections_data is not None:
            existing_sections = {s.id: s for s in instance.sections.all()}
            new_sections = []
            sent_ids = []
            for s_data in sections_data:
                sid = s_data.get('id')
                if sid and sid in existing_sections:
                    SectionSerializer().update(existing_sections[sid], {
                        **s_data, 'evaluation': instance
                    })
                    sent_ids.append(sid)
                else:
                    new_sections.append(s_data)
            for sid, s_obj in existing_sections.items():
                if sid not in sent_ids:
                    s_obj.delete()
            for sd in new_sections:
                SectionSerializer().create({**sd, 'evaluation': instance})

        if parts_data is not None:
            existing_parts = {p.id: p for p in instance.parts.all()}
            new_parts = []
            sent_ids = []
            for p_data in parts_data:
                pid = p_data.get('id')
                if pid and pid in existing_parts:
                    PartSerializer().update(existing_parts[pid], p_data)
                    sent_ids.append(pid)
                else:
                    new_parts.append(p_data)
            for pid, p_obj in existing_parts.items():
                if pid not in sent_ids:
                    p_obj.delete()
            for pd in new_parts:
                PartSerializer().create({**pd, 'evaluation': instance})

        return instance