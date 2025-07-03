# myapp/management/commands/sync_vehicles_from_validators.py

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from django.utils import timezone
import math
import re
import logging
import unicodedata # <--- Añadir import

# Importar todos los modelos necesarios
from myapp.models import (
    TipoDocumento, Empresas, Vehiculos, Propietario, Marca, TipoLinea,
    ClaseVehiculo, Carroceria, Combustible, TipoOperacion, Ciudad, NivelServicio,
    Categoria, Color, VehiculoPropietario, Servicio, Tenedor, VehiculoTenedor,
    Aseguradora, TipoDocumentoVehiculo,
    Soat, RevisionTecnomecanica, TarjetaOperacion,
    PolizaContractual, PolizaExtracontractual, PolizaTodoRiesgo,
    FichaTecnicaHomologacionChasis, FichaTecnicaHomologacionCarroceria,
    FichaTecnicaHomologacionVehCarrozado, LicenciaTransito
)
from django.db.models import Q # Asegurarse que Q esté importado

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Helper Functions (Incluye normalización) ---

def normalize_text(text):
    """Convierte a minúsculas y remueve acentos/diacríticos."""
    if text is None:
        return None
    try:
        text = str(text)
        # Normalizar a NFD (Canonical Decomposition) y filtrar caracteres no base (diacríticos)
        text = ''.join(c for c in unicodedata.normalize('NFD', text)
                       if unicodedata.category(c) != 'Mn')
        return text.lower().strip()
    except Exception:
        # Fallback si algo raro pasa con la normalización
        return str(text).lower().strip()

def safe_get(row_or_series, key, default=None):
    # (Sin cambios)
    try:
        if hasattr(row_or_series, 'get'): val = row_or_series.get(key)
        elif key in row_or_series.index: val = row_or_series[key]
        else: return default
        if pd.isna(val) or val is None: return default
        if isinstance(val, float) and math.isnan(val): return default
        return val
    except (KeyError, IndexError, AttributeError): return default

def to_str_or_none(value):
    # (Sin cambios)
    if pd.isna(value) or value is None or str(value).strip().upper() == 'NULL': return None
    s_val = str(value).strip()
    return s_val if s_val else None

def to_int_or_none(value):
    # (Sin cambios)
    if pd.isna(value) or value is None or str(value).strip().upper() == 'NULL': return None
    try:
        s_value = str(value)
        cleaned_value = s_value.split('.')[0] if '.' in s_value else s_value
        return int(cleaned_value)
    except (ValueError, TypeError): return None

def to_date_or_none(value):
    # (Sin cambios) - Asegurarse que maneje bien los formatos de fecha de Excel
    if pd.isna(value) or value is None or str(value).strip().upper() in ['NULL', '00:00.0', '']: return None
    try:
        if isinstance(value, pd.Timestamp): return value.date()
        if isinstance(value, (int, float)) and value > 20000:
            return (pd.Timestamp('1899-12-30') + pd.Timedelta(days=value)).date()
        dt = pd.to_datetime(value, errors='coerce', dayfirst=False)
        if pd.isna(dt):
            dt = pd.to_datetime(value, errors='coerce', dayfirst=True)
        return dt.date() if pd.notna(dt) else None
    except (ValueError, TypeError, OverflowError): return None

def parse_propietario_name(full_name_str):
    # (Sin cambios)
    if not full_name_str: return None, None
    parts = str(full_name_str).strip().split()
    if not parts: return None, None
    if len(parts) >= 2:
        nombres = parts[0]
        apellidos = " ".join(parts[1:])
    else:
        nombres = parts[0]
        apellidos = None
    return nombres, apellidos

# --- Funciones de Búsqueda/Creación FK Mejoradas ---

