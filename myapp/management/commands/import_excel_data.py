import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
import math
from django.shortcuts import get_object_or_404
import re
from django.db import models as django_models
from django.db.models import Q
from datetime import date

from myapp.models import (
    TipoDocumento, Empresas, Vehiculos, Propietario, Marca, TipoLinea,
    ClaseVehiculo, Carroceria, Combustible, TipoOperacion, Ciudad, NivelServicio,
    Categoria, Color, VehiculoPropietario, Servicio,
    Aseguradora, TipoDocumentoVehiculo,
    Soat, RevisionTecnomecanica, TarjetaOperacion,
    PolizaContractual, PolizaExtracontractual, PolizaTodoRiesgo,
    FichaTecnicaHomologacionChasis, FichaTecnicaHomologacionCarroceria,
    FichaTecnicaHomologacionVehCarrozado, LicenciaTransito
)

SOPORTE_URL_PREFIX = "http://201.216.13.254/GESTORTIC/Tipab/Gestion/Temporales/"

def safe_get(row, key, default=None):
    val = row.get(key)
    if pd.isna(val) or val is None:
        return default
    if isinstance(val, float) and math.isnan(val):
        return default
    return val

def to_int_or_none(value):
    if pd.isna(value) or value is None or (isinstance(value, str) and str(value).strip().upper() == 'NULL'):
        return None
    try:
        s_value = str(value)
        cleaned_value = s_value.split('.')[0] if '.' in s_value else s_value
        return int(cleaned_value)
    except (ValueError, TypeError):
        return None

def to_str_or_none(value):
    if pd.isna(value) or value is None or (isinstance(value, str) and str(value).strip().upper() == 'NULL'):
        return None
    val_str = str(value).strip()
    return val_str


def parse_propietario_name(full_name_str):
    if not full_name_str:
        return None, None
    parts = str(full_name_str).strip().split()
    if not parts:
        return None, None
    
    if len(parts) >= 4:
        nombres = " ".join(parts[:2])
        apellidos = " ".join(parts[2:])
    elif len(parts) == 3:
        nombres = parts[0]
        apellidos = " ".join(parts[1:])
    elif len(parts) == 2:
        nombres = parts[0]
        apellidos = parts[1]
    else:
        nombres = parts[0]
        apellidos = None
    return nombres, apellidos

def to_date_or_none(value):
    if pd.isna(value) or value is None or str(value).strip().upper() == 'NULL' or str(value).strip() == '00:00.0':
        return None
    try:
        if isinstance(value, pd.Timestamp):
            return value.date()
        if isinstance(value, (int, float)): 
            if value > 20000 and value < 60000 : 
                return (pd.to_datetime('1899-12-30') + pd.to_timedelta(value, 'D')).date()
            else: 
                return None 
        dt = pd.to_datetime(value, errors='coerce', dayfirst=False)
        if pd.isna(dt): 
            dt = pd.to_datetime(value, errors='coerce', dayfirst=True)
        return dt.date() if pd.notna(dt) else None
    except (ValueError, TypeError, OverflowError):
        return None

def get_fk_object_from_map(excel_id_val, object_map, object_model_name, record_identifier_str, errors_list, excel_column_name_str):
    if excel_id_val is None: return None
    id_lookup = to_int_or_none(excel_id_val)
    if id_lookup is None: return None
    obj = object_map.get(id_lookup)
    return obj

def make_unique_placeholder(placa, field_name, original_value, max_len):
    str_value = to_str_or_none(original_value)

    if str_value is None: 
        return None

    common_non_unique_patterns = ["NO REGISTRA", "ILEGIBLE", "PENDIENTE", "NO TIENE", "NO CUENTA", "NO APLICA", "NO REPORTA", "NO DISPONIBLE"]
    val_upper = str_value.upper()
    
    is_problematic = not str_value.strip() 

    if not is_problematic:
        for pattern in common_non_unique_patterns:
            if pattern in val_upper:
                is_problematic = True
                break
    
    if is_problematic:
        base = f"{field_name.upper()}-{placa}"
        if not str_value.strip(): 
             placeholder = base + "-EMPTY"
        else: 
            snippet = "".join(filter(str.isalnum, str_value))[:10] 
            placeholder = base + f"-{snippet}" if snippet else base + "-PATTERN"
        return placeholder[:max_len]
        
    return str_value[:max_len] 

