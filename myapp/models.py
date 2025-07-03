
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from django.db import models
import uuid

class TipoDocumento(models.Model):
    nombreDoc = models.CharField(max_length=99, null=False)
    denominacion = models.CharField(max_length=5, null=False, unique=True)
    estado = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

class Empresas(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre_empresa = models.CharField(max_length=150, null=False, unique=True)
    nombre_empresa_corto = models.CharField(max_length=150, null=True)
    nit = models.CharField(max_length=12, null=False, unique=True)
    direccion = models.CharField(max_length=150)
    ciudad = models.CharField(null=True)
    estado = models.BooleanField(default=True)
    telefono1 = models.IntegerField(null=False)
    telefono2 = models.IntegerField(null=True)
    email = models.EmailField(max_length=150, null=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    representante_legal = models.CharField(null=True)
    representante_firma = models.CharField(null=True)
    email_informacion = models.CharField(null=True)
    email_juridica = models.CharField(null=True)
    

class Department(models.Model):
    department_name = models.CharField(max_length=150, null=False)
    empresa = models.ForeignKey(Empresas, on_delete=models.DO_NOTHING, null=False)

class Roles(models.Model):
    detalle_rol = models.CharField(max_length=100, null=False)
    empresa = models.ForeignKey(
        Empresas, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.DO_NOTHING, null=False)
    
class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
class TipoLinea(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
class ClaseVehiculo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
class Carroceria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
class Combustible(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
class TipoOperacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
class Ciudad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
class NivelServicio(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
class Color(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

class Vehiculos(models.Model):
    placa = models.CharField(max_length=7, primary_key=True)
    empresa = models.ForeignKey(Empresas, on_delete=models.CASCADE, related_name='vehiculos', null=True)
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True)
    tipoLinea = models.ForeignKey(TipoLinea, on_delete=models.SET_NULL, null=True, blank=True)
    paxLt = models.IntegerField(null=True)
    paxRl = models.IntegerField(null=True)
    clase = models.ForeignKey(ClaseVehiculo, on_delete=models.SET_NULL, null=True)
    carroceria = models.ForeignKey(Carroceria, on_delete=models.SET_NULL, null=True)
    numeroMotor = models.CharField(max_length=100, null=True)
    tipoMotor = models.CharField(max_length=100, null=True, blank=True)
    combustible = models.ForeignKey(Combustible, on_delete=models.SET_NULL, null=True)
    chasis = models.CharField(max_length=100, null=True, unique=False)
    serie = models.CharField(max_length=100, null=True, unique=True)
    vin = models.CharField(max_length=100, null=True, blank=True, unique=True)
    ciudadBase = models.ForeignKey(Ciudad, on_delete=models.SET_NULL, null=True)
    modelo = models.IntegerField(null=True)
    numeroEjes = models.IntegerField(null=True)
    cilindraje = models.IntegerField(null=True)
    licenciaTransito = models.CharField(max_length=100, null=True, unique=True)
    estado = models.CharField(max_length=100, null=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True)
    unionTemporal = models.BooleanField(default=False)
    facturaCompra = models.FileField(upload_to='facturas/', null=True, blank=True)
    declaracionImportacion = models.FileField(upload_to='importaciones/', null=True, blank=True)
    caracteristicasMecanicas = models.FileField(upload_to='caracteristicas/', null=True, blank=True)

# from django.contrib.auth import get_user_model
class VehiculoLog(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='logs')
    modelo_afectado = models.CharField(max_length=200)
    instancia_pk = models.CharField(max_length=200)
    accion = models.CharField(max_length=200)
    timestamp = models.DateTimeField(default=timezone.now)
    cambios = models.JSONField(null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='vehiculo_logs'
    )

    def __str__(self):
        return f"{self.vehiculo.placa} - {self.modelo_afectado} - {self.accion} - {self.timestamp}"



class EventoDocumento(models.Model):
    OPCIONES_TIPO_DOCUMENTO = [
        ('hurtoOferta', 'Hurto con Oferta'),
        ('hurtoSinOfertaGeneral', 'Hurto sin Oferta (General)'),
        ('hurtoSinOferta', 'Hurto sin Oferta'),
        ('fallaConductor', 'Falla Conductor'),
        ('peConResponsabilidad', 'PE con Responsabilidad (Sí)'),
        ('peConResponsabilidadEvidencia', 'PE con Responsabilidad (Sí) c/ Evidencia'),
        ('paso2', 'Hurto de Equipaje - Paso 2'),
        ('contrapropuesta', 'Contrapropuesta'),
    ]

    OPCIONES_STATUS = [
        ('pendiente', 'Pendiente'),
        ('finalizado', 'Finalizado'),
    ]

    id = models.AutoField(primary_key=True)
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='eventos')
    empresa = models.ForeignKey(Empresas, on_delete=models.CASCADE, null=True, blank=True)
    tipo_documento = models.CharField(max_length=50, choices=OPCIONES_TIPO_DOCUMENTO)
    fecha_evento = models.DateTimeField(default=timezone.now)
    pdf_file = models.FileField(upload_to='pdf_eventos/', null=True, blank=True)
    datos_json = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=OPCIONES_STATUS, default='pendiente')


class Colaboradores(models.Model):
    num_documento = models.IntegerField(primary_key=True)
    tipo_documento = models.ForeignKey(
        TipoDocumento, on_delete=models.DO_NOTHING, null=True, blank=True)
    exp_documento = models.CharField(max_length=99, null=True)
    nombres = models.CharField(max_length=99, null=True)
    apellidos = models.CharField(max_length=99, null=True)
    email = models.EmailField(max_length=150, null=True)
    rol = models.ForeignKey(Roles, on_delete=models.DO_NOTHING, null=True, blank=True)
    empresa = models.ForeignKey(Empresas, on_delete=models.CASCADE)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.DO_NOTHING, null=True, blank=True, to_field='placa', db_column='vehiculo')
    is_active = models.BooleanField(default=True, null=False)
    face_ids = ArrayField(models.CharField(max_length=255), size=5, null=True)
    signature = models.TextField(blank=True, null=True)
    telefono = models.CharField(null=True)

    
class Servicio(models.Model):
    vehiculo = models.OneToOneField(Vehiculos, null=True, on_delete=models.CASCADE, related_name='servicio')
    numeroInterno = models.IntegerField(null=True)
    empresaOficial = models.ForeignKey(Empresas, on_delete=models.CASCADE, related_name='servicios_oficiales')
    empresaAdministra = models.ForeignKey(Empresas, on_delete=models.CASCADE, null=True, related_name='servicios_administrados')
    tipoOperacion = models.ForeignKey(TipoOperacion, on_delete=models.CASCADE, null=True)
    nivelServicio = models.ForeignKey(NivelServicio, on_delete=models.CASCADE, null=True)
    servicio = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=True)
    fechaIngreso = models.DateField(null=True)
    fechaFinServicio = models.DateField(null=True, blank=True)

class Propietario(models.Model):
    tipoDocumento = models.ForeignKey(TipoDocumento, on_delete=models.SET_NULL, null=True, blank=True)
    identificacion = models.CharField(max_length=100, null=True, unique=True)
    direccion = models.CharField(max_length=150, null=True)
    ciudad = models.CharField(null=True)
    departamento = models.CharField(null=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    nombres = models.CharField(max_length=100, null=True)
    apellidos = models.CharField(max_length=100, null=True, blank=True)
    fechaIngreso = models.DateField(auto_now_add=True)
    correo = models.EmailField(max_length=150, null=True, blank=True)

class PropietarioLog(models.Model):
    propietario = models.ForeignKey(Propietario, on_delete=models.CASCADE, related_name='logs')
    modelo_afectado = models.CharField(max_length=100)
    instancia_pk = models.CharField(max_length=100)
    accion = models.CharField(max_length=20)
    timestamp = models.DateTimeField(default=timezone.now)
    cambios = models.JSONField(null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='propietario_logs'
    )

    def __str__(self):
        return f"{self.propietario.identificacion} - {self.modelo_afectado} - {self.accion} - {self.timestamp}"

class Contrato(models.Model):
    placa = models.CharField(max_length=10, unique=True)
    pdf_contrato = models.FileField(upload_to='contratos/', blank=True, null=True)
    firmado = models.BooleanField(default=False)
    link_firma = models.URLField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_vencimiento = models.DateTimeField(blank=True, null=True)

class VehiculoPropietario(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='propietarios_relations')
    propietario = models.ForeignKey(Propietario, on_delete=models.CASCADE, related_name='vehiculos_relations')
    porcentaje = models.IntegerField(null=True)

class Tenedor(models.Model):
    tipoDocumento = models.ForeignKey(TipoDocumento, on_delete=models.SET_NULL, null=True, blank=True)
    identificacion = models.CharField(max_length=100, null=False, unique=True)
    nombres = models.CharField(max_length=100, null=False)
    apellidos = models.CharField(max_length=100, null=True, blank=True)
    fechaIngreso = models.DateField(auto_now_add=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    correo = models.EmailField(max_length=150, null=True, blank=True)

class VehiculoTenedor(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='tenedores_relations')
    tenedor = models.ForeignKey(Tenedor, on_delete=models.CASCADE, related_name='vehiculos_relations')
    porcentaje = models.IntegerField(null=True)

class Aseguradora(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)
    nit = models.CharField(max_length=50, null=True, blank=True)

class TipoDocumentoVehiculo(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)

class Soat(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='soat_docs')
    tipo_documento_vehiculo = models.ForeignKey(TipoDocumentoVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_expedicion = models.DateField(null=True)
    vigencia_desde = models.DateField(null=True)
    vigencia_hasta = models.DateField(null=True)
    numero_poliza = models.CharField(max_length=100, null=True)
    placa = models.CharField(max_length=7, null=True, blank=True)
    soporte = models.CharField(max_length=512, null=True, blank=True)
    estado = models.BooleanField(default=True)
    aseguradora_nombre = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['vehiculo', '-vigencia_hasta']

class RevisionTecnomecanica(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='revisiones_tecnomecanicas')
    tipo_documento_vehiculo = models.ForeignKey(TipoDocumentoVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.SET_NULL, null=True, blank=True) # Typically no insurer for RTM
    fecha_expedicion = models.DateField(null=True)
    no_certificado = models.CharField(max_length=99, null=True)
    fecha_vencimiento = models.DateField(null=True)
    placa = models.CharField(max_length=7, null=True, blank=True)
    soporte = models.CharField(max_length=512, null=True, blank=True)
    estado = models.BooleanField(default=True)
    entidad_expide_certificado = models.CharField(max_length=200, null=True, blank=True)
    nit = models.CharField(max_length=50, null=True, blank=True)


    class Meta:
        ordering = ['vehiculo', '-fecha_vencimiento']

class TarjetaOperacion(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='tarjetas_operacion')
    tipo_documento_vehiculo = models.ForeignKey(TipoDocumentoVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.SET_NULL, null=True, blank=True)
    soporte = models.CharField(max_length=512, null=True, blank=True)
    numero = models.CharField(max_length=100, null=True)
    fechaExpedicion = models.DateField(null=True)
    fechaInicialVigencia = models.DateField(null=True)
    fechaFinVigencia = models.DateField(null=True)
    estado = models.BooleanField(default=True)
    placa = models.CharField(max_length=7, null=True, blank=True)
    nit = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['vehiculo', '-fechaFinVigencia']

class PolizaContractual(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='polizas_contractuales')
    tipo_documento_vehiculo = models.ForeignKey(TipoDocumentoVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.SET_NULL, null=True, blank=True)
    numero_poliza = models.CharField(max_length=100, null=True, blank=True)
    aseguradora_nombre_alt = models.CharField(max_length=255, null=True, blank=True)
    fecha_expedicion = models.DateField(null=True, blank=True)
    fecha_inicio_vigencia = models.DateField(null=True, blank=True)
    fecha_fin_vigencia = models.DateField(null=True, blank=True)
    soporte = models.CharField(max_length=512, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        ordering = ['vehiculo', '-fecha_fin_vigencia']

class PolizaExtracontractual(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='polizas_extracontractuales')
    tipo_documento_vehiculo = models.ForeignKey(TipoDocumentoVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.SET_NULL, null=True, blank=True)
    numero_poliza = models.CharField(max_length=100, null=True, blank=True)
    aseguradora_nombre_alt = models.CharField(max_length=255, null=True, blank=True)
    fecha_expedicion = models.DateField(null=True, blank=True)
    fecha_inicio_vigencia = models.DateField(null=True, blank=True)
    fecha_fin_vigencia = models.DateField(null=True, blank=True)
    soporte = models.CharField(max_length=512, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        ordering = ['vehiculo', '-fecha_fin_vigencia']

class PolizaTodoRiesgo(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='polizas_todo_riesgo')
    tipo_documento_vehiculo = models.ForeignKey(TipoDocumentoVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.SET_NULL, null=True, blank=True)
    numero_poliza = models.CharField(max_length=100)
    aseguradora_nombre_alt = models.CharField(max_length=255, null=True, blank=True)
    fecha_expedicion = models.DateField(null=True, blank=True)
    fecha_inicio_vigencia = models.DateField(null=True, blank=True)
    fecha_fin_vigencia = models.DateField(null=True, blank=True)
    soporte = models.CharField(max_length=512, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        ordering = ['vehiculo', '-fecha_fin_vigencia']

class FichaTecnicaHomologacionChasis(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='fichas_homologacion_chasis')
    tipo_documento_vehiculo = models.ForeignKey(TipoDocumentoVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    numero_documento = models.CharField(max_length=100, null=True, blank=True)
    fecha_expedicion = models.DateField(null=True, blank=True)
    soporte = models.CharField(max_length=512, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['vehiculo', 'numero_documento', 'fecha_expedicion'], name='unique_ft_chasis_doc_date_v3'),
            models.UniqueConstraint(fields=['vehiculo', 'soporte'], name='unique_ft_chasis_support_v3', condition=Q(numero_documento__isnull=True))
        ]
        ordering = ['vehiculo', '-fecha_expedicion']

class FichaTecnicaHomologacionCarroceria(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='fichas_homologacion_carroceria')
    tipo_documento_vehiculo = models.ForeignKey(TipoDocumentoVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    numero_documento = models.CharField(max_length=100, null=True, blank=True)
    fecha_expedicion = models.DateField(null=True, blank=True)
    soporte = models.CharField(max_length=512, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['vehiculo', 'numero_documento', 'fecha_expedicion'], name='unique_ft_carroceria_doc_date_v3'),
            models.UniqueConstraint(fields=['vehiculo', 'soporte'], name='unique_ft_carroceria_support_v3', condition=Q(numero_documento__isnull=True))
        ]
        ordering = ['vehiculo', '-fecha_expedicion']

class FichaTecnicaHomologacionVehCarrozado(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='fichas_homologacion_veh_carrozado')
    tipo_documento_vehiculo = models.ForeignKey(TipoDocumentoVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    numero_documento = models.CharField(max_length=100, null=True, blank=True)
    fecha_expedicion = models.DateField(null=True, blank=True)
    soporte = models.CharField(max_length=512, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['vehiculo', 'numero_documento', 'fecha_expedicion'], name='unique_ft_vehcarroz_doc_date_v3'),
            models.UniqueConstraint(fields=['vehiculo', 'soporte'], name='unique_ft_vehcarroz_support_v3', condition=Q(numero_documento__isnull=True))
        ]
        ordering = ['vehiculo', '-fecha_expedicion']

class LicenciaTransito(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='licencias_transito_docs')
    numero_documento = models.CharField(max_length=100)
    fecha_expedicion = models.DateField(null=True, blank=True)
    fecha_matricula = models.DateField(null=True, blank=True)
    soporte = models.CharField(max_length=512, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        ordering = ['vehiculo', '-fecha_expedicion']

class ReporteVencimientosDiario(models.Model):
    empresa = models.ForeignKey('Empresas', on_delete=models.CASCADE, related_name='reportes_vencimientos')
    fecha_reporte = models.DateField()
    datos_reporte = models.JSONField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['empresa', '-fecha_reporte']

class Poliza(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='polizas')
    soporte = models.FileField(upload_to='polizas/', null=True, blank=True)
    numeroDocumento = models.CharField(max_length=100, null=False)
    documento = models.CharField(max_length=100, null=False)
    fechaExpedicion = models.DateField(null=False)
    fechaInicioVigencia = models.DateField(null=False)
    fechaFinVigencia = models.DateField(null=False)
    nitAseguradora = models.CharField(max_length=100, null=False)
    nombreAseguradora = models.CharField(max_length=150, null=False)
    estado = models.CharField(max_length=100, null=False)

class NovedadVehiculo(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='novedades_vehiculo')
    descripcion = models.TextField(null=False)
    fechaNovedad = models.DateField(null=False)

class FichaTecnica(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='fichas_tecnicas')
    descripcion = models.TextField(null=False)
    fecha = models.DateField(null=False)
    estado = models.CharField(max_length=100, null=False)

class ConductorAsociado(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='conductores_asociados')
    nombre = models.CharField(max_length=100, null=False)
    identificacion = models.CharField(max_length=100, null=False)
    licencia = models.CharField(max_length=100, null=False)
    fechaAsignacion = models.DateField(null=False)

class ProcedimientoJuridico(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='procedimientos_juridicos')
    descripcion = models.TextField()
    fechaInicio = models.DateField()
    fechaFin = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=50, default='En Proceso')

class EventoLegal(models.Model):
    TIPO_EVENTO_CHOICES = [
        ('MATRICULA', 'Matrícula'),
        ('TRASPASO', 'Traspaso'),
        ('REGRABACION_MOTOR', 'Regrabación de motor'),
        ('REGRABACION_CHASIS', 'Regrabación de chasis'),
        ('DUPLICADO_LICENCIA', 'Duplicado de licencia'),
        ('DUPLICADO_PLACAS', 'Duplicado de placas'),
        ('INSCRIPCION_PRENDA', 'Inscripción de prenda'),
        ('LEVANTAR_PRENDA', 'Levantamiento de prenda'),
        ('CAMBIO_MOTOR', 'Cambio de motor'),
        ('DESVINCULACION', 'Desvinculación'),
    ]
    vehiculo = models.ForeignKey(Vehiculos, on_delete=models.CASCADE, related_name='eventos_legales')
    tipo_evento = models.CharField(max_length=50, choices=TIPO_EVENTO_CHOICES)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class EventoLegalFile(models.Model):
    evento_legal = models.ForeignKey(EventoLegal, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to='eventos_legales')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class Mantenimiento(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='mantenimientos')
    descripcion = models.TextField(null=False)
    fecha = models.DateField(null=False)
    costo = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    proveedor = models.CharField(max_length=150, null=False)

class Facturacion(models.Model):
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.CASCADE, related_name='facturacion')
    facturaNumero = models.CharField(max_length=100, null=False)
    fecha = models.DateField(null=False)
    monto = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    estado = models.CharField(max_length=100, null=False)

class RegistroAsistencia(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]
    
    colaborador = models.ForeignKey('Colaboradores', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)
    left_early = models.BooleanField(default=False)
    
class Headquarters(models.Model):
    headquarters_name = models.CharField(max_length=259)
    headquarters_address = models.CharField(max_length=259)
    headquarters_departament = models.CharField(max_length=99)
    headquerters_city = models.CharField(max_length=99)
    headquarters_coordinates = models.JSONField(default=list, blank=True)

class Login(AbstractUser):
    documento_num = models.OneToOneField(
        Colaboradores, on_delete=models.CASCADE, primary_key=True)
    groups = models.ManyToManyField(Group, related_name='logins', blank=True)
    user_permissions = models.ManyToManyField(
        Permission, related_name='logins', blank=True)
    is_temporary = models.BooleanField(default=False)
    expiration_time = models.DateTimeField(null=True, blank=True)
    single_use_token = models.CharField(max_length=50, null=True, blank=True)
    has_logged_in = models.BooleanField(default=False)

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('avisos', 'Avisos'),
        ('mensajes', 'Mensajes'),
        ('tareas', 'Tareas'),
    ]

    STATUS_CHOICES = [
        ('expira pronto', 'Expira pronto'),
        ('no iniciado', 'No iniciado'),
        ('tardaron 8 días', 'Tardaron 8 días'),
        ('en curso', 'En curso'),
    ]

    user = models.ForeignKey(Colaboradores, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=NOTIFICATION_TYPE_CHOICES)
    content = models.TextField()
    time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True)
    is_read = models.BooleanField(default=False)

    def get_status_tag(self):
        status_tags = {
            'expira pronto': 'warning',
            'no iniciado': 'default',
            'tardaron 8 días': 'error',
            'en curso': 'processing',
        }
        return status_tags.get(self.status, 'default')
    
class Token(models.Model):
    token = models.CharField(max_length=6, null=False)
    fecha = models.DateField(auto_now_add=True)
    hora = models.DateTimeField(auto_now_add=True)
    vencido = models.BooleanField(default=False)
    documento_num = models.IntegerField(null=False)
    documento_num_cryp = models.CharField(null=False, max_length=60)

class Acciones(models.Model):
    nombre_accion = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)

class Modulos(models.Model):
    nom_modulo = models.CharField(max_length=150, null=False)
    id_modulo_padre = models.ForeignKey(
        'self', null=True, blank=True, related_name='submenus', on_delete=models.CASCADE)
    link = models.CharField(max_length=200, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class Permisos(models.Model):
    rol = models.ForeignKey(Roles, on_delete=models.CASCADE)
    modulo = models.ForeignKey(Modulos, on_delete=models.CASCADE)
    acciones = models.ManyToManyField(Acciones, blank=True)
    estado_permiso = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class RptoFuec(models.Model):
    nom_fuec = models.CharField(max_length=99, null=False)
    modificaciones = models.CharField(max_length=500, null=True)
    num_bus = models.IntegerField(null=False)
    num_viaje = models.IntegerField(null=False)
    user_creo = models.CharField(max_length=50, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)



class Evaluation(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(Colaboradores, on_delete=models.CASCADE, related_name='evaluations', null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    global_time_limit = models.PositiveIntegerField(blank=True, null=True)
    randomize_questions = models.BooleanField(default=False)
    randomize_answers = models.BooleanField(default=False)
class Part(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='parts', blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
class Section(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='sections', blank=True, null=True)
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='sections', blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    media = models.FileField(upload_to='media/', blank=True, null=True)
    media_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Opción Múltiple'),
        ('true_false', 'Verdadero/Falso'),
        ('open_answer', 'Respuesta Abierta'),
        ('matching', 'Matching'),
        ('ordering', 'Ordenamiento'),
        ('multiple_selection', 'Selección Múltiple'),
        ('rating', 'Rating'),
        ('hotspot', 'Hotspot'),
        ('fill_in_blanks', 'Rellenar Espacios'),
        ('file_upload', 'Subir Archivo'),
        ('scenario', 'Escenario'),
        ('timed', 'Cronometrada'),
    ]
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    text = models.CharField(max_length=1024)
    media = models.FileField(upload_to='media/', blank=True, null=True)
    media_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    score = models.PositiveIntegerField(default=0, blank=True, null=True)
    feedback_correct = models.TextField(blank=True, null=True)
    feedback_incorrect = models.TextField(blank=True, null=True)

    correct_answer = models.BooleanField(null=True, blank=True)
    open_answer = models.TextField(blank=True, null=True)
    rating_value = models.PositiveIntegerField(null=True, blank=True)
    file_answer = models.FileField(upload_to='file_answers/', blank=True, null=True)
    scenario_text = models.TextField(blank=True, null=True)
    time_limit = models.PositiveIntegerField(blank=True, null=True)
class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
class MatchingPair(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='matching_pairs')
    left = models.CharField(max_length=255)
    right = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
class OrderingItem(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='ordering_items')
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
class MultiSelectOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='multi_select_options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
class HotspotCoordinate(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='hotspot_coordinates')
    x = models.FloatField()
    y = models.FloatField()
class FillBlank(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='fill_blanks')
    blank_index = models.PositiveIntegerField(default=0)
    correct_text = models.CharField(max_length=255)
    


class TrainingsCategories(models.Model):
    tr_ctg_name = models.CharField(max_length=99, null=True)
    tr_ctg_abbreviation = models.CharField(max_length=9, null=True)
    
class Event(models.Model):
    event_record_number = models.CharField(max_length=255, null=True, blank=True)
    event_date = models.DateField(null=True, blank=True)
    event_start_date = models.DateTimeField(null=True, blank=True)
    event_end_date = models.DateTimeField(null=True, blank=True)
    event_place = models.ForeignKey(Headquarters, on_delete=models.SET_NULL, null=True)
    event_aim = models.TextField(null=True, blank=True)
    event_issue = models.TextField(null=True, blank=True)
    event_agenda = models.TextField(null=True, blank=True)
    event_development = models.TextField(null=True, blank=True)
    event_responsible = models.ForeignKey(Colaboradores, on_delete=models.SET_NULL, null=True, related_name='events_responsible')
    event_evaluation = models.ForeignKey(Evaluation, on_delete=models.SET_NULL, null=True, blank=True)
    event_required_roles = models.ManyToManyField(Roles, related_name='events_required_evaluation')
    event_required_colaboradores = models.ManyToManyField(Colaboradores, related_name='events_required_colaboradores')
    event_training_category = models.ForeignKey(TrainingsCategories, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    event_type = models.CharField(max_length=20, choices=[('reunion', 'Reunión'), ('capacitacion', 'Capacitación')], default='reunion')
    is_virtual = models.BooleanField(default=False)

    def get_events_by_user(user_id):
        colaborador = Colaboradores.objects.get(num_documento=user_id)
        participations = EventParticipant.objects.filter(colaborador=colaborador)
        events = Event.objects.filter(participants__in=participations)
        return events.distinct()

    def get_trainings_for_roles(self):
        required_roles = self.event_required_roles.all()
        if not required_roles:
            return []

        category_abbreviation = self.event_training_category.tr_ctg_abbreviation if self.event_training_category else 'Sin Categoría'
        return [{
            'nombre': self.event_name or 'Capacitación Sin Nombre',
            'categoria': category_abbreviation,
            'event_id': self.id_event
        }]

    def get_event_data(self):
        participant_details = []
        participants = self.participants.select_related('colaborador')
        for participant in participants:
            user = participant.colaborador
            participant_details.append({
                "participant_name": f'{user.nombres} {user.apellidos}',
                "participant_position": user.rol.detalle_rol,
                "participant_signature": user.signature,
                "participant_rating": participant.rating or 'No calificación'
            })

        return {
            "form_event": [
                {
                    "event_data": {
                        'event_name': self.event_name,
                        'event_record_number': self.event_record_number,
                        'event_date': self.event_date,
                        'event_start_date': self.event_start_date,
                        'event_end_date': self.event_end_date,
                        'event_place': self.event_place,
                        'event_aim': self.event_aim,
                        'event_issue': self.event_issue,
                        'event_agenda': self.event_agenda,
                        'event_development': self.event_development,
                        'event_responsible_id': self.event_responsible.num_documento if self.event_responsible else None
                    },
                    "event_participants": participant_details,
                    "event_guests": list(self.guests.values()),
                    "event_actions": list(self.actions.values()),
                    "event_evidence": list(self.evidences.values()),
                    "event_evaluation_id": self.event_evaluation.id_evaluation if self.event_evaluation else None,
                    "event_required_roles": [role.id_rol for role in self.event_required_roles.all()],
                    "training_category": self.event_training_category.tr_ctg_abbreviation if self.event_training_category else "Sin Categoría"
                }
            ]
        }

    def get_event_attendance(self):
        participants = self.participants.select_related('colaborador')

        duration = self.event_end_date - self.event_start_date if self.event_end_date and self.event_start_date else None
        hours, minutes = (divmod(duration.total_seconds() // 60, 60) if duration else (0, 0))

        responsable = self.event_responsible
        event_city = self.event_place.headquerters_city if self.event_place else 'Ciudad no disponible'
        
        return {
            "form_event": [
                {
                    "event_date": self.event_date,
                    "event_attendance": self.event_aim,
                    "event_responsible_name": f'{responsable.nombres} {responsable.apellidos}' if responsable else 'Responsable no encontrado',
                    "event_responsible_role": responsable.rol.detalle_rol if responsable else 'Rol no disponible',
                    "event_responsible_department": responsable.rol.department.department_name if responsable else 'Departamento no disponible',
                    "event_responsible_signature": responsable.signature if responsable else 'Firma no disponible',
                    "event_issue": self.event_issue,
                    "event_duration": f"{duration.days} días, {int(hours)} horas, {int(minutes)} minutos" if duration else 'Duración no disponible',
                    "event_city": event_city,
                    "event_participants": [
                        {
                            "participant_num_documento": colaborador.num_documento,
                            "participant_name": f'{colaborador.apellidos} {colaborador.nombres}',
                            "participant_position": colaborador.rol.detalle_rol,
                            "participant_signature": colaborador.signature,
                            "participant_rating": participant.rating or 'No calificación'
                        }
                        for participant in participants
                        for colaborador in [participant.colaborador]
                    ]
                }
            ]
        }

    def get_event_attendance_drivers(self):
        participants = self.participants.select_related('colaborador')
        colaboradores_con_vehiculo = Colaboradores.objects.filter(
            num_documento__in=participants.values_list('colaborador__num_documento', flat=True),
            vehiculo__isnull=False
        )

        duration = self.event_end_date - self.event_start_date if self.event_end_date and self.event_start_date else None
        hours, minutes = (divmod(duration.total_seconds() // 60, 60) if duration else (0, 0))

        responsable = self.event_responsible
        event_city = self.event_place.headquerters_city if self.event_place else 'Ciudad no disponible'

        return {
            "form_event": [
                {
                    "event_date": self.event_date,
                    "event_attendance": self.event_aim,
                    "event_responsible_name": f'{responsable.nombres} {responsable.apellidos}' if responsable else 'Responsable no encontrado',
                    "event_responsible_role": responsable.rol.detalle_rol if responsable else 'Rol no disponible',
                    "event_responsible_department": responsable.rol.department.department_name if responsable else 'Departamento no disponible',
                    "event_responsible_signature": responsable.signature if responsable else 'Firma no disponible',
                    "event_issue": self.event_issue,
                    "event_duration": f"{duration.days} días, {int(hours)} horas, {int(minutes)} minutos" if duration else 'Duración no disponible',
                    "event_city": event_city,
                    "event_participants": [
                        {
                            "participant_num_documento": colaborador.num_documento,
                            "participant_name": f'{colaborador.apellidos} {colaborador.nombres}',
                            "participant_position": colaborador.rol.detalle_rol,
                            "participant_signature": colaborador.signature,
                            "vehicle_plate": colaborador.vehiculo.placa,
                            "participant_rating": participant.rating or 'No calificación'
                        }
                        for participant in participants
                        for colaborador in [participant.colaborador]
                        if colaborador in colaboradores_con_vehiculo
                    ]
                }
            ]
        }

class EventParticipant(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    colaborador = models.ForeignKey(Colaboradores, on_delete=models.CASCADE)
    rating = models.CharField(max_length=255, null=True, blank=True)
    fecha = models.DateField(null=True, blank=True)

class EventGuest(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='guests')
    guest_name = models.CharField(max_length=255)
    guest_company = models.CharField(max_length=255, null=True, blank=True)
    guest_position = models.CharField(max_length=255, null=True, blank=True)
    guest_signature = models.TextField(null=True, blank=True)

class EventAction(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='actions')
    action_name = models.CharField(max_length=255)
    action_deadline = models.DateField(null=True, blank=True)
    action_responsible = models.CharField(max_length=255)

class EventEvidence(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='evidences')
    evidence_file = models.FileField(upload_to='event_evidences/', null=True, blank=True)
    evidence_type = models.CharField(max_length=100, null=True, blank=True)  # Añadido para almacenar el tipo de archivo

class Agenda(models.Model):
    AGENDA_TYPES = [
        ('work', 'Horario Laboral'),
        ('event', 'Evento'),
    ]

    agenda_colaborador = models.ForeignKey(Colaboradores, on_delete=models.CASCADE)
    agenda_title = models.CharField(max_length=255)
    agenda_start_date = models.DateField()
    agenda_end_date = models.DateField()
    agenda_start_time = models.TimeField()
    agenda_end_time = models.TimeField()
    agenda_color = models.CharField(max_length=7)
    agenda_type = models.CharField(max_length=10, choices=AGENDA_TYPES, default='event')

class Parte(models.Model):
    id_parte = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
class Pregunta(models.Model):
    parte = models.ForeignKey(Parte, on_delete=models.CASCADE)
    texto = models.TextField(blank=True, null=True)
    opciones = models.JSONField()
    respuesta_correcta = models.CharField(max_length=1)
    
    imagen = models.ImageField(upload_to='imagenes_preguntas/', blank=True, null=True)
    video = models.FileField(upload_to='videos_preguntas/', blank=True, null=True)
class RespuestaUsuario(models.Model):
    usuario = models.ForeignKey(Colaboradores, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    respuesta_seleccionada = models.CharField(max_length=1)
    es_correcta = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.es_correcta = self.respuesta_seleccionada == self.pregunta.respuesta_correcta
        super().save(*args, **kwargs)

class ResultadoParte(models.Model):
    usuario = models.ForeignKey(Colaboradores, on_delete=models.CASCADE)
    parte = models.ForeignKey(Parte, on_delete=models.CASCADE)
    calificacion = models.FloatField()
class CalificacionTotal(models.Model):
    usuario = models.ForeignKey(Colaboradores, on_delete=models.CASCADE)
    promedio = models.FloatField()
class InductionDoc(models.Model):
    cedula_empleado = models.ForeignKey(Colaboradores, on_delete=models.CASCADE)
    responsable_induccion = models.ForeignKey(Colaboradores, on_delete=models.DO_NOTHING, null=True, related_name='docs_responsable')
    vfanswers = models.JSONField(default=dict, blank=True)
    vfanswers2 = models.JSONField(default=dict, blank=True)
    vfanswers3 = models.JSONField(default=dict, blank=True)
    abcanswers = models.JSONField(default=dict, blank=True)
    abcanswers2 = models.JSONField(default=dict, blank=True)
    abcanswers3 = models.JSONField(default=dict, blank=True)
    
    lugar = models.ForeignKey(Headquarters, on_delete=models.DO_NOTHING, null=True)
    fecha = models.DateField(auto_now=True)
    horafin_social = models.TimeField(null=True, blank=True)
    horafin_pesv = models.TimeField(null=True, blank=True)
    observaciones_vi = models.TextField(blank=True, null=True)
    observaciones_iv = models.TextField(blank=True, null=True)
    
    cumplimiento_objetivos = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    claridad_conceptos = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    desarrollo_personal = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    trabajo_actual = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    conocimiento_tema = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True, default='')
    habilidades_comunicacion = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    capacidad_orientar = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True, default='')
    transmision_ideas = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    manejo_tiempo = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True, default='')
    generacion_empatia = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    puntualidad = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    material_usado = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    recursos_empleados = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    instalaciones = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    aspectos_logisticos = models.CharField(max_length=1, choices=[('E', 'Excelente'), ('B', 'Bueno'), ('R', 'Regular'), ('D', 'Deficiente')], null=True, blank=True)
    
    sino1 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True)
    sino2 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True)
    sino3 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True)
    sino4 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino5 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino6 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino7 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino8 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino9 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino10 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino11 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino12 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino13 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino14 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino15 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino16 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino17 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino18 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    sino19 = models.CharField(max_length=3, choices=[('Sí', 'Sí'), ('No', 'No')], null=True, blank=True, default='')
    
    firma_empleado = models.TextField(blank=True, null=True)
    firma_capacitador = models.TextField(blank=True, null=True)
    huella_soci2 = models.TextField(blank=True, null=True)
    ciudadFecha = models.CharField(max_length=255, blank=True, null=True)
    
    nombre_autorizacion = models.CharField(max_length=255, blank=True, null=True)
    firma_autorizacion = models.TextField(blank=True, null=True)
    ciudad_fecha_autorizacion = models.CharField(max_length=255, blank=True, null=True)

QUESTION_TYPES = [
    ('text', 'Text'),
    ('question', 'Question'),
    ('headerWithImage', 'Header with Image'),
    ('headerWithOptions', 'Header with Options'),
    ('imageOptions', 'Image with Options'),
]

class Test(models.Model):
    title = models.CharField(max_length=255, verbose_name="Título de la Evaluación")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción de la Evaluación")
    created_at = models.DateTimeField(auto_now_add=True)

class Section2(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=255, verbose_name="Título de la Sección")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción de la Sección")
    
class Question2(models.Model):
    section = models.ForeignKey(Section2, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField("Enunciado de la Pregunta", null=True)
    type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='question')
    description = models.TextField("Descripción", blank=True, null=True)
    image_src = models.URLField("URL de la Imagen", blank=True, null=True)
    options = models.JSONField("Opciones", blank=True, null=True)
    correct_answer = models.CharField("Respuesta Correcta", max_length=100, blank=True, null=True)
    correct_answers = models.JSONField(null=True, blank=True)
    images = ArrayField(models.CharField(max_length=455), null=True)

class TestDrivers(models.Model):
    id_test_driver = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    colaborador_evaluador = models.ForeignKey(Colaboradores, on_delete=models.DO_NOTHING, null=True)
    name_driver = models.CharField(max_length=255, null=True)
    dni_driver = models.CharField(max_length=15, null=True)
    empresa_solicitante = models.ForeignKey(Empresas, on_delete=models.DO_NOTHING)
    vehiculo = models.ForeignKey(Vehiculos, null=True, on_delete=models.DO_NOTHING)
    lugar = models.ForeignKey(Headquarters, on_delete=models.DO_NOTHING)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)
    resultados = models.JSONField(default=dict)
    observaciones = models.JSONField(default=dict)
    recomendacion = models.BooleanField(default=False)
    calificaciones = models.JSONField(default=dict)
    license_category = models.CharField(max_length=5, null=True)
    experience_time = models.CharField(max_length=20, null=True)
    signature_driver = models.TextField(blank=True, null=True)

class TestDriversSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluator = models.ForeignKey(Colaboradores, on_delete=models.DO_NOTHING)
    evaluation_request = models.ForeignKey(TestDrivers, on_delete=models.DO_NOTHING)
    data = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)

    def fetch_session_details(self):
        driver_details = self.evaluation_request
        driver_name = driver_details.name_driver
        driver_dni = driver_details.dni_driver

        empresa_details = driver_details.empresa_solicitante
        empresa_name = empresa_details.nombre_empresa

        vehicle_details = driver_details.vehiculo
        vehicle_placa = vehicle_details.placa

        headquarters_details = driver_details.lugar
        city = headquarters_details.headquerters_city
        location = headquarters_details.headquarters_name

        session_info = {
            'driver_name': driver_name,
            'driver_dni': driver_dni,
            'bussines_name': empresa_name,
            'vehicle_placa': vehicle_placa,
            'city': city,
            'location': location
        }

        return session_info

class TestSessionResponses(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(TestDrivers, on_delete=models.DO_NOTHING)
    responses = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
class WrittenTest(models.Model):
    id_written_test = models.UUIDField(primary_key=True, default=uuid.uuid4)
    test_driver = models.ForeignKey(TestDrivers, on_delete=models.DO_NOTHING)
    scores = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
class WrittenTestSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluation_request = models.ForeignKey(TestDrivers, on_delete=models.DO_NOTHING)
    user_responses = models.JSONField(default=dict)
    current_section = models.IntegerField(default=0)
    score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class ConversationSession(models.Model):
    user_phone = models.CharField(max_length=50)
    current_flow = models.CharField(max_length=100, default="", blank=True)
    current_step = models.CharField(max_length=100, default="START", blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

class ConversationMessage(models.Model):
    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField()
    is_user = models.BooleanField(default=True)
    intent = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)



class EnteAtencion(models.Model):
    nombre = models.CharField(max_length=100)

class ProcesoDefinicion(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    codigoProceso = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class EtapaDefinicion(models.Model):
    proceso_definicion = models.ForeignKey(ProcesoDefinicion, related_name='etapas', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    codigoEtapa = models.CharField(max_length=50, blank=True, null=True)
    orden = models.PositiveIntegerField()

    class Meta:
        ordering = ['orden']
        unique_together = [('proceso_definicion', 'nombre'), ('proceso_definicion', 'orden')]

    def __str__(self):
        return f"{self.proceso_definicion.nombre} - {self.nombre}"

class SubEtapaDefinicion(models.Model):
    etapa_definicion = models.ForeignKey(EtapaDefinicion, related_name='sub_etapas', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    codigoSubEtapa = models.CharField(max_length=50, blank=True, null=True)
    orden = models.PositiveIntegerField()

    class Meta:
        ordering = ['orden']
        unique_together = [('etapa_definicion', 'nombre'), ('etapa_definicion', 'orden')]

    def __str__(self):
        return f"{self.etapa_definicion.nombre} - {self.nombre}"

class ActuacionDefinicion(models.Model):
    sub_etapa_definicion = models.ForeignKey(SubEtapaDefinicion, related_name='actuaciones', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    terminaProceso = models.BooleanField(default=False)
    estadoResultado = models.CharField(max_length=100, blank=True, null=True)
    codigoActuacion = models.CharField(max_length=50, blank=True, null=True)
    orden = models.PositiveIntegerField()

    class Meta:
        ordering = ['orden']
        unique_together = [('sub_etapa_definicion', 'nombre'), ('sub_etapa_definicion', 'orden')]

    def __str__(self):
        return self.nombre

class Siniestro(models.Model):
    TIPO_EVENTO_CHOICES = [
        ('Siniestro', 'Siniestro'),
        ('Incidente', 'Incidente'),
    ]
    GRAVEDAD_CHOICES = [
        ('Heridos', 'Heridos'),
        ('Choque simple', 'Choque simple'),
        ('Muertos', 'Muertos'),
        ('Heridos y muertos', 'Heridos y muertos'),
    ]
    ZONA_CHOICES = [
        ('Rural', 'Rural'),
        ('Urbana', 'Urbana'),
    ]
    descripcion = models.TextField(null=True, blank=True)
    tipo_evento = models.CharField(max_length=20, choices=TIPO_EVENTO_CHOICES, default='Incidente')
    gravedad = models.CharField(max_length=20, choices=GRAVEDAD_CHOICES, default='Choque simple')
    entes_atendieron = models.ManyToManyField(EnteAtencion, related_name='siniestros_atendidos', blank=True)
    latitud = models.DecimalField(max_digits=22, decimal_places=19, null=True, blank=True)
    longitud = models.DecimalField(max_digits=22, decimal_places=19, null=True, blank=True)
    zona = models.CharField(max_length=10, choices=ZONA_CHOICES, default='Rural')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    colaborador = models.ForeignKey('Colaboradores', on_delete=models.CASCADE, related_name='siniestros_colaborador', null=True, blank=True)
    vehiculo = models.ForeignKey('Vehiculos', on_delete=models.CASCADE, null=True, blank=True, related_name='siniestros_vehiculo')
    empresa = models.ForeignKey('Empresas', on_delete=models.CASCADE, related_name='siniestros_empresa', null=True, blank=True)
    ipat = models.BooleanField(default=False)
    inmovilizacion = models.BooleanField(default=False)
    direccion_text = models.TextField(null=True, blank=True)
    proceso_estado_general = models.OneToOneField('SiniestroProceso', on_delete=models.SET_NULL, null=True, blank=True, related_name='siniestro_directo')
    datos_adicionales = models.JSONField(default=dict, blank=True)

    @property
    def numero_victimas_calculado(self):
        return self.victimas.count()

    def __str__(self):
        return f"Siniestro {self.id} - {self.tipo_evento}"

class SiniestroProceso(models.Model):
    ESTADO_GENERAL_CHOICES = [
        ('no_iniciado', 'No Iniciado'),
        ('en_progreso', 'En Progreso'),
        ('terminado', 'Terminado'),
    ]
    siniestro = models.OneToOneField(Siniestro, related_name='proceso_detalle_siniestro', on_delete=models.CASCADE)
    proceso_definicion_actual = models.ForeignKey(ProcesoDefinicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='siniestros_procesos_actuales')
    etapa_definicion_actual = models.ForeignKey(EtapaDefinicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='siniestros_etapas_actuales')
    sub_etapa_definicion_actual = models.ForeignKey(SubEtapaDefinicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='siniestros_subetapas_actuales')
    actuacion_definicion_siguiente = models.ForeignKey(ActuacionDefinicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='siniestros_actuaciones_siguientes')
    estado_general = models.CharField(max_length=20, choices=ESTADO_GENERAL_CHOICES, default='no_iniciado')
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Proceso Siniestro {self.siniestro_id} - Estado: {self.get_estado_general_display()}"

class SiniestroHistorialActuacion(models.Model):
    STATUS_CHOICES = [
        ('completada', 'Completada'),
        ('omitida_temporalmente', 'Omitida Temporalmente'),
        ('omitida_permanentemente', 'Omitida Permanentemente'),
        ('en_espera', 'En Espera'),
        ('pendiente', 'Pendiente')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    siniestro_proceso = models.ForeignKey(SiniestroProceso, related_name='historial_actuaciones_siniestro', on_delete=models.CASCADE)
    actuacion_definicion = models.ForeignKey(ActuacionDefinicion, on_delete=models.CASCADE, related_name='historial_siniestros')
    fecha_actuacion = models.DateField()
    fecha_vigencia = models.DateField(null=True, blank=True)
    notas = models.TextField(blank=True, null=True)
    documento = models.FileField(upload_to='documentos_actuaciones_siniestros/', null=True, blank=True)
    documento_nombre_original = models.CharField(max_length=255, blank=True, null=True)
    timestamp_registro = models.DateTimeField(auto_now_add=True)
    status_actuacion = models.CharField(max_length=30, choices=STATUS_CHOICES)
    resuelve_omision_de = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='accion_resolutoria_siniestro')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='historial_siniestros_creados')

    def __str__(self):
        return f"Historial Siniestro {self.id} para {self.siniestro_proceso.siniestro_id} - Actuación: {self.actuacion_definicion.nombre}"

class DocumentoSiniestroHistorialActuacion(models.Model):
    siniestro_historial_actuacion = models.ForeignKey(SiniestroHistorialActuacion, related_name='documentos', on_delete=models.CASCADE)
    documento = models.FileField(upload_to='documentos_actuaciones_siniestros/', null=True, blank=True)
    documento_nombre_original = models.CharField(max_length=255, blank=True, null=True)
    timestamp_registro = models.DateTimeField(auto_now_add=True)

class Ipat(models.Model):
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, related_name='ipat_record')
    clase_evento = models.CharField(max_length=100)
    clase_evento_otro = models.CharField(max_length=100, null=True, blank=True)
    choque_con = models.CharField(max_length=100, null=True, blank=True)
    clase_vehiculo = models.CharField(max_length=100, null=True, blank=True)
    objeto_fijo = models.CharField(max_length=100, null=True, blank=True)
    alineacion_horizontal = models.CharField(max_length=100, null=True, blank=True)
    alineacion_vertical = models.CharField(max_length=100, null=True, blank=True)
    utilizacion_vial = models.CharField(max_length=50,  null=True, blank=True)
    calzadas = models.IntegerField(null=True, blank=True)
    carriles = models.CharField(max_length=20,  null=True, blank=True)
    superficie_rodadura = models.CharField(max_length=50,  null=True, blank=True)
    superficie_rodadura_otro = models.CharField(max_length=100, null=True, blank=True)
    condicion_vial = models.CharField(max_length=50,  null=True, blank=True)
    condicion_vial_otra = models.CharField(max_length=100, null=True, blank=True)
    iluminacion = models.CharField(max_length=10,  null=True, blank=True)
    iluminacion_detalle = models.CharField(max_length=20,  null=True, blank=True)
    area = models.JSONField(default=list, blank=True, null=True)
    sector = models.JSONField(default=list, blank=True, null=True)
    zona = models.JSONField(default=list, blank=True, null=True)
    condicion_climatica = models.JSONField(default=list, blank=True, null=True)
    diseno_via = models.JSONField(default=list)
    opciones_geometricas = models.JSONField(default=list, blank=True, null=True)
    lugar_impacto = models.JSONField(default=list)
    elementos_laterales = models.JSONField(default=list, blank=True, null=True)
    estado_vial = models.JSONField(default=list, blank=True, null=True)
    impact_visual = models.JSONField(default=list)
    impact_visual_svg = models.FileField( upload_to='ipat_svgs/', null=True, blank=True)
    impact_visual_lines = models.JSONField(default=dict)
    croquis_lines = models.JSONField(default=list, blank=True, null=True)
    controles_transito = models.JSONField(default=list, blank=True, null=True)
    control_items = models.JSONField(default=dict, blank=True, null=True)
    control_other = models.JSONField(default=dict, blank=True, null=True)
    control_sub_items = models.JSONField(default=dict, blank=True, null=True)
    testigos = models.JSONField(default=list, blank=True, null=True)
    interrogatorio_conductor = models.JSONField(default=list, blank=True, null=True)
    hipotesis_conductor = models.JSONField(default=list, blank=True, null=True)
    hipotesis_vehiculo = models.JSONField(default=list, blank=True, null=True)
    hipotesis_via = models.JSONField(default=list, blank=True, null=True)
    hipotesis_peaton = models.JSONField(default=list, blank=True, null=True)
    hipotesis_pasajero = models.JSONField(default=list, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

class SiniestroMedia(models.Model):
    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE, related_name='media')
    file_url = models.CharField(max_length=255)
    tipo = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SiniestroLog(models.Model):
    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey('Colaboradores', on_delete=models.SET_NULL, null=True, related_name='logs_siniestro_user')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    media = models.ForeignKey(SiniestroMedia, on_delete=models.SET_NULL, null=True, blank=True, related_name='log_media')

class Tercero(models.Model):
    siniestro = models.ForeignKey('Siniestro', on_delete=models.CASCADE, related_name='terceros')
    nombre_completo = models.CharField(max_length=200)
    cedula = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(max_length=150, null=True, blank=True)
    licencia_conduccion = models.FileField(upload_to='licencias/', max_length=255, null=True, blank=True)
    licencia_transito = models.FileField(upload_to='licencias/', max_length=255, null=True, blank=True)
    audio_version = models.CharField(max_length=255, null=True, blank=True)
    fotos_seguro = models.FileField(upload_to='seguros/', null=True, blank=True)
    propietario = models.CharField(max_length=200, null=True, blank=True)
    cedula_propietario = models.CharField(max_length=20)
    direccion_propietario = models.CharField(max_length=200, null=True, blank=True)
    correo_propietario = models.EmailField(max_length=150, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

class ActaConciliacion(models.Model):
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, related_name='acta_conciliacion')
    nombre_completo_conductor1 = models.CharField(max_length=200, null=True, blank=True)
    cedula_conductor1 = models.CharField(max_length=20, null=True, blank=True)
    placa_conductor1 = models.CharField(max_length=10, null=True, blank=True)
    firma_conductor1 = models.TextField(null=True, blank=True)
    nombre_completo_conductor2 = models.CharField(max_length=200, null=True, blank=True)
    cedula_conductor2 = models.CharField(max_length=20, null=True, blank=True)
    placa_conductor2 = models.CharField(max_length=10, null=True, blank=True)
    telefono_conductor2 = models.CharField(max_length=15, null=True, blank=True)
    email_conductor2 = models.CharField(max_length=256, null=True, blank=True)
    firma_conductor2 = models.TextField(null=True, blank=True)
    suma_a_pagar = models.CharField(max_length=15, null=True, blank=True)
    conciliacion_lograda = models.BooleanField(default=False)
    conciliacion_por_conciliador = models.FileField(upload_to='conciliaciones/', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    pdf_conciliacion = models.CharField(null=True, blank=True)

class Victima(models.Model):
    TIPO_CHOICES = [
        ('herido', 'Herido'),
        ('fatal', 'Fatal'),
    ]
    siniestro = models.ForeignKey(Siniestro, related_name='victimas', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=255)
    cedula = models.CharField(max_length=20)
    contacto = models.CharField(max_length=20)
    nombreContacto = models.CharField(max_length=255, blank=True, null=True)
    parentesco = models.CharField(max_length=50, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()}) - Siniestro {self.siniestro_id}"

class VictimaProceso(models.Model):
    ESTADO_GENERAL_CHOICES = [
        ('no_iniciado', 'No Iniciado'),
        ('en_progreso', 'En Progreso'),
        ('terminado', 'Terminado'),
    ]
    victima = models.OneToOneField(Victima, related_name='proceso_estado', on_delete=models.CASCADE)
    proceso_definicion_actual = models.ForeignKey(ProcesoDefinicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='victima_procesos_actuales')
    etapa_definicion_actual = models.ForeignKey(EtapaDefinicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='victima_etapas_actuales')
    sub_etapa_definicion_actual = models.ForeignKey(SubEtapaDefinicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='victima_subetapas_actuales')
    actuacion_definicion_siguiente = models.ForeignKey(ActuacionDefinicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='victima_actuaciones_siguientes')
    estado_general = models.CharField(max_length=20, choices=ESTADO_GENERAL_CHOICES, default='no_iniciado')
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Proceso de {self.victima.nombre} - Estado: {self.get_estado_general_display()}"

class HistorialActuacion(models.Model):
    STATUS_CHOICES = [
        ('completada', 'Completada'),
        ('omitida_temporalmente', 'Omitida Temporalmente'),
        ('omitida_permanentemente', 'Omitida Permanentemente'),
        ('en_espera', 'En Espera'),
        ('pendiente', 'Pendiente')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    victima_proceso = models.ForeignKey(VictimaProceso, related_name='historial_actuaciones', on_delete=models.CASCADE)
    actuacion_definicion = models.ForeignKey(ActuacionDefinicion, on_delete=models.CASCADE, related_name='historial_victimas')
    fecha_actuacion = models.DateField()
    fecha_vigencia = models.DateField(null=True, blank=True)
    notas = models.TextField(blank=True, null=True)
    documento = models.FileField(upload_to='documentos_actuaciones/', null=True, blank=True)
    documento_nombre_original = models.CharField(max_length=255, blank=True, null=True)
    timestamp_registro = models.DateTimeField(auto_now_add=True)
    status_actuacion = models.CharField(max_length=30, choices=STATUS_CHOICES)
    resuelve_omision_de = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='accion_resolutoria')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='historial_victimas_creados')


    def __str__(self):
        return f"Historial {self.id} para {self.victima_proceso.victima.nombre} - Actuación: {self.actuacion_definicion.nombre}"