def get_or_create_fk_normalized(model, cache, search_value_orig, field_name='nombre'):
    """
    Busca en caché o BD (insensible a mayús/acentos) o crea un objeto FK.
    Usa el nombre original para crear, pero el normalizado para caché y búsqueda inicial.
    """
    if search_value_orig is None: return None
    search_value_str = str(search_value_orig).strip()
    if not search_value_str: return None

    normalized_key = normalize_text(search_value_str)
    if not normalized_key: return None # Si la normalización falla o resulta vacía

    # 1. Buscar en caché (con clave normalizada)
    if normalized_key in cache:
        return cache[normalized_key]

    # 2. Buscar en BD (insensible a mayúsculas/acentos)
    # Nota: Esto requiere que el modelo y la BD lo soporten idealmente (ej: unaccent)
    # Como fallback, usamos iexact y luego podríamos filtrar en Python si fuera necesario,
    # pero para simplificar, confiaremos en iexact y crearemos si no se encuentra.
    try:
        # Intenta búsqueda exacta insensible a mayúsculas primero
        obj = model.objects.get(**{f'{field_name}__iexact': search_value_str})
        cache[normalized_key] = obj # Guardar en caché con clave normalizada
        return obj
    except model.DoesNotExist:
        # 3. Si no existe, Crear
        try:
            # Crear usando el valor original (sin normalizar, solo strip)
            obj = model.objects.create(**{field_name: search_value_str})
            cache[normalized_key] = obj # Guardar en caché con clave normalizada
            logger.info(f"Creado nuevo registro en {model.__name__}: '{search_value_str}'")
            return obj
        except Exception as e:
            logger.error(f"Error creando registro en {model.__name__} para '{search_value_str}': {e}")
            # Intentar buscar de nuevo por si hubo una race condition o un error al crear pero ya existía
            try:
                 obj = model.objects.get(**{f'{field_name}__iexact': search_value_str})
                 cache[normalized_key] = obj
                 return obj
            except Exception:
                 return None # Falló la creación y la re-búsqueda
    except model.MultipleObjectsReturned:
        logger.warning(f"Múltiples registros encontrados en {model.__name__} para {field_name}__iexact='{search_value_str}'. Usando el primero.")
        obj = model.objects.filter(**{f'{field_name}__iexact': search_value_str}).first()
        if obj:
             cache[normalized_key] = obj
        return obj
    except Exception as e:
        logger.error(f"Error buscando/creando FK en {model.__name__} para '{search_value_str}': {e}")
        return None

def get_ciudad_normalized(cache, nombre_ciudad_orig, nombre_dpto_orig):
    """Busca o crea una ciudad, insensible a mayús/acentos."""
    nc_orig = to_str_or_none(nombre_ciudad_orig)
    nd_orig = to_str_or_none(nombre_dpto_orig)
    if not nc_orig: return None

    nc_norm = normalize_text(nc_orig)
    nd_norm = normalize_text(nd_orig) if nd_orig else None

    # Crear una clave única normalizada para el caché
    cache_key = f"{nc_norm}|{nd_norm or 'NULL'}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        # Filtro con iexact para nombres
        q_filter = Q(nombre__iexact=nc_orig)
        if nd_orig:
            q_filter &= Q(departamento__iexact=nd_orig)
        else:
            # Si no hay departamento, buscar los que tengan departamento nulo o vacío
            q_filter &= (Q(departamento__isnull=True) | Q(departamento=''))

        ciudad_obj = Ciudad.objects.get(q_filter)
        cache[cache_key] = ciudad_obj
        return ciudad_obj
    except Ciudad.DoesNotExist:
        try:
            # Crear usando los nombres originales (stripped)
            ciudad_obj = Ciudad.objects.create(nombre=nc_orig, departamento=nd_orig)
            cache[cache_key] = ciudad_obj
            logger.info(f"Ciudad creada: '{nc_orig}' ({nd_orig or 'N/A'})")
            return ciudad_obj
        except Exception as e:
            logger.error(f"Error creando ciudad '{nc_orig}' ({nd_orig or 'N/A'}): {e}")
            # Reintentar búsqueda por si acaso
            try:
                ciudad_obj = Ciudad.objects.get(q_filter)
                cache[cache_key] = ciudad_obj
                return ciudad_obj
            except Exception:
                return None
    except Ciudad.MultipleObjectsReturned:
        logger.warning(f"Múltiples ciudades encontradas para '{nc_orig}' ({nd_orig or 'N/A'}). Usando la primera.")
        ciudad_obj = Ciudad.objects.filter(q_filter).first()
        if ciudad_obj:
             cache[cache_key] = ciudad_obj
        return ciudad_obj
    except Exception as e:
         logger.error(f"Error buscando/creando ciudad '{nc_orig}' ({nd_orig or 'N/A'}): {e}")
         return None

# --- Mapeo de Empresas Validador 1 ---
EMPRESA_MAP_V1 = {
    "BERLINASTUR S.A.": 4,
    "BERLITUR S.A.S": 5,
    "CIT": 2, # Asumiendo que 'CIT' en el Excel es ID 2
    "TOURLINE EXPRESS S.A.S": 6,
}

