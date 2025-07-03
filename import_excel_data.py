import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
import math
from django.shortcuts import get_object_or_404

from myapp.models import (
    TipoDocumento, Empresas, Vehiculos, Propietario, Marca, TipoLinea,
    ClaseVehiculo, Carroceria, Combustible, TipoOperacion, Ciudad, NivelServicio,
    Categoria, Color, VehiculoPropietario, Servicio
)


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
    return str(value).strip()

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
            if value > 20000: 
                return (pd.to_datetime('1899-12-30') + pd.to_timedelta(value, 'D')).date()
            else: 
                return None 
        dt = pd.to_datetime(value, errors='coerce')
        return dt.date() if pd.notna(dt) else None
    except (ValueError, TypeError, OverflowError):
        return None

def get_fk_object_from_map(excel_id_val, object_map, object_model_name, record_identifier_str, errors_list, excel_column_name_str):
    if excel_id_val is None:
        return None
    
    id_lookup = to_int_or_none(excel_id_val)
    if id_lookup is None:
        errors_list.append(f"{object_model_name} para '{record_identifier_str}': ID '{excel_id_val}' (de columna '{excel_column_name_str}') no es un entero válido.")
        return None
        
    fk_object = object_map.get(id_lookup)
    if fk_object is None:
        errors_list.append(f"{object_model_name} para '{record_identifier_str}': ID '{id_lookup}' (de columna '{excel_column_name_str}') no encontrado en el mapa de {object_model_name}s.")
    return fk_object