class Command(BaseCommand):
    help = 'Import data from Excel file into Django models, prioritizing validator files and creating Servicio records, and then vehicle documents.'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the main Excel file (doc migracion.xlsx)')
        parser.add_argument('validator1_file', type=str, help='Path to the validator.xlsx file')
        parser.add_argument('validator2_file', type=str, help='Path to the validator2.xlsx file')

    def _get_or_create_fk_by_name(self, model_class, name_value, name_field_in_model, errors_list, record_identifier_str, default_values_for_creation=None, create_if_not_found=True):
        if not name_value: return None
        if default_values_for_creation is None: default_values_for_creation = {}
        
        cleaned_name_value = str(name_value).strip() 
        if not cleaned_name_value: return None

        query_lookup_params = {f"{name_field_in_model}__iexact": cleaned_name_value}
        if model_class == TipoLinea and 'marca' in default_values_for_creation:
            if default_values_for_creation['marca'] is not None:
                query_lookup_params['marca'] = default_values_for_creation['marca']

        try:
            obj = model_class.objects.filter(**query_lookup_params).first()
            if obj: return obj
            
            if create_if_not_found:
                valid_creation_data = {name_field_in_model: cleaned_name_value} 
                
                for k,v in default_values_for_creation.items():
                    if hasattr(model_class, k.split('__')[0]): 
                        valid_creation_data[k.split('__')[0]] = v
                
                get_or_create_lookup_params = {f"{name_field_in_model}__iexact": cleaned_name_value}
                if model_class == TipoLinea and 'marca' in valid_creation_data:
                     if valid_creation_data['marca'] is not None: 
                        get_or_create_lookup_params['marca'] = valid_creation_data['marca']

                final_defaults_for_creation = {k:v for k,v in valid_creation_data.items() if hasattr(model_class, k.split('__')[0])}
                for k_lookup in get_or_create_lookup_params:
                    final_defaults_for_creation.pop(k_lookup.split('__')[0], None)

                obj, created = model_class.objects.get_or_create(
                    **get_or_create_lookup_params, 
                    defaults=final_defaults_for_creation
                )
                return obj
            return None
        except IntegrityError as ie:
            obj = model_class.objects.filter(**query_lookup_params).first() 
            if obj: return obj
            errors_list.append(f"ERROR FK (Integrity): No se pudo crear/obtener {model_class.__name__} para '{cleaned_name_value}' en {record_identifier_str}. Error: {ie}. Lookup: {query_lookup_params} Defaults: {default_values_for_creation}")
            return None
        except Exception as e:
            errors_list.append(f"ERROR FK (Exception): No se pudo crear/obtener {model_class.__name__} para '{cleaned_name_value}' en {record_identifier_str}. Error: {type(e).__name__} - {e}. Lookup: {query_lookup_params} Args: {default_values_for_creation}")
            return None

    @transaction.atomic
    def handle(self, *args, **options):
        excel_file_path = options['excel_file']
        validator1_file_path = options['validator1_file']
        validator2_file_path = options['validator2_file']
        
        errors_log, summary = [], {}
        self.stdout.write(f"Iniciando importación...")

        tipo_doc_default, _ = TipoDocumento.objects.get_or_create(id=1, defaults={'nombre': 'CÉDULA DE CIUDADANÍA'})

        empresa_id_1_obj = Empresas.objects.filter(id=1).first()
        empresa_id_2_obj = Empresas.objects.filter(id=2).first()
        empresa_id_4_obj = Empresas.objects.filter(id=4).first()
        empresa_id_5_obj = Empresas.objects.filter(id=5).first()
        empresa_id_6_obj = Empresas.objects.filter(id=6).first()
        
        generic_empresa_nit_super_gen = "NIT000SUPERGENDEF" 
        generic_empresa_super_obj = None 

        if not empresa_id_1_obj: errors_log.append("ERROR CRÍTICO: Empresa con ID 1 (requerida para validator2 y fallback) no encontrada en BD.")

        map_vars = {k: {} for k in ["tipo_operacion_map", "combustible_map", "carroceria_map", "marca_map", "tipo_linea_map", 
                                     "nivel_servicio_map", "clase_vehiculo_map", "categoria_map", "color_map", "ciudad_map", 
                                     "empresas_map", "propietarios_map_excel_id_to_django_obj", "vehiculos_map_excel_id_to_django_obj"]}
        placas_with_validator_owners, propietarios_cache_by_identificacion = set(), {}

        validator1_data_map, validator2_data_map = {}, {}
        try:
            df_val1 = pd.read_excel(validator1_file_path, sheet_name=0, dtype=str) 
            for _, row in df_val1.iterrows():
                placa = to_str_or_none(row.get('PLACA'))
                if placa: validator1_data_map[placa.upper()] = row
        except Exception as e: errors_log.append(f"Error validator.xlsx: {e}")

        try:
            df_val2 = pd.read_excel(validator2_file_path, sheet_name=0, dtype=str) 
            c1_col, c2_col = 'CEDULA', (df_val2.columns[8] if len(df_val2.columns) > 8 else None)
            for _, row in df_val2.iterrows():
                placa = to_str_or_none(row.get('PLACA'))
                if placa:
                    rd = row.to_dict(); rd['_cedula_p1_col_name'], rd['_cedula_p2_col_name'] = c1_col, c2_col
                    validator2_data_map[placa.upper()] = rd
        except Exception as e: errors_log.append(f"Error validator2.xlsx: {e}")

        sheets_cfg = [('Tipos Operacion', TipoOperacion, 'tipo_operacion_map', 'tipoOperacionID', 'descripcionTipoOperacion', 'nombre'),
                      ('tipoCombustible', Combustible, 'combustible_map', 'combustibleID', 'descripcionCombustible', 'nombre'),
                      ('tipoCarroceria', Carroceria, 'carroceria_map', 'carroceriaID', 'DescripcionCarroceria', 'nombre'),
                      ('marcas', Marca, 'marca_map', 'marcaID', 'DescripcionMarca', 'nombre'),
                      ('LineasMarca', TipoLinea, 'tipo_linea_map', 'lineaID', 'detalleLinea', 'nombre'), 
                      ('nivelServicio', NivelServicio, 'nivel_servicio_map', 'nivelServicioID', 'DescripcionNivelServicio', 'nombre'),
                      ('claseVehiculo', ClaseVehiculo, 'clase_vehiculo_map', 'claseVehicID', 'DescripcionClaseVehiculo', 'nombre'),
                      ('categorias veh', Categoria, 'categoria_map', 'categoriaID', 'DescripcionCategoria', 'nombre'),
                      ('colores-veh', Color, 'color_map', 'colorID', 'detalleColor', 'nombre'),
                      ('Ciudades', Ciudad, 'ciudad_map', 'ciudadID', 'DescripcionCiudad', 'nombre'),]

        for sh_name, model, map_name, id_col, name_col_xl, name_fld_mdl in sheets_cfg:
            try:
                df = pd.read_excel(excel_file_path, sheet_name=sh_name, dtype=str)
                for _, row in df.iterrows():
                    nombre, excel_id = to_str_or_none(row.get(name_col_xl)), to_int_or_none(row.get(id_col))
                    if nombre and excel_id is not None:
                        obj, _ = model.objects.get_or_create(**{name_fld_mdl: nombre})
                        map_vars[map_name][excel_id] = obj
            except FileNotFoundError: errors_log.append(f"Advertencia: Hoja '{sh_name}' no encontrada en {excel_file_path}.")
            except Exception as e: errors_log.append(f"Error hoja '{sh_name}': {e}")
        
        try:
            df_empresas = pd.read_excel(excel_file_path, sheet_name='Empresas', dtype=str)
            for _, row in df_empresas.iterrows():
                excel_id, nom_emp, nit = to_int_or_none(row.get('empresaID')), to_str_or_none(row.get('DescripcionEmpresa')), to_str_or_none(row.get('nit'))
                if excel_id is not None and nom_emp and nit:
                    try:
                        emp_defaults = {
                            'nombre_empresa': nom_emp, 'nit': nit, 
                            'direccion': to_str_or_none(row.get('direccion')),
                            'telefono1': to_int_or_none(row.get('Telefono1')), 
                            'telefono2': to_int_or_none(row.get('Telefono2')), 
                            'email': to_str_or_none(row.get('EMail')), 
                            'estado': to_str_or_none(row.get('estado')) == '1'
                        }
                        if emp_defaults['telefono1'] is None: emp_defaults['telefono1'] = 0 
                        if emp_defaults['email'] is None: emp_defaults['email'] = "default@example.com"


                        obj, _ = Empresas.objects.update_or_create(id=excel_id, defaults=emp_defaults)
                        map_vars['empresas_map'][excel_id] = obj
                    except IntegrityError:
                        obj_by_nit = Empresas.objects.filter(nit=nit).first()
                        if obj_by_nit: map_vars['empresas_map'][excel_id] = obj_by_nit
            summary['Empresas'] = f"{len(map_vars['empresas_map'])} procesadas."
        except FileNotFoundError: pass
        except Exception as e: errors_log.append(f"Error hoja 'Empresas': {e}")

        try:
            df_prop_main = pd.read_excel(excel_file_path, sheet_name='Propietarios', dtype=str)
            for _, row in df_prop_main.iterrows():
                ident, excel_id, nombres_xl = to_str_or_none(row.get('identificacion')), to_int_or_none(row.get('propietariosID')), to_str_or_none(row.get('nombre'))
                apellidos_xl = to_str_or_none(row.get('apellido'))

                if not ident: 
                    continue
                
                nombres_parsed, apellidos_parsed = parse_propietario_name(nombres_xl)
                
                final_nombres = nombres_parsed
                final_apellidos = apellidos_parsed if apellidos_parsed else apellidos_xl 

                if ident and excel_id is not None and final_nombres: 
                    prop_defs = {
                        'tipoDocumento': tipo_doc_default, 
                        'nombres': final_nombres, 
                        'apellidos': final_apellidos,
                        'telefono': to_str_or_none(row.get('telefono')), 
                        'correo': to_str_or_none(row.get('correo'))
                    }
                    prop_obj, _ = Propietario.objects.update_or_create(identificacion=ident, defaults=prop_defs)
                    map_vars['propietarios_map_excel_id_to_django_obj'][excel_id] = prop_obj
                    propietarios_cache_by_identificacion[ident] = prop_obj
        except FileNotFoundError: pass
        except Exception as e: errors_log.append(f"Error hoja 'Propietarios': {e}")

        all_plates_to_process = set(validator1_data_map.keys()) | set(validator2_data_map.keys())
        main_excel_vehicle_data = {}
        try:
            df_vehiculos_main = pd.read_excel(excel_file_path, sheet_name='Vehiculos', dtype=str)
            for _, row in df_vehiculos_main.iterrows():
                placa = to_str_or_none(row.get('placa_Vehiculo'))
                if placa:
                    placa_upper = placa.upper(); main_excel_vehicle_data[placa_upper] = row; all_plates_to_process.add(placa_upper)
        except FileNotFoundError: pass
        except Exception as e: errors_log.append(f"Error hoja 'Vehiculos': {e}")

        self.stdout.write(self.style.SUCCESS(f"\n--- Iniciando procesamiento de {len(all_plates_to_process)} vehículos únicos ---"))
        count_vehiculos_processed = 0

        for placa_upper in all_plates_to_process:
            main_row, val2_dict, val1_series = main_excel_vehicle_data.get(placa_upper), validator2_data_map.get(placa_upper), validator1_data_map.get(placa_upper)
            
            current_source_file_info = "Desconocida"
            if val2_dict: current_source_file_info = "validator2.xlsx"
            elif val1_series is not None: current_source_file_info = "validator.xlsx"
            elif main_row is not None: current_source_file_info = "doc_migracion.xlsx (Hoja Vehiculos)"

            if main_row is None and val2_dict is None and val1_series is None: continue

            excel_vehiculo_id = to_int_or_none(safe_get(main_row, 'vehiculoID')) if main_row is not None else None
            record_id_str = f"Placa: {placa_upper} (Fuente Datos: {current_source_file_info})"
            
            owner_details = []
            if val2_dict:
                p1n, p1id = to_str_or_none(val2_dict.get('PROPIETARIO 1')), to_str_or_none(val2_dict.get(val2_dict.get('_cedula_p1_col_name')))
                if p1id and p1n: n,a=parse_propietario_name(p1n); owner_details.append({'id':p1id,'n':n,'a':a,'tel':to_str_or_none(val2_dict.get('TELEFONO')),'cor':to_str_or_none(val2_dict.get('CORREO ELECTRONICO'))})
                p2n, p2id_col = to_str_or_none(val2_dict.get('PROPIETARIO2')), val2_dict.get('_cedula_p2_col_name')
                p2id = to_str_or_none(val2_dict.get(p2id_col)) if p2id_col else None
                if p2id and p2n: n,a=parse_propietario_name(p2n); owner_details.append({'id':p2id,'n':n,'a':a,'tel':None,'cor':None})
            elif val1_series is not None:
                p1n, p1id = to_str_or_none(safe_get(val1_series, 'NombrePropietario 1')), to_str_or_none(safe_get(val1_series, 'Identificacion Prop 1'))
                if p1id and p1n: n,a=parse_propietario_name(p1n); owner_details.append({'id':p1id,'n':n,'a':a,'tel':to_str_or_none(safe_get(val1_series,'Telefono 1')),'cor':to_str_or_none(safe_get(val1_series,'Correo 1'))})
                p2n, p2id = to_str_or_none(safe_get(val1_series, 'NombrePropietario 2')), to_str_or_none(safe_get(val1_series, 'Identificacion Prop 2'))
                if p2id and p2n: n,a=parse_propietario_name(p2n); owner_details.append({'id':p2id,'n':n,'a':a,'tel':to_str_or_none(safe_get(val1_series,'Telefono 2')),'cor':to_str_or_none(safe_get(val1_series,'Correo 2'))})
            
            if owner_details: placas_with_validator_owners.add(placa_upper)

            veh_defs = {'placa': placa_upper}
            emp_asig = None

            if val2_dict:
                if empresa_id_1_obj: emp_asig = empresa_id_1_obj
                veh_defs.update({'numeroMotor': to_str_or_none(val2_dict.get('No MOTOR')), 'serie': to_str_or_none(val2_dict.get('No SERIE')),
                    'chasis': to_str_or_none(val2_dict.get('No CHASIS')), 'licenciaTransito': to_str_or_none(val2_dict.get('No LICENCIA TRANSITO')),
                    'modelo': to_int_or_none(val2_dict.get('MODELO')), 'paxLt': to_int_or_none(val2_dict.get('CAPACIDAD RUNT LICENCIA'))})
                m_str = to_str_or_none(val2_dict.get('MARCA')); lin_str = to_str_or_none(val2_dict.get('LINEA'))
                cls_str = to_str_or_none(val2_dict.get('TIPO')); ciu_str_raw = to_str_or_none(val2_dict.get('LUGAR DE MATRICULA'))
                if m_str: veh_defs['marca'] = self._get_or_create_fk_by_name(Marca, m_str, 'nombre', errors_log, record_id_str)
                m_obj = veh_defs.get('marca')
                if m_obj and lin_str: veh_defs['tipoLinea'] = self._get_or_create_fk_by_name(TipoLinea, lin_str, 'nombre', errors_log, record_id_str, {'marca': m_obj}) 
                elif lin_str: veh_defs['tipoLinea'] = self._get_or_create_fk_by_name(TipoLinea, lin_str, 'nombre', errors_log, record_id_str) 
                if cls_str: veh_defs['clase'] = self._get_or_create_fk_by_name(ClaseVehiculo, cls_str, 'nombre', errors_log, record_id_str)
                if ciu_str_raw: ciu_nom = ciu_str_raw.split('(')[0].split('/')[0].strip(); veh_defs['ciudadBase'] = self._get_or_create_fk_by_name(Ciudad, ciu_nom, 'nombre', errors_log, record_id_str)
            elif val1_series is not None:
                e_str = to_str_or_none(safe_get(val1_series, 'EMPRESA'))
                if e_str=="BERLINASTUR S.A." and empresa_id_4_obj: emp_asig=empresa_id_4_obj
                elif e_str=="BERLITUR S.A.S" and empresa_id_5_obj: emp_asig=empresa_id_5_obj
                elif e_str=="CIT" and empresa_id_2_obj: emp_asig=empresa_id_2_obj
                elif e_str=="TOURLINE EXPRESS S.A.S" and empresa_id_6_obj: emp_asig=empresa_id_6_obj
                
                veh_defs.update({'numeroMotor':to_str_or_none(safe_get(val1_series,'MOTOR')), 'chasis':to_str_or_none(safe_get(val1_series,'CHASIS')),
                    'vin':to_str_or_none(safe_get(val1_series,'VIN')), 'licenciaTransito':to_str_or_none(safe_get(val1_series,'LICENCIA TRANSITO')),
                    'modelo':to_int_or_none(safe_get(val1_series,'MODELO')), 'paxLt':to_int_or_none(safe_get(val1_series,'CAP LICENCIA'))})
                cls_str = to_str_or_none(safe_get(val1_series,'CLASE'))
                if cls_str and not veh_defs.get('clase'): veh_defs['clase'] = self._get_or_create_fk_by_name(ClaseVehiculo, cls_str, 'nombre', errors_log, record_id_str)

            if emp_asig: veh_defs['empresa'] = emp_asig

            if main_row is not None:
                veh_defs['empresa'] = emp_asig or get_fk_object_from_map(safe_get(main_row, 'empresaDirecta'), map_vars['empresas_map'], "Empresa", record_id_str, errors_log, "empresaDirecta")
                veh_defs['marca'] = get_fk_object_from_map(safe_get(main_row, 'marcaID'), map_vars['marca_map'], "Marca", record_id_str, errors_log, "marcaID") or veh_defs.get('marca')
                
                marca_for_linea = veh_defs.get('marca')
                tipo_linea_id_from_excel = safe_get(main_row, 'tipoLinea')
                linea_obj_from_map = None
                if tipo_linea_id_from_excel is not None:
                    linea_obj_from_map = map_vars['tipo_linea_map'].get(to_int_or_none(tipo_linea_id_from_excel))

                if linea_obj_from_map:
                    if marca_for_linea and hasattr(linea_obj_from_map, 'marca') and linea_obj_from_map.marca == marca_for_linea:
                        veh_defs['tipoLinea'] = linea_obj_from_map
                    elif not hasattr(linea_obj_from_map, 'marca'):
                         veh_defs['tipoLinea'] = linea_obj_from_map
                
                veh_defs['tipoLinea'] = veh_defs.get('tipoLinea')

                veh_defs['paxLt'] = to_int_or_none(safe_get(main_row, 'pax_lt')) or veh_defs.get('paxLt')
                veh_defs['paxRl'] = to_int_or_none(safe_get(main_row, 'pax_real')) or veh_defs.get('paxRl')
                veh_defs['clase'] = get_fk_object_from_map(safe_get(main_row, 'claseVehicID'), map_vars['clase_vehiculo_map'], "ClaseVehiculo", record_id_str, errors_log, "claseVehicID") or veh_defs.get('clase')
                veh_defs['carroceria'] = get_fk_object_from_map(safe_get(main_row, 'carroceriaID'), map_vars['carroceria_map'], "Carroceria", record_id_str, errors_log, "carroceriaID") or veh_defs.get('carroceria')
                veh_defs['numeroMotor'] = to_str_or_none(safe_get(main_row, 'numMotorVehiculo')) or veh_defs.get('numeroMotor')
                veh_defs['tipoMotor'] = to_str_or_none(safe_get(main_row, 'tipoMotor')) or veh_defs.get('tipoMotor')
                veh_defs['combustible'] = get_fk_object_from_map(safe_get(main_row, 'combustibleID'), map_vars['combustible_map'], "Combustible", record_id_str, errors_log, "combustibleID") or veh_defs.get('combustible')
                veh_defs['chasis'] = to_str_or_none(safe_get(main_row, 'numChasisVehiculo')) or veh_defs.get('chasis')
                veh_defs['serie'] = to_str_or_none(safe_get(main_row, 'numSerieVehiculo')) or veh_defs.get('serie')
                veh_defs['vin'] = to_str_or_none(safe_get(main_row, 'numVin')) or veh_defs.get('vin')
                veh_defs['ciudadBase'] = get_fk_object_from_map(safe_get(main_row, 'ciudadID'), map_vars['ciudad_map'], "Ciudad", record_id_str, errors_log, "ciudadID") or veh_defs.get('ciudadBase')
                veh_defs['modelo'] = to_int_or_none(safe_get(main_row, 'modelo')) or veh_defs.get('modelo')
                veh_defs['numeroEjes'] = to_int_or_none(safe_get(main_row, 'configuracionEjes')) or veh_defs.get('numeroEjes')
                veh_defs['cilindraje'] = to_int_or_none(safe_get(main_row, 'cilindraje')) or veh_defs.get('cilindraje')
                veh_defs['licenciaTransito'] = to_str_or_none(safe_get(main_row, 'licenciaTransito')) or veh_defs.get('licenciaTransito')
                veh_defs['color'] = get_fk_object_from_map(safe_get(main_row, 'colorID'), map_vars['color_map'], "Color", record_id_str, errors_log, "colorID") or veh_defs.get('color')
                veh_defs['unionTemporal'] = (to_str_or_none(safe_get(main_row, 'vehiculoUnion', '0')) == '1')
            
            veh_defs['estado'] = 'ACTIVO' 
            veh_defs.pop('fechaMatricula', None) 

            veh_defs['serie'] = make_unique_placeholder(placa_upper, 'serie', veh_defs.get('serie'), 100)
            veh_defs['chasis'] = make_unique_placeholder(placa_upper, 'chasis', veh_defs.get('chasis'), 100)
            veh_defs['vin'] = make_unique_placeholder(placa_upper, 'vin', veh_defs.get('vin'), 100)
            veh_defs['licenciaTransito'] = make_unique_placeholder(placa_upper, 'licenciaTransito', veh_defs.get('licenciaTransito'), 100)


            for field in Vehiculos._meta.get_fields():
                if not field.concrete: continue 
                if field.name not in veh_defs or veh_defs.get(field.name) is None:
                    if hasattr(field, 'null') and not field.null and not field.primary_key: 
                        if field.is_relation:
                            fk_model_class = field.related_model
                            if fk_model_class == Empresas:
                                if empresa_id_1_obj: veh_defs[field.name] = empresa_id_1_obj
                                else: 
                                    if not generic_empresa_super_obj: generic_empresa_super_obj, _ = Empresas.objects.get_or_create(nit=generic_empresa_nit_super_gen, defaults={'nombre_empresa': "EMPRESA SUPER GENÉRICA", 'telefono1':0, 'email': 'gen@gen.com'})
                                    veh_defs[field.name] = generic_empresa_super_obj
                            else:
                                gnm = { Marca: ('nombre', "MARCA GENÉRICA"), ClaseVehiculo: ('nombre', "CLASE GENÉRICA"), 
                                        TipoLinea: ('nombre', "LINEA GENÉRICA"), 
                                        Carroceria: ('nombre', "CARROCERIA GENÉRICA"), Combustible: ('nombre', "COMBUSTIBLE GENÉRICO"), 
                                        Ciudad: ('nombre', "CIUDAD GENÉRICA"), Color: ('nombre', "COLOR GENÉRICA")}
                                if fk_model_class in gnm:
                                    name_attr, gen_name = gnm[fk_model_class]
                                    fk_c_args = {}
                                    if fk_model_class == TipoLinea:
                                        current_marca_obj = veh_defs.get('marca')
                                        if current_marca_obj and isinstance(current_marca_obj, Marca):
                                            fk_c_args['marca'] = current_marca_obj
                                        else: 
                                            generic_marca, _ = Marca.objects.get_or_create(nombre="MARCA GENÉRICA PARA LINEA")
                                            fk_c_args['marca'] = generic_marca
                                    
                                    fk_obj = self._get_or_create_fk_by_name(fk_model_class, gen_name, name_attr, errors_log, record_id_str + " (Generic FK)", fk_c_args)
                                    if fk_obj: veh_defs[field.name] = fk_obj
                        elif isinstance(field, (django_models.IntegerField, django_models.PositiveIntegerField, django_models.FloatField, django_models.DecimalField)): 
                            veh_defs[field.name] = field.default if field.has_default() else 0
                        elif isinstance(field, (django_models.CharField, django_models.TextField)): 
                            veh_defs[field.name] = field.default if field.has_default() else ("" if field.blank else "N/A")
                        elif isinstance(field, django_models.BooleanField): 
                            veh_defs[field.name] = field.default if field.has_default() else False
                        elif isinstance(field, django_models.DateField) and not field.auto_now and not field.auto_now_add : 
                            veh_defs[field.name] = field.default if field.has_default() else date(1900,1,1)
            
            final_veh_defs = {k: v for k, v in veh_defs.items() if hasattr(Vehiculos, k.split('__')[0]) and k != 'placa'} 
            if 'placa' not in veh_defs and placa_upper : veh_defs['placa'] = placa_upper 

            
            try:
                vehiculo_obj, v_created = Vehiculos.objects.update_or_create(placa=placa_upper, defaults=final_veh_defs )
                if excel_vehiculo_id is not None: map_vars['vehiculos_map_excel_id_to_django_obj'][excel_vehiculo_id] = vehiculo_obj
                count_vehiculos_processed += 1

                if placa_upper in placas_with_validator_owners and owner_details:
                    VehiculoPropietario.objects.filter(vehiculo=vehiculo_obj).delete()
                    num_o = len(owner_details); porc = round(100/num_o) if num_o > 0 else 0
                    calculated_total_porc = 0
                    for od_idx, od in enumerate(owner_details):
                        prop_id = to_str_or_none(od.get('id'))
                        if not prop_id: continue
                        
                        prop_obj = propietarios_cache_by_identificacion.get(prop_id)
                        if not prop_obj:
                            prop_data = {
                                'tipoDocumento': tipo_doc_default,
                                'nombres': od.get('n'),
                                'apellidos': od.get('a'),
                                'telefono': to_str_or_none(od.get('tel')),
                                'correo': to_str_or_none(od.get('cor')),
                            }
                            valid_prop_data = {k_prop: v_prop for k_prop, v_prop in prop_data.items() if hasattr(Propietario, k_prop)}
                            
                            prop_obj, _ = Propietario.objects.update_or_create(
                                identificacion=prop_id, 
                                defaults=valid_prop_data
                            )
                            propietarios_cache_by_identificacion[prop_id] = prop_obj
                        
                        current_porc = porc
                        if num_o > 0 and od_idx == num_o - 1 : 
                            current_porc = 100 - calculated_total_porc
                        
                        VehiculoPropietario.objects.update_or_create(vehiculo=vehiculo_obj,propietario=prop_obj,defaults={'porcentaje':current_porc})
                        if num_o > 0 and od_idx < num_o -1:
                            calculated_total_porc += current_porc
                
                svc_fks, svc_data = {}, {}
                if main_row is not None:
                    svc_fks['empresaOficial'] = vehiculo_obj.empresa 
                    svc_fks['empresaAdministra'] = get_fk_object_from_map(safe_get(main_row,'empresaAdministradora'), map_vars['empresas_map'], "EmpAdmin",record_id_str,errors_log,"empresaAdministradora")
                    svc_fks['tipoOperacion'] = get_fk_object_from_map(safe_get(main_row,'tipoOperacionID'),map_vars['tipo_operacion_map'],"TipoOp",record_id_str,errors_log,"tipoOperacionID")
                    svc_fks['nivelServicio'] = get_fk_object_from_map(safe_get(main_row,'nivelServicioID'),map_vars['nivel_servicio_map'],"NivelSvc",record_id_str,errors_log,"nivelServicioID")
                    svc_fks['servicio'] = get_fk_object_from_map(safe_get(main_row,'categoriaID'),map_vars['categoria_map'],"CatSvc",record_id_str,errors_log,"categoriaID") 
                    svc_data['numeroInterno'] = to_int_or_none(safe_get(main_row,'numero_Vehiculo'))
                    svc_data['fechaIngreso'] = to_date_or_none(safe_get(main_row,'fechaInicioServicio'))
                    svc_data['fechaFinServicio'] = to_date_or_none(safe_get(main_row,'fechaFinServicio'))
                else: 
                    svc_fks['empresaOficial'] = vehiculo_obj.empresa 
                    if val2_dict:
                        svc_data['numeroInterno'] = to_int_or_none(val2_dict.get('No Interno'))
                        svc_data['fechaIngreso'] = to_date_or_none(val2_dict.get('FECHA AFILIACION'))
                    elif val1_series is not None:
                        svc_data['fechaIngreso'] = to_date_or_none(safe_get(val1_series,'fechaInicioServicio o vinculacion radicacion t.-operación o expedicion'))
                
                cln_svc_defs = {k:v for k,v in {**svc_fks, **svc_data}.items() if v is not None}
                
                required_servicio_fields_present = all([
                    vehiculo_obj,
                    cln_svc_defs.get('empresaOficial'),
                    cln_svc_defs.get('fechaIngreso') 
                ])

                if required_servicio_fields_present:
                    valid_servicio_defs = {k: v for k, v in cln_svc_defs.items() if hasattr(Servicio, k)}
                    try: 
                        Servicio.objects.update_or_create(vehiculo=vehiculo_obj, defaults=valid_servicio_defs)
                    except Exception as e_svc: 
                        errors_log.append(f"Servicio para {placa_upper} falló: {type(e_svc).__name__} - {e_svc}. Datos: {valid_servicio_defs}")

            except IntegrityError as ie_veh:
                errors_log.append(f"FALLO CREACIÓN/ACTUALIZACIÓN (IntegrityError) Vehículo {placa_upper} (Fuente: {current_source_file_info}): {ie_veh}. DATOS INTENTADOS: {final_veh_defs}")
            except Exception as e_veh:
                errors_log.append(f"FALLO CREACIÓN/ACTUALIZACIÓN (Exception) Vehículo {placa_upper} (Fuente: {current_source_file_info}): {type(e_veh).__name__} - {e_veh}. DATOS INTENTADOS: {final_veh_defs}")
        
        summary['Vehiculos (Intentados Crear/Actualizar)'] = f"{count_vehiculos_processed}"

        try:
            df_vp = pd.read_excel(excel_file_path, sheet_name='propietariosVehiculo', dtype=str)
            for _, row in df_vp.iterrows():
                p_id, v_id, porc = to_int_or_none(row.get('propietariosID')), to_int_or_none(row.get('vehiculoID')), to_int_or_none(row.get('porcentaje'))
                if p_id is None or v_id is None or porc is None: continue
                
                v_obj = map_vars['vehiculos_map_excel_id_to_django_obj'].get(v_id)
                p_obj = map_vars['propietarios_map_excel_id_to_django_obj'].get(p_id)

                if not v_obj or not p_obj : continue
                if v_obj.placa.upper() in placas_with_validator_owners: continue 

                try: 
                    VehiculoPropietario.objects.update_or_create(vehiculo=v_obj, propietario=p_obj, defaults={'porcentaje': porc})
                except Exception as e_vp: errors_log.append(f"VehiculoPropietario (fallback) {v_obj.placa}-{p_obj.identificacion} falló: {e_vp}")
        except FileNotFoundError: pass
        except Exception as e: errors_log.append(f"Error hoja 'propietariosVehiculo': {e}")

        self.stdout.write(self.style.SUCCESS("\n--- Procesamiento de Documentos de Vehículos ---"))
        
        aseguradoras_map, aseguradoras_by_name_map = {}, {}
        try:
            df_aseg = pd.read_excel(excel_file_path, sheet_name='Aseguradoras', dtype=str) 
            for _, row in df_aseg.iterrows():
                ex_id, nom_aseg = to_int_or_none(row.get('aseguradoraID')), to_str_or_none(row.get('DescripcionAseguradora'))
                if ex_id is not None and nom_aseg:
                    obj, _ = Aseguradora.objects.update_or_create(id=ex_id, defaults={'nombre': nom_aseg, 'nit': to_str_or_none(row.get('Nit'))})
                    aseguradoras_map[ex_id], aseguradoras_by_name_map[nom_aseg.upper()] = obj, obj
        except FileNotFoundError: pass
        except Exception as e: errors_log.append(f"Error hoja 'Aseguradoras': {e}")

        tipo_documento_vehiculo_map = {}
        try:
            df_tdv = pd.read_excel(excel_file_path, sheet_name='tipoDocumentoVehiculo', dtype=str)
            for _, row in df_tdv.iterrows():
                ex_id, nom_doc = to_int_or_none(row.get('tipoDocumentoID')), to_str_or_none(row.get('detalleDocumento'))
                if ex_id is not None and nom_doc:
                    obj, _ = TipoDocumentoVehiculo.objects.update_or_create(id=ex_id, defaults={'nombre': nom_doc})
                    tipo_documento_vehiculo_map[ex_id] = obj 
        except FileNotFoundError: errors_log.append(f"AdvertenciaCRITICA: Hoja 'tipoDocumentoVehiculo' no encontrada.")
        except Exception as e: errors_log.append(f"Error crítico hoja 'tipoDocumentoVehiculo': {e}")

        tipos_doc_obj = {i: tipo_documento_vehiculo_map.get(i) for i in range(1, 11)} 

        if tipo_documento_vehiculo_map: 
            for sheet_name, is_historic in [('documentosVehiculo', False), ('historicoDocumentosVehiculo', True)]: 
                try:
                    df_docs = pd.read_excel(excel_file_path, sheet_name=sheet_name, dtype=str)
                    for _, row in df_docs.iterrows():
                        ex_veh_id = to_int_or_none(row.get('vehiculo'))
                        veh_obj = map_vars['vehiculos_map_excel_id_to_django_obj'].get(ex_veh_id)
                        if not veh_obj: continue
                        
                        ex_tipo_doc_id = to_int_or_none(row.get('tipoDocumentoID'))
                        tipo_doc_obj_instance = tipos_doc_obj.get(ex_tipo_doc_id)
                        if not tipo_doc_obj_instance: continue

                        num_doc, fec_exp, fec_ini_v, fec_fin_v = to_str_or_none(row.get('numeroDocumento')), to_date_or_none(row.get('fechaExpedicion')), to_date_or_none(row.get('fechaIniVigencia')), to_date_or_none(row.get('fechaFinVigencia'))
                        sop_raw, sop_path = to_str_or_none(row.get('archivoSoporte')), None
                        if sop_raw: sop_path = f"{SOPORTE_URL_PREFIX}{sop_raw.lstrip('/')}"
                        
                        ex_aseg_id = to_int_or_none(row.get('aseguradoraID'))
                        aseg_obj = None
                        if ex_aseg_id is not None: aseg_obj = aseguradoras_map.get(ex_aseg_id)
                        
                        doc_defs = {'fecha_expedicion': fec_exp, 'soporte': sop_path, 
                                    'estado': (to_str_or_none(row.get('estado', '1' if not is_historic else '0')) == '1'), 
                                    'tipo_documento_vehiculo': tipo_doc_obj_instance, 'aseguradora': aseg_obj}
                        
                        excel_doc_id_val = to_int_or_none(row.get('documentosVehiculoID')) 
                        if excel_doc_id_val is not None:
                             doc_defs['excel_documento_id'] = excel_doc_id_val
                        
                        upd_keys = {'vehiculo': veh_obj}
                        model_to_use, req_fields_ok = None, False

                        doc_id_from_excel = to_str_or_none(row.get('documentosVehiculoID')) 

                        if tipo_doc_obj_instance.id in [1, 4, 5, 6] and num_doc is None: num_doc = f"DEF-{doc_id_from_excel if doc_id_from_excel else 'NO_NUM'}"


                        if tipo_doc_obj_instance.id == 1 and tipos_doc_obj[1]: 
                            model_to_use, req_fields_ok = Soat, all([fec_exp, fec_ini_v, fec_fin_v, num_doc])
                            if req_fields_ok: upd_keys.update({'numero_poliza': num_doc, 'vigencia_hasta': fec_fin_v}); doc_defs.update({'vigencia_desde': fec_ini_v, 'aseguradora_nombre': aseg_obj.nombre if aseg_obj else None, 'placa': veh_obj.placa})
                        elif tipo_doc_obj_instance.id == 2 and tipos_doc_obj[2]: 
                            model_to_use, req_fields_ok = TarjetaOperacion, all([fec_exp, fec_ini_v, fec_fin_v, num_doc])
                            if req_fields_ok: upd_keys.update({'numero': num_doc, 'fechaFinVigencia': fec_fin_v}); doc_defs.update({'fechaInicialVigencia': fec_ini_v, 'placa': veh_obj.placa})
                        elif tipo_doc_obj_instance.id == 3 and tipos_doc_obj[3]: 
                            model_to_use, req_fields_ok = RevisionTecnomecanica, all([fec_exp, fec_fin_v, num_doc])
                            if req_fields_ok: upd_keys.update({'no_certificado': num_doc, 'fecha_vencimiento': fec_fin_v}); doc_defs.update({'placa': veh_obj.placa})
                        elif tipo_doc_obj_instance.id == 4 and tipos_doc_obj[4]: 
                            model_to_use, req_fields_ok = PolizaContractual, all([num_doc, fec_fin_v])
                            if req_fields_ok: upd_keys.update({'numero_poliza': num_doc, 'fecha_fin_vigencia': fec_fin_v}); doc_defs.update({'fecha_inicio_vigencia': fec_ini_v, 'aseguradora_nombre_alt': aseg_obj.nombre if aseg_obj else None})
                        elif tipo_doc_obj_instance.id == 5 and tipos_doc_obj[5]: 
                            model_to_use, req_fields_ok = PolizaExtracontractual, all([num_doc, fec_fin_v])
                            if req_fields_ok: upd_keys.update({'numero_poliza': num_doc, 'fecha_fin_vigencia': fec_fin_v}); doc_defs.update({'fecha_inicio_vigencia': fec_ini_v, 'aseguradora_nombre_alt': aseg_obj.nombre if aseg_obj else None})
                        elif tipo_doc_obj_instance.id == 6 and tipos_doc_obj[6]: 
                            model_to_use, req_fields_ok = PolizaTodoRiesgo, all([num_doc, fec_fin_v])
                            if req_fields_ok: upd_keys.update({'numero_poliza': num_doc, 'fecha_fin_vigencia': fec_fin_v}); doc_defs.update({'fecha_inicio_vigencia': fec_ini_v, 'aseguradora_nombre_alt': aseg_obj.nombre if aseg_obj else None})
                        elif tipo_doc_obj_instance.id == 7 and tipos_doc_obj[7]: 
                            model_to_use = FichaTecnicaHomologacionChasis
                            req_fields_ok = True 
                            upd_keys.update({'numero_documento': num_doc if num_doc else None, 'fecha_expedicion': fec_exp}) 
                            if num_doc is None and sop_path: upd_keys['soporte'] = sop_path 
                            doc_defs.pop('excel_documento_id', None) 
                        elif tipo_doc_obj_instance.id == 8 and tipos_doc_obj[8]: 
                            model_to_use = FichaTecnicaHomologacionCarroceria
                            req_fields_ok = True 
                            upd_keys.update({'numero_documento': num_doc if num_doc else None, 'fecha_expedicion': fec_exp})
                            if num_doc is None and sop_path: upd_keys['soporte'] = sop_path
                            doc_defs.pop('excel_documento_id', None)
                        elif tipo_doc_obj_instance.id == 9 and tipos_doc_obj[9]: 
                            model_to_use = FichaTecnicaHomologacionVehCarrozado
                            req_fields_ok = True
                            upd_keys.update({'numero_documento': num_doc if num_doc else None, 'fecha_expedicion': fec_exp})
                            if num_doc is None and sop_path: upd_keys['soporte'] = sop_path
                            doc_defs.pop('excel_documento_id', None)
                        elif tipo_doc_obj_instance.id == 10 and tipos_doc_obj[10]: 
                            model_to_use, req_fields_ok = LicenciaTransito, all([num_doc])
                            if req_fields_ok: upd_keys.update({'numero_documento': num_doc}); doc_defs.update({'fecha_inicio_vigencia': fec_ini_v, 'fecha_fin_vigencia': fec_fin_v, 'fecha_expedicion': fec_exp})
                        
                        if model_to_use and req_fields_ok:
                            valid_upd_keys = {k:v for k,v in upd_keys.items() if hasattr(model_to_use, k.split('__')[0])}
                            valid_doc_defs = {k:v for k,v in doc_defs.items() if hasattr(model_to_use, k.split('__')[0])}
                            
                            if tipo_doc_obj_instance.id in [7,8,9] and valid_upd_keys.get('numero_documento') is None:
                                valid_upd_keys.pop('numero_documento', None)
                                if 'soporte' not in valid_upd_keys and sop_path: 
                                    valid_upd_keys['soporte'] = sop_path

                            try: 
                                model_to_use.objects.update_or_create(**valid_upd_keys, defaults=valid_doc_defs)
                            except Exception as e_doc_spec: 
                                errors_log.append(f"Doc {num_doc or sop_path} ({tipo_doc_obj_instance.nombre}) para {veh_obj.placa} (Hoja: {sheet_name}) falló: {type(e_doc_spec).__name__} - {e_doc_spec}. Lookup: {valid_upd_keys}, Defaults: {valid_doc_defs}")
                except FileNotFoundError: 
                    if sheet_name == 'documentosVehiculo': 
                        errors_log.append(f"AdvertenciaCRITICA: Hoja '{sheet_name}' no encontrada.")
                except Exception as e: errors_log.append(f"Error hoja docs '{sheet_name}': {e}")

        self.stdout.write(self.style.SUCCESS(f"\n--- Procesamiento de Documentos desde Validadores ---"))
        for vehiculo_db_obj in Vehiculos.objects.all().prefetch_related('empresa'): 
            placa_db = vehiculo_db_obj.placa.upper()
            val_row_data, src_file_indicator = (validator2_data_map.get(placa_db), "v2") if placa_db in validator2_data_map else \
                                         (validator1_data_map.get(placa_db), "v1") if placa_db in validator1_data_map else (None, None)
            if val_row_data is None or \
               (not isinstance(val_row_data, pd.Series) and not val_row_data):
                continue
            
            try:
                doc_defaults_common = {'estado':True, 'placa':placa_db, 'vehiculo': vehiculo_db_obj}

                if src_file_indicator == "v1":
                    num_s, fv_s, aseg_n_s = to_str_or_none(safe_get(val_row_data,'NUMERO SOAT')), to_date_or_none(safe_get(val_row_data,'FECHA VENCIMIENTO SOAT')), to_str_or_none(safe_get(val_row_data,'ASEGURADORA'))
                    aseg_o_val = aseguradoras_by_name_map.get(aseg_n_s.upper()) if aseg_n_s else None
                    if num_s and fv_s and tipos_doc_obj.get(1): 
                        Soat.objects.update_or_create(vehiculo=vehiculo_db_obj,numero_poliza=num_s,vigencia_hasta=fv_s,defaults={**doc_defaults_common, 'fecha_expedicion':fv_s,'vigencia_desde':fv_s,'aseguradora_nombre':aseg_n_s,'aseguradora':aseg_o_val,'tipo_documento_vehiculo':tipos_doc_obj[1]})
                    
                    num_t, fv_t = to_str_or_none(safe_get(val_row_data,'NUMERO TECNICOMECANICA')), to_date_or_none(safe_get(val_row_data,'FECHA VENCIMIENTO REVISION TECNICO MECANICA'))
                    if num_t and fv_t and tipos_doc_obj.get(3): 
                        RevisionTecnomecanica.objects.update_or_create(vehiculo=vehiculo_db_obj,no_certificado=num_t,fecha_vencimiento=fv_t,defaults={**doc_defaults_common, 'fecha_expedicion':fv_t,'tipo_documento_vehiculo':tipos_doc_obj[3]})
                    
                    num_to, fv_to = to_str_or_none(safe_get(val_row_data,'NUMERO TARJETA OPERACIÓN')), to_date_or_none(safe_get(val_row_data,'FECHA VENCIMIENTO TARJETA DE OPERACIÓN'))
                    if num_to and fv_to and tipos_doc_obj.get(2): 
                        TarjetaOperacion.objects.update_or_create(vehiculo=vehiculo_db_obj,numero=num_to,fechaFinVigencia=fv_to,defaults={**doc_defaults_common, 'fechaExpedicion':fv_to,'fechaInicialVigencia':fv_to,'tipo_documento_vehiculo':tipos_doc_obj[2]})
                    
                    num_l = to_str_or_none(safe_get(val_row_data,'LICENCIA TRANSITO'))
                    if num_l and tipos_doc_obj.get(10): 
                        LicenciaTransito.objects.update_or_create(vehiculo=vehiculo_db_obj,numero_documento=num_l,defaults={**doc_defaults_common, 'tipo_documento_vehiculo':tipos_doc_obj[10]})
                        if vehiculo_db_obj.licenciaTransito != num_l : vehiculo_db_obj.licenciaTransito=num_l; vehiculo_db_obj.save(update_fields=['licenciaTransito'])

                    num_pc, fv_pc = to_str_or_none(safe_get(val_row_data,'NUMERO POLIZA CONTRACTUAL')), to_date_or_none(safe_get(val_row_data,'FECHA VENCIMIENTO CONTRACTUAL'))
                    if num_pc and fv_pc and tipos_doc_obj.get(4): 
                        PolizaContractual.objects.update_or_create(vehiculo=vehiculo_db_obj,numero_poliza=num_pc,fecha_fin_vigencia=fv_pc,defaults={**doc_defaults_common, 'aseguradora_nombre_alt':aseg_n_s,'aseguradora':aseg_o_val,'tipo_documento_vehiculo':tipos_doc_obj[4]})
                    
                    num_pe, fv_pe = to_str_or_none(safe_get(val_row_data,'NUMERO POLIZA EXCONTRACTUAL')), to_date_or_none(safe_get(val_row_data,'FECHA VENCIMIENTO EXTRACONTRACTUAL'))
                    if num_pe and fv_pe and tipos_doc_obj.get(5): 
                        PolizaExtracontractual.objects.update_or_create(vehiculo=vehiculo_db_obj,numero_poliza=num_pe,fecha_fin_vigencia=fv_pe,defaults={**doc_defaults_common, 'aseguradora_nombre_alt':aseg_n_s,'aseguradora':aseg_o_val,'tipo_documento_vehiculo':tipos_doc_obj[5]})

                elif src_file_indicator == "v2":
                    num_s, fv_s = to_str_or_none(val_row_data.get('SOAT NUMERO')), to_date_or_none(val_row_data.get('SOAT FECHA VENCIMIENTO'))
                    if num_s and fv_s and tipos_doc_obj.get(1): 
                        Soat.objects.update_or_create(vehiculo=vehiculo_db_obj,numero_poliza=num_s,vigencia_hasta=fv_s,defaults={**doc_defaults_common, 'fecha_expedicion':fv_s,'vigencia_desde':fv_s,'tipo_documento_vehiculo':tipos_doc_obj[1]})
                    
                    num_t, fv_t = to_str_or_none(val_row_data.get('TECNOMECANICA NUMERO')), to_date_or_none(val_row_data.get('TECNOMECANICA FECHA VENCIMIENTO'))
                    if num_t and fv_t and tipos_doc_obj.get(3): 
                        RevisionTecnomecanica.objects.update_or_create(vehiculo=vehiculo_db_obj,no_certificado=num_t,fecha_vencimiento=fv_t,defaults={**doc_defaults_common, 'fecha_expedicion':fv_t,'tipo_documento_vehiculo':tipos_doc_obj[3]})
                    
                    num_to, fv_to = to_str_or_none(val_row_data.get('TARJETA OPERACIÓN No')), to_date_or_none(val_row_data.get('VENCIMIENTO TARJETA OPERACIÓN'))
                    if num_to and fv_to and tipos_doc_obj.get(2): 
                        TarjetaOperacion.objects.update_or_create(vehiculo=vehiculo_db_obj,numero=num_to,fechaFinVigencia=fv_to,defaults={**doc_defaults_common, 'fechaExpedicion':fv_to,'fechaInicialVigencia':fv_to,'tipo_documento_vehiculo':tipos_doc_obj[2]})
                    
                    num_l = to_str_or_none(val_row_data.get('No LICENCIA TRANSITO'))
                    if num_l and tipos_doc_obj.get(10): 
                        LicenciaTransito.objects.update_or_create(vehiculo=vehiculo_db_obj,numero_documento=num_l,defaults={**doc_defaults_common, 'tipo_documento_vehiculo':tipos_doc_obj[10]})
                        if vehiculo_db_obj.licenciaTransito != num_l : vehiculo_db_obj.licenciaTransito=num_l; vehiculo_db_obj.save(update_fields=['licenciaTransito'])

                    pol_key = next((k for k in val_row_data if isinstance(k,str) and 'R.C. C. POLIZA' in k.upper() and 'R.C. E. POLIZA' in k.upper()),None) 
                    pol_fld_val, fv_pol_val = (to_str_or_none(val_row_data.get(pol_key)) if pol_key else None), to_date_or_none(val_row_data.get('VENCIMIENTO POLIZA'))
                    
                    if pol_fld_val and fv_pol_val:
                        mc_match, me_match = re.search(r"R\.C\. C\. POLIZA\s*([^\s/]+)",pol_fld_val,re.I), re.search(r"R\.C\. E\. POLIZA\s*([^\s/]+)",pol_fld_val,re.I)
                        if mc_match and tipos_doc_obj.get(4): 
                            PolizaContractual.objects.update_or_create(vehiculo=vehiculo_db_obj,numero_poliza=mc_match.group(1),fecha_fin_vigencia=fv_pol_val,defaults={**doc_defaults_common,'tipo_documento_vehiculo':tipos_doc_obj[4]})
                        if me_match and tipos_doc_obj.get(5): 
                            PolizaExtracontractual.objects.update_or_create(vehiculo=vehiculo_db_obj,numero_poliza=me_match.group(1),fecha_fin_vigencia=fv_pol_val,defaults={**doc_defaults_common,'tipo_documento_vehiculo':tipos_doc_obj[5]})
            except Exception as e_val_d: 
                errors_log.append(f"Doc Validador {placa_db} falló: {type(e_val_d).__name__} - {e_val_d}")


        self.stdout.write(self.style.SUCCESS("\n--- Resumen de Importación ---"))
        for item, msg in summary.items(): self.stdout.write(f"{item}: {msg}")

        if errors_log:
            self.stdout.write(self.style.ERROR("\n--- Errores Encontrados ---"))
            crit_errs = [e for e in errors_log if "CRÍTICO" in e.upper() or "FALLO CREACIÓN" in e.upper() or "INTEGRITYERROR" in e.upper()]
            oth_errs = [e for e in errors_log if not ("CRÍTICO" in e.upper() or "FALLO CREACIÓN" in e.upper() or "INTEGRITYERROR" in e.upper())]
            
            if crit_errs:
                self.stdout.write(self.style.ERROR("\n--- ERRORES CRÍTICOS / FALLOS DE CREACIÓN / INTEGRITY ---"))
                for error in crit_errs: self.stdout.write(self.style.ERROR(error))
            if oth_errs:
                self.stdout.write(self.style.WARNING("\n--- OTROS ERRORES Y ADVERTENCIAS ---"))
                for error in oth_errs: self.stdout.write(self.style.WARNING(error))
            self.stdout.write(self.style.ERROR(f"\nSe encontraron {len(errors_log)} errores/advertencias en total."))
        else:
            self.stdout.write(self.style.SUCCESS("\nImportación completada exitosamente."))