class Command(BaseCommand):
    help = 'Sincroniza vehículos desde validadores: elimina los no presentes y crea/actualiza (buscando FKs existentes sin importar mayus/tildes).'

    def add_arguments(self, parser):
        parser.add_argument('validator1_file', type=str, help='Ruta al archivo validator.xlsx')
        parser.add_argument('validator2_file', type=str, help='Ruta al archivo validator2.xlsx')

    @transaction.atomic
    def handle(self, *args, **options):
        validator1_path = options['validator1_file']
        validator2_path = options['validator2_file']

        logger.info("--- Iniciando Sincronización de Vehículos desde Validadores (Normalizada) ---")

        # --- 1. Cargar Datos de Prerrequisito (Cachés) ---
        logger.info("Cargando datos de prerrequisito (Empresas, Tipos, Aseguradoras)...")
        try:
            empresas_cache_id = {e.id: e for e in Empresas.objects.all()}
            # No necesitamos caché por nombre para empresa V1 si usamos el mapeo directo
            # Crear caché normalizado para Aseguradoras
            aseguradoras_cache_norm = {normalize_text(a.nombre): a for a in Aseguradora.objects.all()}
            tipo_doc_veh_cache = {tdv.id: tdv for tdv in TipoDocumentoVehiculo.objects.all()}
            tipo_doc_persona_cc = TipoDocumento.objects.get(id=1) # Cédula

            # Cachés para FKs simples (se llenarán sobre la marcha con claves normalizadas)
            marcas_cache = {}
            lineas_cache = {}
            clasesv_cache = {}
            carrocerias_cache = {}
            combustibles_cache = {}
            ciudades_cache = {} # Usará get_ciudad_normalized
            colores_cache = {}
            tipo_op_cache = {}

        except Exception as e:
            raise CommandError(f"Error cargando datos de prerrequisito: {e}")

        # --- 2. Cargar Datos de Validadores ---
        # (Sin cambios en esta sección, carga los datos en validator_data)
        logger.info("Cargando datos desde archivos validadores...")
        validator_data = {}
        try:
            df_val1 = pd.read_excel(validator1_path, sheet_name=0)
            logger.info(f"Leyendo {len(df_val1)} filas de {validator1_path}")
            for index, row in df_val1.iterrows():
                placa = to_str_or_none(safe_get(row, 'PLACA'))
                if placa:
                    placa_norm = placa.strip().upper()
                    validator_data[placa_norm] = {'data': row, 'source': 'v1'}
        except Exception as e:
            raise CommandError(f"Error fatal leyendo {validator1_path}: {e}")

        try:
            df_val2 = pd.read_excel(validator2_path, sheet_name=0)
            logger.info(f"Leyendo {len(df_val2)} filas de {validator2_path}")
            for index, row in df_val2.iterrows():
                placa = to_str_or_none(safe_get(row, 'PLACA'))
                if placa:
                    placa_norm = placa.strip().upper()
                    validator_data[placa_norm] = {'data': row, 'source': 'v2'} # V2 sobreescribe V1
        except Exception as e:
            raise CommandError(f"Error fatal leyendo {validator2_path}: {e}")

        all_validator_plates = set(validator_data.keys())
        logger.info(f"Total placas únicas cargadas de validadores: {len(all_validator_plates)}")


        # --- 3. Obtener Placas de la Base de Datos ---
        # (Sin cambios)
        logger.info("Obteniendo placas existentes en la base de datos...")
        try:
            db_vehicle_plates = set(Vehiculos.objects.values_list('placa', flat=True))
            logger.info(f"Total placas encontradas en la base de datos: {len(db_vehicle_plates)}")
        except Exception as e:
            raise CommandError(f"Error obteniendo placas de la base de datos: {e}")


        # --- 4. Identificar y Realizar Eliminaciones ---
        # (Sin cambios en la lógica de eliminación)
        plates_to_delete = db_vehicle_plates - all_validator_plates
        deleted_count = 0
        if plates_to_delete:
            logger.warning(f"Se eliminarán {len(plates_to_delete)} vehículos y sus relaciones por no estar en los validadores.")
            # Confirmación?
            for placa_del in plates_to_delete:
                try:
                    vehiculo_to_delete = Vehiculos.objects.get(placa=placa_del)
                    vehiculo_to_delete.delete()
                    logger.info(f"Vehículo {placa_del} y sus relaciones eliminados.")
                    deleted_count += 1
                except Vehiculos.DoesNotExist:
                     logger.warning(f"Vehículo {placa_del} para eliminar no encontrado (¿ya borrado?).")
                except Exception as e:
                     logger.error(f"Error eliminando vehículo {placa_del}: {e}")
                     # Podría detener la transacción aquí si es crítico
            logger.warning(f"Eliminación completada. {deleted_count} vehículos eliminados.")
        else:
            logger.info("No se encontraron vehículos en la BD para eliminar.")


        # --- 5. Procesar Creaciones y Actualizaciones (Usando Búsqueda Normalizada) ---
        created_count = 0
        updated_count = 0
        error_count = 0
        processed_count = 0

        logger.info(f"Procesando {len(all_validator_plates)} vehículos desde validadores para creación/actualización...")

        for i, placa_norm in enumerate(all_validator_plates):
            if (i + 1) % 100 == 0:
                logger.info(f"Procesando vehículo {i+1} de {len(all_validator_plates)}: {placa_norm}")

            val_info = validator_data[placa_norm]
            row_data = val_info['data']
            source = val_info['source']
            is_update = placa_norm in db_vehicle_plates
            log_prefix = f"Vehículo {placa_norm} (Fuente: {source}, {'Update' if is_update else 'Create'}):"

            try:
                # --- Extraer y Mapear Datos del Vehículo (Usando get_or_create_fk_normalized) ---
                vehiculo_defaults = {}
                empresa_obj = None

                if source == 'v2':
                    empresa_obj = empresas_cache_id.get(1)
                    if not empresa_obj: logger.error(f"{log_prefix} Empresa ID 1 no encontrada!"); error_count+=1; continue

                    vehiculo_defaults['marca'] = get_or_create_fk_normalized(Marca, marcas_cache, safe_get(row_data, 'MARCA'))
                    vehiculo_defaults['tipoLinea'] = get_or_create_fk_normalized(TipoLinea, lineas_cache, safe_get(row_data, 'LINEA'))
                    vehiculo_defaults['modelo'] = to_int_or_none(safe_get(row_data, 'MODELO'))
                    vehiculo_defaults['paxLt'] = to_int_or_none(safe_get(row_data, 'CAPACIDAD RUNT LICENCIA'))
                    vehiculo_defaults['numeroMotor'] = to_str_or_none(safe_get(row_data, 'No MOTOR'))
                    vehiculo_defaults['serie'] = to_str_or_none(safe_get(row_data, 'No SERIE'))
                    vehiculo_defaults['chasis'] = to_str_or_none(safe_get(row_data, 'No CHASIS'))
                    vehiculo_defaults['clase'] = get_or_create_fk_normalized(ClaseVehiculo, clasesv_cache, safe_get(row_data, 'TIPO')) # TIPO -> ClaseVehiculo
                    vehiculo_defaults['licenciaTransito'] = to_str_or_none(safe_get(row_data, 'No LICENCIA TRANSITO'))
                    vehiculo_defaults['estado'] = to_str_or_none(safe_get(row_data, 'ESTADO', 'ACTIVO'))
                    vehiculo_defaults['fechaMatricula'] = to_date_or_none(safe_get(row_data, 'FECHA DE MATRICULA'))
                    # Usar función de ciudad normalizada
                    ciudad_matricula = get_ciudad_normalized(ciudades_cache, safe_get(row_data, 'LUGAR DE MATRICULA'), None)
                    vehiculo_defaults['ciudadBase'] = ciudad_matricula

                elif source == 'v1':
                    empresa_nombre = to_str_or_none(safe_get(row_data, 'EMPRESA'))
                    empresa_id_v1 = EMPRESA_MAP_V1.get(empresa_nombre) if empresa_nombre else None
                    if empresa_id_v1: empresa_obj = empresas_cache_id.get(empresa_id_v1)
                    if not empresa_obj: logger.error(f"{log_prefix} Empresa '{empresa_nombre}' no mapeada o no encontrada!"); error_count+=1; continue

                    # V1 no tiene Marca/Linea explícita, se crearán si no existen o se dejarán nulos
                    vehiculo_defaults['marca'] = get_or_create_fk_normalized(Marca, marcas_cache, None) # O buscar por otro campo si existe?
                    vehiculo_defaults['tipoLinea'] = get_or_create_fk_normalized(TipoLinea, lineas_cache, None)

                    vehiculo_defaults['modelo'] = to_int_or_none(safe_get(row_data, 'MODELO'))
                    vehiculo_defaults['paxLt'] = to_int_or_none(safe_get(row_data, 'CAP LICENCIA'))
                    vehiculo_defaults['clase'] = get_or_create_fk_normalized(ClaseVehiculo, clasesv_cache, safe_get(row_data, 'CLASE'))
                    vehiculo_defaults['vin'] = to_str_or_none(safe_get(row_data, 'VIN'))
                    vehiculo_defaults['numeroMotor'] = to_str_or_none(safe_get(row_data, 'MOTOR'))
                    vehiculo_defaults['chasis'] = to_str_or_none(safe_get(row_data, 'CHASIS'))
                    vehiculo_defaults['licenciaTransito'] = to_str_or_none(safe_get(row_data, 'LICENCIA TRANSITO'))
                    vehiculo_defaults['estado'] = 'ACTIVO'

                vehiculo_defaults['empresa'] = empresa_obj
                vehiculo_defaults = {k: v for k, v in vehiculo_defaults.items() if v is not None} # Limpiar Nones

                if not vehiculo_defaults.get('clase') or not vehiculo_defaults.get('modelo'):
                     logger.error(f"{log_prefix} Datos básicos faltantes (Clase/Modelo). Saltando.")
                     error_count += 1
                     continue

                vehiculo_obj, v_created = Vehiculos.objects.update_or_create(
                    placa=placa_norm, defaults=vehiculo_defaults
                )
                if v_created: created_count += 1
                else: updated_count += 1

                # --- Procesar Propietarios (Usando get_ciudad_normalized) ---
                propietarios_info = [] # Lista para almacenar dicts de info de propietarios
                # ... (Lógica de extracción de propietarios_info para V1 y V2 igual que antes) ...
                if source == 'v2':
                    p1_nombre=safe_get(row_data, 'PROPIETARIO 1'); p1_id=safe_get(row_data, 'CEDULA')
                    if p1_nombre and p1_id:
                        n, a = parse_propietario_name(p1_nombre)
                        propietarios_info.append({'nombre':n,'apellido':a,'id':p1_id,'tel':safe_get(row_data,'TELEFONO'),'correo':safe_get(row_data,'CORREO ELECTRONICO'),'dir':safe_get(row_data,'DIRECCION'),'ciudad_nombre':safe_get(row_data,'CIUDAD RESIDENCIA'),'dpto_nombre':None})
                    p2_nombre=safe_get(row_data, 'PROPIETARIO2'); p2_id=safe_get(row_data, row_data.index[8] if len(row_data.index)>8 else None) # Cuidado con indice fijo!
                    if p2_nombre and p2_id:
                        n, a = parse_propietario_name(p2_nombre)
                        propietarios_info.append({'nombre':n,'apellido':a,'id':p2_id,'tel':None,'correo':None,'dir':None,'ciudad_nombre':None,'dpto_nombre':None})
                elif source == 'v1':
                    p1_nombre=safe_get(row_data,'NombrePropietario 1');p1_id=safe_get(row_data,'Identificacion Prop 1')
                    if p1_nombre and p1_id:
                         n,a=parse_propietario_name(p1_nombre)
                         propietarios_info.append({'nombre':n,'apellido':a,'id':p1_id,'tel':safe_get(row_data,'Telefono 1'),'correo':safe_get(row_data,'Correo 1'),'dir':safe_get(row_data,'Direccion 1'),'ciudad_nombre':safe_get(row_data,'CIUDAD 1'),'dpto_nombre':safe_get(row_data,'DEPARTAMENTO 1')})
                    p2_nombre=safe_get(row_data,'NombrePropietario 2');p2_id=safe_get(row_data,'Identificacion Prop 2')
                    if p2_nombre and p2_id:
                         n,a=parse_propietario_name(p2_nombre)
                         propietarios_info.append({'nombre':n,'apellido':a,'id':p2_id,'tel':safe_get(row_data,'Telefono 2'),'correo':safe_get(row_data,'Correo 2'),'dir':safe_get(row_data,'Direccion 2'),'ciudad_nombre':safe_get(row_data,'CIUDAD 2'),'dpto_nombre':safe_get(row_data,'DEPARTAMENTO 2')})

                # Actualizar propietarios y relaciones
                if propietarios_info:
                    VehiculoPropietario.objects.filter(vehiculo=vehiculo_obj).delete()
                    num_owners = len(propietarios_info)
                    porcentaje = round(100 / num_owners) if num_owners > 0 else 100

                    for owner_data in propietarios_info:
                        prop_id_orig = to_str_or_none(owner_data['id'])
                        if not prop_id_orig: continue

                        # Usar get_ciudad_normalized para la ciudad del propietario
                        ciudad_prop = get_ciudad_normalized(ciudades_cache, owner_data['ciudad_nombre'], owner_data['dpto_nombre'])

                        prop_defaults = {
                            'nombres': to_str_or_none(owner_data['nombre']),
                            'apellidos': to_str_or_none(owner_data['apellido']),
                            'telefono': to_str_or_none(owner_data['tel']),
                            'correo': to_str_or_none(owner_data['correo']),
                            'direccion': to_str_or_none(owner_data['dir']),
                            'ciudad': ciudad_prop, # <-- Ciudad normalizada
                            'tipoDocumento': tipo_doc_persona_cc
                        }
                        prop_defaults = {k: v for k, v in prop_defaults.items() if v is not None}

                        propietario_obj, p_created = Propietario.objects.update_or_create(
                            identificacion=prop_id_orig, defaults=prop_defaults
                        )
                        VehiculoPropietario.objects.create(
                            vehiculo=vehiculo_obj, propietario=propietario_obj, porcentaje=porcentaje
                        )
                else:
                    logger.warning(f"{log_prefix} No se encontraron datos de propietario en el validador.")


                # --- Procesar Servicio (Usando FKs normalizados) ---
                servicio_defaults = {}
                if source == 'v2':
                    servicio_defaults['numeroInterno'] = to_int_or_none(safe_get(row_data, 'No Interno'))
                    servicio_defaults['fechaIngreso'] = to_date_or_none(safe_get(row_data, 'FECHA AFILIACION'))
                elif source == 'v1':
                    servicio_defaults['numeroInterno'] = to_int_or_none(safe_get(row_data, 'VEHICULO'))
                    modalidad_nombre = to_str_or_none(safe_get(row_data, 'MODALIDAD DE SERVICIO'))
                    # Usar búsqueda normalizada para TipoOperacion
                    servicio_defaults['tipoOperacion'] = get_or_create_fk_normalized(TipoOperacion, tipo_op_cache, modalidad_nombre)
                    fecha_ing_v1 = to_date_or_none(safe_get(row_data, 'fechaInicioServicio o vinculacion radicacion t.-operación o expedicion'))
                    servicio_defaults['fechaIngreso'] = fecha_ing_v1

                servicio_defaults['empresaOficial'] = empresa_obj
                # NivelServicio y Servicio (Categoria) - si no están en validadores, se omitirán
                # servicio_defaults['nivelServicio'] = get_or_create_fk_normalized(NivelServicio, ..., ...)
                # servicio_defaults['servicio'] = get_or_create_fk_normalized(Categoria, ..., ...)

                servicio_defaults = {k: v for k, v in servicio_defaults.items() if v is not None}
                if servicio_defaults.get('empresaOficial') and servicio_defaults.get('fechaIngreso'):
                     Servicio.objects.update_or_create(vehiculo=vehiculo_obj, defaults=servicio_defaults)
                else:
                     logger.warning(f"{log_prefix} Datos insuficientes para Servicio.")


                # --- Procesar Documentos (Usando búsqueda normalizada para Aseguradora) ---
                # SOAT
                num_soat, fec_venc_soat, aseg_nombre_soat = None, None, None
                if source == 'v2':
                    num_soat=safe_get(row_data,'SOAT NUMERO'); fec_venc_soat=safe_get(row_data,'SOAT FECHA VENCIMIENTO')
                elif source == 'v1':
                    num_soat=safe_get(row_data,'NUMERO SOAT'); fec_venc_soat=safe_get(row_data,'FECHA VENCIMIENTO SOAT'); aseg_nombre_soat=safe_get(row_data,'ASEGURADORA')

                if num_soat and fec_venc_soat:
                    aseg_obj = None
                    aseg_nombre_soat_str = to_str_or_none(aseg_nombre_soat)
                    if aseg_nombre_soat_str:
                        aseg_norm_key = normalize_text(aseg_nombre_soat_str)
                        aseg_obj = aseguradoras_cache_norm.get(aseg_norm_key)
                        if not aseg_obj:
                            logger.warning(f"{log_prefix} Aseguradora SOAT '{aseg_nombre_soat_str}' no encontrada en BD (búsqueda normalizada). Se dejará nula.")

                    Soat.objects.update_or_create(
                        vehiculo=vehiculo_obj, numero_poliza=to_str_or_none(num_soat), vigencia_hasta=to_date_or_none(fec_venc_soat),
                        defaults={
                            'aseguradora': aseg_obj,
                            'aseguradora_nombre': aseg_nombre_soat_str, # Guardar nombre original
                            'fecha_expedicion': None, 'vigencia_desde': None, 'estado': True,
                            'tipo_documento_vehiculo': tipo_doc_veh_cache.get(1)
                        }
                    )

                # RTM
                num_rtm, fec_venc_rtm = None, None
                if source == 'v2': num_rtm=safe_get(row_data,'TECNOMECANICA NUMERO'); fec_venc_rtm=safe_get(row_data,'TECNOMECANICA FECHA VENCIMIENTO')
                elif source == 'v1': num_rtm=safe_get(row_data,'NUMERO TECNICOMECANICA'); fec_venc_rtm=safe_get(row_data,'FECHA VENCIMIENTO REVISION TECNICO MECANICA')

                if num_rtm and fec_venc_rtm:
                    RevisionTecnomecanica.objects.update_or_create(
                        vehiculo=vehiculo_obj, no_certificado=to_str_or_none(num_rtm), fecha_vencimiento=to_date_or_none(fec_venc_rtm),
                        defaults={
                            'fecha_expedicion': None, 'estado': True,
                            'tipo_documento_vehiculo': tipo_doc_veh_cache.get(3)
                        }
                    )

                # Tarjeta Operacion
                num_to, fec_venc_to, cap_to = None, None, None
                if source == 'v2': num_to=safe_get(row_data,'TARJETA OPERACIÓN No'); fec_venc_to=safe_get(row_data,'VENCIMIENTO TARJETA OPERACIÓN'); cap_to=safe_get(row_data,'CAPACIDAD TARJETA OPERACIÓN')
                elif source == 'v1': num_to=safe_get(row_data,'NUMERO TARJETA OPERACIÓN'); fec_venc_to=safe_get(row_data,'FECHA VENCIMIENTO TARJETA DE OPERACIÓN')

                if num_to and fec_venc_to:
                    TarjetaOperacion.objects.update_or_create(
                         vehiculo=vehiculo_obj, numero=to_str_or_none(num_to), fechaFinVigencia=to_date_or_none(fec_venc_to),
                         defaults={
                             'fechaExpedicion': None, 'fechaInicialVigencia': None,
                             'capacidad': to_int_or_none(cap_to), 'estado': True,
                             'tipo_documento_vehiculo': tipo_doc_veh_cache.get(2)
                         }
                    )

                # Licencia Tránsito
                num_lic = None
                if source == 'v2': num_lic = safe_get(row_data, 'No LICENCIA TRANSITO')
                elif source == 'v1': num_lic = safe_get(row_data, 'LICENCIA TRANSITO')
                num_lic_str = to_str_or_none(num_lic)
                if num_lic_str:
                    # Actualizar en Vehiculo si cambió
                    if vehiculo_obj.licenciaTransito != num_lic_str:
                         vehiculo_obj.licenciaTransito = num_lic_str
                         vehiculo_obj.save(update_fields=['licenciaTransito'])
                    LicenciaTransito.objects.update_or_create(
                        vehiculo=vehiculo_obj, numero_documento=num_lic_str,
                        defaults={
                            'fecha_expedicion': None, 'estado': True,
                            'tipo_documento_vehiculo': tipo_doc_veh_cache.get(10)
                        }
                    )

                # Pólizas Contractual y Extracontractual
                num_pol_cont, num_pol_extra, fec_venc_pol, fec_venc_cont, fec_venc_extra, aseg_nombre_pol = None, None, None, None, None, None
                if source == 'v2':
                    poliza_combined_key=next((k for k in row_data.index if isinstance(k,str) and 'R.C. C. POLIZA' in k),None)
                    poliza_combined_field=to_str_or_none(safe_get(row_data, poliza_combined_key)) if poliza_combined_key else None
                    fec_venc_pol=safe_get(row_data,'VENCIMIENTO POLIZA')
                    if poliza_combined_field:
                        match_cont=re.search(r"R\.C\. C\. POLIZA\s*([^\s/]+)",poliza_combined_field,re.IGNORECASE)
                        match_extra=re.search(r"R\.C\. E\. POLIZA\s*([^\s/]+)",poliza_combined_field,re.IGNORECASE)
                        if match_cont: num_pol_cont=match_cont.group(1)
                        if match_extra: num_pol_extra=match_extra.group(1)
                elif source == 'v1':
                    num_pol_cont=safe_get(row_data,'NUMERO POLIZA CONTRACTUAL')
                    fec_venc_cont=safe_get(row_data,'FECHA VENCIMIENTO CONTRACTUAL')
                    num_pol_extra=safe_get(row_data,'NUMERO POLIZA EXCONTRACTUAL')
                    fec_venc_extra=safe_get(row_data,'FECHA VENCIMIENTO EXTRACONTRACTUAL')
                    aseg_nombre_pol=aseg_nombre_soat # Reusar aseguradora SOAT V1

                aseg_obj_pol = None
                aseg_nombre_pol_str = to_str_or_none(aseg_nombre_pol)
                if aseg_nombre_pol_str:
                    aseg_pol_norm_key = normalize_text(aseg_nombre_pol_str)
                    aseg_obj_pol = aseguradoras_cache_norm.get(aseg_pol_norm_key)
                    if not aseg_obj_pol:
                        logger.warning(f"{log_prefix} Aseguradora Pólizas '{aseg_nombre_pol_str}' no encontrada en BD. Se dejará nula.")

                fec_venc_usar_cont = to_date_or_none(fec_venc_pol if source == 'v2' else fec_venc_cont)
                num_pol_cont_str = to_str_or_none(num_pol_cont)
                if num_pol_cont_str and fec_venc_usar_cont:
                    PolizaContractual.objects.update_or_create(
                        vehiculo=vehiculo_obj, numero_poliza=num_pol_cont_str, fecha_fin_vigencia=fec_venc_usar_cont,
                        defaults={
                            'aseguradora': aseg_obj_pol, 'aseguradora_nombre_alt': aseg_nombre_pol_str,
                            'estado': True, 'tipo_documento_vehiculo': tipo_doc_veh_cache.get(4)
                        }
                    )

                fec_venc_usar_extra = to_date_or_none(fec_venc_pol if source == 'v2' else fec_venc_extra)
                num_pol_extra_str = to_str_or_none(num_pol_extra)
                if num_pol_extra_str and fec_venc_usar_extra:
                     PolizaExtracontractual.objects.update_or_create(
                         vehiculo=vehiculo_obj, numero_poliza=num_pol_extra_str, fecha_fin_vigencia=fec_venc_usar_extra,
                         defaults={
                             'aseguradora': aseg_obj_pol, 'aseguradora_nombre_alt': aseg_nombre_pol_str,
                             'estado': True, 'tipo_documento_vehiculo': tipo_doc_veh_cache.get(5)
                         }
                     )

                processed_count += 1

            except IntegrityError as ie:
                logger.error(f"{log_prefix} Error de Integridad: {ie}")
                error_count += 1
            except Exception as e:
                logger.error(f"{log_prefix} Error inesperado: {e}", exc_info=True)
                error_count += 1

        # --- 6. Resumen Final ---
        # (Sin cambios)
        logger.info("--- Resumen de Sincronización ---")
        logger.info(f"Vehículos eliminados (no en validadores): {deleted_count}")
        logger.info(f"Vehículos creados (nuevos desde validadores): {created_count}")
        logger.info(f"Vehículos actualizados (existentes en BD y validadores): {updated_count}")
        logger.info(f"Vehículos procesados con errores: {error_count}")
        logger.info(f"Total vehículos procesados desde validadores: {processed_count} de {len(all_validator_plates)}")

        if error_count > 0:
             logger.error(f"Se encontraron {error_count} errores durante el proceso.")
             # Descomentar para forzar rollback si hay errores:
             # raise CommandError("Proceso de sincronización finalizado con errores.")
        else:
             logger.info(self.style.SUCCESS("Sincronización completada exitosamente."))