class Command(BaseCommand):
    help = 'Import data from Excel file into Django models, prioritizing validator files and creating Servicio records'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the main Excel file (doc migracion.xlsx)')
        parser.add_argument('validator1_file', type=str, help='Path to the validator.xlsx file')
        parser.add_argument('validator2_file', type=str, help='Path to the validator2.xlsx file')

    @transaction.atomic
    def handle(self, *args, **options):
        excel_file_path = options['excel_file']
        validator1_file_path = options['validator1_file']
        validator2_file_path = options['validator2_file']
        
        errors_log = []
        summary = {}

        self.stdout.write(f"Iniciando importación desde {excel_file_path}, con validadores {validator1_file_path} y {validator2_file_path}...")

        tipo_doc_default, created = TipoDocumento.objects.get_or_create(
            id=1,
            defaults={'nombre': 'CÉDULA DE CIUDADANÍA'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"TipoDocumento default (ID:1 CÉDULA DE CIUDADANÍA) creado."))
        summary['TipoDocumento (Default)'] = "Asegurado/Creado"

        tipo_operacion_map = {}
        combustible_map = {}
        carroceria_map = {}
        marca_map = {}
        tipo_linea_map = {}
        nivel_servicio_map = {}
        clase_vehiculo_map = {}
        categoria_map = {}
        color_map = {}
        ciudad_map = {}
        empresas_map = {}
        propietarios_map_excel_id_to_django_obj = {} 
        vehiculos_map_excel_id_to_django_obj = {}
        
        placas_with_validator_owners = set()
        propietarios_cache_by_identificacion = {}

        validator1_data_map = {}
        try:
            df_val1 = pd.read_excel(validator1_file_path, sheet_name=0)
            for index, row in df_val1.iterrows():
                placa = to_str_or_none(safe_get(row, 'PLACA'))
                if placa:
                    validator1_data_map[placa.upper()] = row
            summary['Validator1 (validator.xlsx)'] = f"{len(validator1_data_map)} registros cargados."
        except Exception as e:
            errors_log.append(f"Error leyendo validator.xlsx: {e}")

        validator2_data_map = {}
        try:
            df_val2 = pd.read_excel(validator2_file_path, sheet_name=0)
            cedula_p1_col_name = 'CEDULA'
            cedula_p2_col_name = df_val2.columns[8] if len(df_val2.columns) > 8 else None

            for index, row in df_val2.iterrows():
                placa = to_str_or_none(safe_get(row, 'PLACA'))
                if placa:
                    row_data = row.to_dict()
                    row_data['_cedula_p1_col_name'] = cedula_p1_col_name
                    row_data['_cedula_p2_col_name'] = cedula_p2_col_name
                    validator2_data_map[placa.upper()] = row_data
            summary['Validator2 (validator2.xlsx)'] = f"{len(validator2_data_map)} registros cargados."
        except Exception as e:
            errors_log.append(f"Error leyendo validator2.xlsx: {e}")

        sheets_to_process = [
            ('Tipos Operacion', TipoOperacion, tipo_operacion_map, 'tipoOperacionID', 'descripcionTipoOperacion'),
            ('tipoCombustible', Combustible, combustible_map, 'combustibleID', 'descripcionCombustible'),
            ('tipoCarroceria', Carroceria, carroceria_map, 'carroceriaID', 'DescripcionCarroceria'),
            ('marcas', Marca, marca_map, 'marcaID', 'DescripcionMarca'),
            ('LineasMarca', TipoLinea, tipo_linea_map, 'lineaID', 'detalleLinea'),
            ('nivelServicio', NivelServicio, nivel_servicio_map, 'nivelServicioID', 'DescripcionNivelServicio'),
            ('claseVehiculo', ClaseVehiculo, clase_vehiculo_map, 'claseVehicID', 'DescripcionClaseVehiculo'),
            ('categorias veh', Categoria, categoria_map, 'categoriaID', 'DescripcionCategoria'),
            ('colores-veh', Color, color_map, 'colorID', 'detalleColor'),
            ('Ciudades', Ciudad, ciudad_map, 'ciudadID', 'DescripcionCiudad'),
        ]

        for sheet_name, model, data_map, id_col_name, name_col in sheets_to_process:
            try:
                df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
                count = 0
                for index, row in df.iterrows():
                    nombre = to_str_or_none(safe_get(row, name_col))
                    excel_id_raw = safe_get(row, id_col_name)
                    excel_id = to_int_or_none(excel_id_raw)

                    if not nombre or excel_id is None:
                        errors_log.append(f"{model.__name__} fila {index+2} en '{sheet_name}': nombre o ID faltante/inválido (ID_raw='{excel_id_raw}').")
                        continue
                    try:
                        obj, created = model.objects.get_or_create(nombre=nombre)
                        data_map[excel_id] = obj
                        count += 1
                    except Exception as e:
                        errors_log.append(f"{model.__name__} Error fila {index+2} ('{nombre}') en '{sheet_name}': {e}")
                summary[model.__name__] = f"{count} procesados desde '{sheet_name}'."
            except Exception as e:
                errors_log.append(f"Error leyendo hoja '{sheet_name}': {e}")
        
        try:
            df_empresas = pd.read_excel(excel_file_path, sheet_name='Empresas')
            count = 0
            for index, row in df_empresas.iterrows():
                excel_id_raw = safe_get(row, 'empresaID')
                excel_id = to_int_or_none(excel_id_raw)
                nombre_empresa = to_str_or_none(safe_get(row, 'DescripcionEmpresa'))
                nit_excel = to_str_or_none(safe_get(row, 'nit'))

                if excel_id is None or not nombre_empresa or not nit_excel:
                    errors_log.append(f"Empresa fila {index+2}: ID ('{excel_id_raw}'), nombre o NIT faltante/inválido.")
                    continue
                try:
                    obj, created = Empresas.objects.update_or_create(
                        id=excel_id,
                        defaults={
                            'nombre_empresa': nombre_empresa,
                            'nit': nit_excel,
                            'direccion': to_str_or_none(safe_get(row, 'direccion')),
                            'telefono1': to_int_or_none(safe_get(row, 'Telefono1')),
                            'telefono2': to_int_or_none(safe_get(row, 'Telefono2')),
                            'email': to_str_or_none(safe_get(row, 'EMail')),
                            'estado': safe_get(row, 'estado', 1) == 1 
                        }
                    )
                    empresas_map[excel_id] = obj
                    count += 1
                except IntegrityError as e:
                    errors_log.append(f"Empresa Error de Integridad fila {index+2} (ID: {excel_id}, NIT: {nit_excel}): {e}.")
                except Exception as e:
                    errors_log.append(f"Empresa Error fila {index+2} (ID: {excel_id}, '{nombre_empresa}'): {e}")
            summary['Empresas'] = f"{count} procesadas."
        except Exception as e:
            errors_log.append(f"Error leyendo hoja 'Empresas': {e}")

        try:
            df_prop_main = pd.read_excel(excel_file_path, sheet_name='Propietarios')
            count = 0
            for index, row in df_prop_main.iterrows():
                identificacion_excel = to_str_or_none(safe_get(row, 'identificacion'))
                excel_propietario_id_raw = safe_get(row, 'propietariosID')
                excel_propietario_id = to_int_or_none(excel_propietario_id_raw)
                nombres_excel = to_str_or_none(safe_get(row, 'nombre'))

                if not identificacion_excel or not nombres_excel or excel_propietario_id is None:
                    errors_log.append(f"Propietario (doc migracion) fila {index+2}: identificación, nombre o propietariosID ('{excel_propietario_id_raw}') faltante/inválido.")
                    continue
                
                prop_defaults = {
                    'tipoDocumento': tipo_doc_default,
                    'nombres': nombres_excel,
                    'apellidos': to_str_or_none(safe_get(row, 'apellido')),
                    'telefono': to_str_or_none(safe_get(row, 'telefono')),
                    'correo': to_str_or_none(safe_get(row, 'correo')),
                }
                
                try:
                    obj, created = Propietario.objects.update_or_create(
                        identificacion=identificacion_excel,
                        defaults=prop_defaults
                    )
                    propietarios_map_excel_id_to_django_obj[excel_propietario_id] = obj
                    propietarios_cache_by_identificacion[identificacion_excel] = obj
                    count += 1
                except Exception as e:
                    errors_log.append(f"Propietario (doc migracion) Error fila {index+2} ('{identificacion_excel}'): {e}")
            summary['Propietarios (doc migracion)'] = f"{count} procesados."
        except Exception as e:
            errors_log.append(f"Error leyendo hoja 'Propietarios' de doc migracion: {e}")

        try:
            df_vehiculos = pd.read_excel(excel_file_path, sheet_name='Vehiculos')
            count_vehiculos = 0
            for index, row in df_vehiculos.iterrows():
                placa_excel_orig = safe_get(row, 'placa_Vehiculo')
                placa_excel = to_str_or_none(placa_excel_orig)
                excel_vehiculo_id_raw = safe_get(row, 'vehiculoID')
                excel_vehiculo_id = to_int_or_none(excel_vehiculo_id_raw)


                if not placa_excel or excel_vehiculo_id is None:
                    errors_log.append(f"Vehiculo fila {index+2}: placa o vehiculoID ('{excel_vehiculo_id_raw}') faltante/inválido.")
                    continue
                
                placa_upper = placa_excel.upper()
                record_id_str = f"Vehiculo {placa_excel} (ExcelVehiculoID: {excel_vehiculo_id})"
                vehicle_data_from_validator = {}
                owner_details_list_from_validator = []
                current_validator_source = None

                if placa_upper in validator2_data_map:
                    current_validator_source = "validator2.xlsx"
                    val_row_dict = validator2_data_map[placa_upper]
                    vehicle_data_from_validator['numeroMotor'] = to_str_or_none(val_row_dict.get('No MOTOR'))
                    vehicle_data_from_validator['serie'] = to_str_or_none(val_row_dict.get('No SERIE'))
                    vehicle_data_from_validator['chasis'] = to_str_or_none(val_row_dict.get('No CHASIS'))
                    
                    prop1_nombre_full = to_str_or_none(val_row_dict.get('PROPIETARIO 1'))
                    prop1_id = to_str_or_none(val_row_dict.get(val_row_dict.get('_cedula_p1_col_name')))
                    if prop1_id and prop1_nombre_full:
                        n, a = parse_propietario_name(prop1_nombre_full)
                        owner_details_list_from_validator.append({
                            'id': prop1_id, 'nombres': n, 'apellidos': a,
                            'telefono': to_str_or_none(val_row_dict.get('TELEFONO')),
                            'correo': to_str_or_none(val_row_dict.get('CORREO ELECTRONICO'))
                        })
                    
                    prop2_nombre_full = to_str_or_none(val_row_dict.get('PROPIETARIO2'))
                    prop2_id_col = val_row_dict.get('_cedula_p2_col_name')
                    prop2_id = to_str_or_none(val_row_dict.get(prop2_id_col)) if prop2_id_col else None
                    if prop2_id and prop2_nombre_full:
                        n, a = parse_propietario_name(prop2_nombre_full)
                        owner_details_list_from_validator.append({
                            'id': prop2_id, 'nombres': n, 'apellidos': a,
                            'telefono': None, 'correo': None 
                        })
                    if owner_details_list_from_validator:
                        placas_with_validator_owners.add(placa_upper)

                elif placa_upper in validator1_data_map:
                    current_validator_source = "validator.xlsx"
                    val_row_series = validator1_data_map[placa_upper]
                    vehicle_data_from_validator['numeroMotor'] = to_str_or_none(safe_get(val_row_series, 'MOTOR'))
                    vehicle_data_from_validator['chasis'] = to_str_or_none(safe_get(val_row_series, 'CHASIS'))
                    vehicle_data_from_validator['vin'] = to_str_or_none(safe_get(val_row_series, 'VIN'))

                    prop1_nombre_full = to_str_or_none(safe_get(val_row_series, 'NombrePropietario 1'))
                    prop1_id = to_str_or_none(safe_get(val_row_series, 'Identificacion Prop 1'))
                    if prop1_id and prop1_nombre_full:
                        n, a = parse_propietario_name(prop1_nombre_full)
                        owner_details_list_from_validator.append({
                            'id': prop1_id, 'nombres': n, 'apellidos': a,
                            'telefono': to_str_or_none(safe_get(val_row_series, 'Telefono 1')),
                            'correo': to_str_or_none(safe_get(val_row_series, 'Correo 1'))
                        })

                    prop2_nombre_full = to_str_or_none(safe_get(val_row_series, 'NombrePropietario 2'))
                    prop2_id = to_str_or_none(safe_get(val_row_series, 'Identificacion Prop 2'))
                    if prop2_id and prop2_nombre_full:
                        n, a = parse_propietario_name(prop2_nombre_full)
                        owner_details_list_from_validator.append({
                            'id': prop2_id, 'nombres': n, 'apellidos': a,
                            'telefono': to_str_or_none(safe_get(val_row_series, 'Telefono 2')),
                            'correo': to_str_or_none(safe_get(val_row_series, 'Correo 2'))
                        })
                    if owner_details_list_from_validator:
                        placas_with_validator_owners.add(placa_upper)
                
                empresa_obj_for_veh = get_fk_object_from_map(safe_get(row, 'empresaDirecta'), empresas_map, "Empresa", record_id_str, errors_log, "empresaDirecta")
                
                vehiculo_defaults = {
                    'empresa': empresa_obj_for_veh,
                    'marca': get_fk_object_from_map(safe_get(row, 'marcaID'), marca_map, "Marca", record_id_str, errors_log, "marcaID"),
                    'tipoLinea': get_fk_object_from_map(safe_get(row, 'tipoLinea'), tipo_linea_map, "TipoLinea", record_id_str, errors_log, "tipoLinea"),
                    'paxLt': to_int_or_none(safe_get(row, 'pax_lt')),
                    'paxRl': to_int_or_none(safe_get(row, 'pax_real')),
                    'clase': get_fk_object_from_map(safe_get(row, 'claseVehicID'), clase_vehiculo_map, "ClaseVehiculo", record_id_str, errors_log, "claseVehicID"),
                    'carroceria': get_fk_object_from_map(safe_get(row, 'carroceriaID'), carroceria_map, "Carroceria", record_id_str, errors_log, "carroceriaID"),
                    'numeroMotor': vehicle_data_from_validator.get('numeroMotor') or to_str_or_none(safe_get(row, 'numMotorVehiculo')),
                    'tipoMotor': to_str_or_none(safe_get(row, 'tipoMotor')),
                    'combustible': get_fk_object_from_map(safe_get(row, 'combustibleID'), combustible_map, "Combustible", record_id_str, errors_log, "combustibleID"),
                    'chasis': vehicle_data_from_validator.get('chasis') or to_str_or_none(safe_get(row, 'numChasisVehiculo')),
                    'serie': vehicle_data_from_validator.get('serie') or to_str_or_none(safe_get(row, 'numSerieVehiculo')),
                    'vin': vehicle_data_from_validator.get('vin') or to_str_or_none(safe_get(row, 'numVin')),
                    'ciudadBase': get_fk_object_from_map(safe_get(row, 'ciudadID'), ciudad_map, "Ciudad", record_id_str, errors_log, "ciudadID"),
                    'modelo': to_int_or_none(safe_get(row, 'modelo')),
                    'numeroEjes': to_int_or_none(safe_get(row, 'configuracionEjes')),
                    'cilindraje': to_int_or_none(safe_get(row, 'cilindraje')),
                    'licenciaTransito': to_str_or_none(safe_get(row, 'licenciaTransito')),
                    'estado': 'ACTIVO',
                    'color': get_fk_object_from_map(safe_get(row, 'colorID'), color_map, "Color", record_id_str, errors_log, "colorID"),
                    'unionTemporal': safe_get(row, 'vehiculoUnion', 0) == 1
                }
                
                missing_required_veh_fks = []
                if not vehiculo_defaults['marca']: missing_required_veh_fks.append("Marca (marcaID)")
                if not vehiculo_defaults['clase']: missing_required_veh_fks.append("ClaseVehiculo (claseVehicID)")
                if not vehiculo_defaults['combustible']: missing_required_veh_fks.append("Combustible (combustibleID)")
                if not vehiculo_defaults['ciudadBase']: missing_required_veh_fks.append("CiudadBase (ciudadID)")
                if not vehiculo_defaults['color']: missing_required_veh_fks.append("Color (colorID)")
                if Vehiculos._meta.get_field('empresa').null is False and not vehiculo_defaults['empresa']:
                     missing_required_veh_fks.append("Empresa (empresaDirecta)")


                if missing_required_veh_fks:
                    errors_log.append(f"Vehiculo {placa_excel}: Faltan objetos FK obligatorios: {', '.join(missing_required_veh_fks)}. No se creará/actualizará.")
                    continue
                
                try:
                    vehiculo_obj, v_created = Vehiculos.objects.update_or_create(
                        placa=placa_excel,
                        defaults=vehiculo_defaults
                    )
                    vehiculos_map_excel_id_to_django_obj[excel_vehiculo_id] = vehiculo_obj
                    count_vehiculos += 1

                    if placa_upper in placas_with_validator_owners and owner_details_list_from_validator:
                        VehiculoPropietario.objects.filter(vehiculo=vehiculo_obj).delete()
                        num_owners = len(owner_details_list_from_validator)
                        porcentaje_prop = round(100 / num_owners) if num_owners > 0 else 0
                        
                        for owner_data in owner_details_list_from_validator:
                            prop_identificacion = to_str_or_none(owner_data.get('id'))
                            if not prop_identificacion:
                                errors_log.append(f"Vehiculo {placa_excel} (Validador: {current_validator_source}): ID de propietario faltante. {owner_data.get('nombres')}")
                                continue

                            propietario_obj = propietarios_cache_by_identificacion.get(prop_identificacion)
                            if not propietario_obj:
                                prop_create_defaults = {
                                    'tipoDocumento': tipo_doc_default,
                                    'nombres': owner_data.get('nombres'),
                                    'apellidos': owner_data.get('apellidos'),
                                    'telefono': to_str_or_none(owner_data.get('telefono')),
                                    'correo': to_str_or_none(owner_data.get('correo')),
                                }
                                propietario_obj, p_created = Propietario.objects.update_or_create(
                                    identificacion=prop_identificacion,
                                    defaults=prop_create_defaults
                                )
                                propietarios_cache_by_identificacion[prop_identificacion] = propietario_obj
                            
                            VehiculoPropietario.objects.update_or_create(
                                vehiculo=vehiculo_obj,
                                propietario=propietario_obj,
                                defaults={'porcentaje': porcentaje_prop}
                            )
                    
                    servicio_fk_objects = {
                        'empresaOficial': get_fk_object_from_map(safe_get(row, 'empresaDirecta'), empresas_map, "Empresa (Oficial para Servicio)", record_id_str, errors_log, "empresaDirecta"),
                        'empresaAdministra': get_fk_object_from_map(safe_get(row, 'empresaAdministradora'), empresas_map, "Empresa (Admin para Servicio)", record_id_str, errors_log, "empresaAdministradora"),
                        'tipoOperacion': get_fk_object_from_map(safe_get(row, 'tipoOperacionID'), tipo_operacion_map, "TipoOperacion (para Servicio)", record_id_str, errors_log, "tipoOperacionID"),
                        'nivelServicio': get_fk_object_from_map(safe_get(row, 'nivelServicioID'), nivel_servicio_map, "NivelServicio (para Servicio)", record_id_str, errors_log, "nivelServicioID"),
                        'servicio': get_fk_object_from_map(safe_get(row, 'categoriaID'), categoria_map, "Categoria (para Servicio.servicio)", record_id_str, errors_log, "categoriaID")
                    }
                    servicio_data_fields = {
                        'numeroInterno': to_int_or_none(safe_get(row, 'numero_Vehiculo')),
                        'fechaIngreso': to_date_or_none(safe_get(row, 'fechaInicioServicio')),
                        'fechaFinServicio': to_date_or_none(safe_get(row, 'fechaFinServicio'))
                    }
                    
                    servicio_final_defaults = {**servicio_fk_objects, **servicio_data_fields}
                    
                    missing_servicio_req_fields = []
                    for field_name, field_obj in servicio_fk_objects.items():
                        if field_obj is None and not Servicio._meta.get_field(field_name).null: # Check based on actual model
                            missing_servicio_req_fields.append(f"{field_name} (FK de {field_name}ID)")
                    if servicio_data_fields['numeroInterno'] is None and not Servicio._meta.get_field('numeroInterno').null:
                         missing_servicio_req_fields.append("numeroInterno")
                    if servicio_data_fields['fechaIngreso'] is None and not Servicio._meta.get_field('fechaIngreso').null:
                         missing_servicio_req_fields.append("fechaIngreso")

                    if not missing_servicio_req_fields:
                        try:
                            Servicio.objects.update_or_create(
                                vehiculo=vehiculo_obj,
                                defaults=servicio_final_defaults
                            )
                        except Exception as e_servicio:
                            errors_log.append(f"Servicio para {record_id_str}: Error al crear/actualizar: {e_servicio}. Datos: {servicio_final_defaults}")
                    else:
                        errors_log.append(f"Servicio para {record_id_str}: Datos FK/obligatorios insuficientes: {', '.join(missing_servicio_req_fields)}. No se creó/actualizó Servicio.")

                except Exception as e:
                    errors_log.append(f"Vehiculo/Servicio Error {record_id_str}: {e}. Datos Vehiculo: {vehiculo_defaults}")
            summary['Vehiculos y Servicios'] = f"{count_vehiculos} procesados."
        except Exception as e:
            errors_log.append(f"Error general leyendo hoja 'Vehiculos': {e}")

        try:
            df_vp = pd.read_excel(excel_file_path, sheet_name='propietariosVehiculo')
            count_vp = 0
            for index, row in df_vp.iterrows():
                excel_propietario_id_raw = safe_get(row, 'propietariosID')
                excel_propietario_id_vp = to_int_or_none(excel_propietario_id_raw)
                excel_vehiculo_id_raw = safe_get(row, 'vehiculoID')
                excel_vehiculo_id_vp = to_int_or_none(excel_vehiculo_id_raw)
                porcentaje_excel_vp = to_int_or_none(safe_get(row, 'porcentaje'))

                if excel_propietario_id_vp is None or excel_vehiculo_id_vp is None or porcentaje_excel_vp is None:
                    errors_log.append(f"VehiculoPropietario (doc migracion) fila {index+2}: IDs (PropRaw:'{excel_propietario_id_raw}', VehRaw:'{excel_vehiculo_id_raw}') o porcentaje faltante/inválido.")
                    continue

                vehiculo_obj_vp = vehiculos_map_excel_id_to_django_obj.get(excel_vehiculo_id_vp)
                propietario_obj_vp = propietarios_map_excel_id_to_django_obj.get(excel_propietario_id_vp)

                if not vehiculo_obj_vp:
                    errors_log.append(f"VehiculoPropietario (doc migracion) fila {index+2}: Vehiculo con Excel ID {excel_vehiculo_id_vp} no encontrado en DB.")
                    continue
                
                if vehiculo_obj_vp.placa.upper() in placas_with_validator_owners:
                    continue 

                if not propietario_obj_vp:
                    errors_log.append(f"VehiculoPropietario (doc migracion) fila {index+2}: Propietario con Excel ID {excel_propietario_id_vp} no encontrado en DB.")
                    continue
                
                try:
                    VehiculoPropietario.objects.update_or_create(
                        vehiculo=vehiculo_obj_vp,
                        propietario=propietario_obj_vp,
                        defaults={'porcentaje': porcentaje_excel_vp}
                    )
                    count_vp += 1
                except Exception as e:
                    placa_info = vehiculo_obj_vp.placa if vehiculo_obj_vp else 'N/A'
                    prop_info = propietario_obj_vp.identificacion if propietario_obj_vp else 'N/A'
                    errors_log.append(f"VehiculoPropietario (doc migracion) Error fila {index+2} (Vehiculo: {placa_info}, Propietario ID: {prop_info}): {e}")
            summary['VehiculoPropietario (doc migracion fallback)'] = f"{count_vp} relaciones procesadas."
        except Exception as e:
            errors_log.append(f"Error leyendo hoja 'propietariosVehiculo' de doc migracion: {e}")


        self.stdout.write(self.style.SUCCESS("\n--- Resumen de Importación ---"))
        for model_name, message in summary.items():
            self.stdout.write(f"{model_name}: {message}")

        if errors_log:
            self.stdout.write(self.style.ERROR("\n--- Errores Encontrados ---"))
            for error in errors_log:
                self.stdout.write(self.style.WARNING(error))
            self.stdout.write(self.style.ERROR(f"\nSe encontraron {len(errors_log)} errores."))
            self.stdout.write(self.style.WARNING("Si el script completó pero mostró errores, significa que esos ítems específicos fallaron pero el resto pudo continuar. La transacción general SÓLO se revierte si una excepción no controlada escapa del @transaction.atomic."))
        else:
            self.stdout.write(self.style.SUCCESS("\nImportación completada exitosamente sin errores reportados en los logs."))