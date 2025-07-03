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
    return val_str if val_str else None

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

class Command(BaseCommand):
    help = 'Import vehicle documents from Excel by document name, with pre-confirmation and insurer creation.'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file with documents.')

    @transaction.atomic
    def handle(self, *args, **options):
        excel_file_path = options['excel_file']
        self.stdout.write(f"Starting document import from {excel_file_path}...")

        errors_log = []
        warnings_log = []
        proposed_creations = []
        aseguradoras_to_create_details = {}

        tipos_doc_fk_by_name = {tdv.nombre.upper().strip(): tdv for tdv in TipoDocumentoVehiculo.objects.all()}
        if not tipos_doc_fk_by_name:
            self.stdout.write(self.style.ERROR("CRITICAL: No TipoDocumentoVehiculo found in the database. Aborting."))
            return

        existing_aseguradoras_by_nit = {a.nit: a for a in Aseguradora.objects.filter(nit__isnull=False).exclude(nit='')}
        existing_aseguradoras_by_name = {a.nombre.upper(): a for a in Aseguradora.objects.all()}

        try:
            df = pd.read_excel(excel_file_path, sheet_name=0, dtype=str)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Excel file not found: {excel_file_path}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading Excel file: {e}"))
            return

        for index, row in df.iterrows():
            row_num = index + 2

            placa_str = to_str_or_none(row.get('placa_Vehiculo'))
            if not placa_str:
                warnings_log.append(f"Row {row_num}: Skipped - 'placa_Vehiculo' is missing.")
                continue

            vehiculo_obj = Vehiculos.objects.filter(placa=placa_str.upper()).first()
            if not vehiculo_obj:
                warnings_log.append(f"Row {row_num}: Skipped - Vehicle with placa '{placa_str}' not found.")
                continue

            detalle_documento_excel = to_str_or_none(row.get('detalleDocumento'))
            if not detalle_documento_excel:
                warnings_log.append(f"Row {row_num} (Placa: {placa_str}): Skipped - 'detalleDocumento' is missing.")
                continue
            
            detalle_documento_excel_upper = detalle_documento_excel.upper().strip()
            tipo_documento_fk_obj = tipos_doc_fk_by_name.get(detalle_documento_excel_upper)

            if not tipo_documento_fk_obj:
                # Intenta buscar con nombres alternativos o parciales si es necesario
                # Ejemplo: si el excel dice "NUMERO REVISION" pero en BD es "REVISION TECNOMECANICA"
                if "NUMERO REVISION" in detalle_documento_excel_upper:
                    tipo_documento_fk_obj = tipos_doc_fk_by_name.get("REVISION TECNOMECANICA Y DE GASES") or \
                                            tipos_doc_fk_by_name.get("REVISION TECNOMECANICA") #Ajusta estos nombres a los de tu BD
                elif "FICHA TECNICA HOMOLOGACIÓN CARROCERIA" in detalle_documento_excel_upper:
                     tipo_documento_fk_obj = tipos_doc_fk_by_name.get("FICHA TECNICA HOMOLOGACION CARROCERIA")
                # ... otros mapeos si son necesarios

            if not tipo_documento_fk_obj:
                warnings_log.append(f"Row {row_num} (Placa: {placa_str}): Skipped - TipoDocumentoVehiculo for '{detalle_documento_excel}' not found in DB mapping.")
                continue

            numero_documento = to_str_or_none(row.get('numeroDocumento'))
            fecha_expedicion = to_date_or_none(row.get('fechaExpedicion'))
            fecha_ini_vigencia = to_date_or_none(row.get('fechaIniVigencia'))
            fecha_fin_vigencia = to_date_or_none(row.get('fechaFinVigencia'))
            detalle_aseguradora_excel = to_str_or_none(row.get('detalleAseguradora'))
            nit_aseguradora_excel = to_str_or_none(row.get('nitAseguradora'))
            soporte_raw = to_str_or_none(row.get('archivoSoporte'))
            soporte_path = f"{SOPORTE_URL_PREFIX}{soporte_raw.lstrip('/')}" if soporte_raw else None
            estado_doc = to_str_or_none(row.get('estado', '1')) == '1'

            aseguradora_instance_for_doc = None
            aseguradora_data_for_creation_key = None

            if detalle_aseguradora_excel:
                aseg_name_upper = detalle_aseguradora_excel.upper()
                if nit_aseguradora_excel and nit_aseguradora_excel in existing_aseguradoras_by_nit:
                    aseguradora_instance_for_doc = existing_aseguradoras_by_nit[nit_aseguradora_excel]
                elif aseg_name_upper in existing_aseguradoras_by_name:
                    aseguradora_instance_for_doc = existing_aseguradoras_by_name[aseg_name_upper]

                if not aseguradora_instance_for_doc:
                    aseguradora_data_for_creation_key = (aseg_name_upper, nit_aseguradora_excel if nit_aseguradora_excel else None)
                    if aseguradora_data_for_creation_key not in aseguradoras_to_create_details:
                        aseguradoras_to_create_details[aseguradora_data_for_creation_key] = {
                            'nombre': detalle_aseguradora_excel,
                            'nit': nit_aseguradora_excel
                        }
            
            model_class = None
            lookup_keys = {'vehiculo': vehiculo_obj}
            defaults = {
                'fecha_expedicion': fecha_expedicion,
                'soporte': soporte_path,
                'estado': estado_doc,
                'tipo_documento_vehiculo': tipo_documento_fk_obj,
                'placa': vehiculo_obj.placa
            }
            is_policy_type = False
            
            # Lógica basada en el nombre del documento del Excel
            if detalle_documento_excel_upper == "SOAT":
                model_class, is_policy_type = Soat, True
                if not numero_documento or not fecha_ini_vigencia or not fecha_fin_vigencia:
                    warnings_log.append(f"Row {row_num} (SOAT for {placa_str}): Skipped - Missing num, F.IniVig, or F.FinVig.")
                    continue
                lookup_keys.update({'numero_poliza': numero_documento, 'vigencia_hasta': fecha_fin_vigencia})
                defaults.update({'vigencia_desde': fecha_ini_vigencia, 'aseguradora_nombre': detalle_aseguradora_excel})
            elif detalle_documento_excel_upper == "TARJETA OPERACION":
                model_class = TarjetaOperacion
                if not numero_documento or not fecha_ini_vigencia or not fecha_fin_vigencia:
                    warnings_log.append(f"Row {row_num} (T.Op for {placa_str}): Skipped - Missing num, F.IniVig, or F.FinVig.")
                    continue
                lookup_keys.update({'numero': numero_documento, 'fechaFinVigencia': fecha_fin_vigencia})
                defaults.update({'fechaInicialVigencia': fecha_ini_vigencia})
            elif detalle_documento_excel_upper == "NUMERO REVISION": # Asumiendo que es RTM
                model_class = RevisionTecnomecanica
                if not numero_documento or not fecha_fin_vigencia:
                    warnings_log.append(f"Row {row_num} (RTM/Numero Revision for {placa_str}): Skipped - Missing num or F.FinVig.")
                    continue
                lookup_keys.update({'no_certificado': numero_documento, 'fecha_vencimiento': fecha_fin_vigencia})
            elif detalle_documento_excel_upper == "POLIZA CONTRACTUAL":
                model_class, is_policy_type = PolizaContractual, True
                if not numero_documento or not fecha_ini_vigencia or not fecha_fin_vigencia:
                    warnings_log.append(f"Row {row_num} ({detalle_documento_excel} for {placa_str}): Skipped - Missing num, F.IniVig, or F.FinVig.")
                    continue
                lookup_keys.update({'numero_poliza': numero_documento, 'fecha_fin_vigencia': fecha_fin_vigencia})
                defaults.update({'fecha_inicio_vigencia': fecha_ini_vigencia, 'aseguradora_nombre_alt': detalle_aseguradora_excel})
            elif detalle_documento_excel_upper == "POLIZA EXTRACONTRACTUAL":
                model_class, is_policy_type = PolizaExtracontractual, True
                if not numero_documento or not fecha_ini_vigencia or not fecha_fin_vigencia:
                    warnings_log.append(f"Row {row_num} ({detalle_documento_excel} for {placa_str}): Skipped - Missing num, F.IniVig, or F.FinVig.")
                    continue
                lookup_keys.update({'numero_poliza': numero_documento, 'fecha_fin_vigencia': fecha_fin_vigencia})
                defaults.update({'fecha_inicio_vigencia': fecha_ini_vigencia, 'aseguradora_nombre_alt': detalle_aseguradora_excel})
            elif detalle_documento_excel_upper == "POLIZA TODO RIESGO":
                model_class, is_policy_type = PolizaTodoRiesgo, True
                if not numero_documento or not fecha_ini_vigencia or not fecha_fin_vigencia:
                    warnings_log.append(f"Row {row_num} ({detalle_documento_excel} for {placa_str}): Skipped - Missing num, F.IniVig, or F.FinVig.")
                    continue
                lookup_keys.update({'numero_poliza': numero_documento, 'fecha_fin_vigencia': fecha_fin_vigencia})
                defaults.update({'fecha_inicio_vigencia': fecha_ini_vigencia, 'aseguradora_nombre_alt': detalle_aseguradora_excel})
            elif detalle_documento_excel_upper == "FICHA TECNICA HOMOLOGACIÓN CARROCERIA":
                model_class = FichaTecnicaHomologacionCarroceria
                if not numero_documento and not soporte_path:
                    warnings_log.append(f"Row {row_num} ({detalle_documento_excel} for {placa_str}): Skipped - Missing num AND soporte.")
                    continue
                if numero_documento: lookup_keys['numero_documento'] = numero_documento
                defaults['numero_documento'] = numero_documento # Puede ser None si solo hay soporte
            elif detalle_documento_excel_upper == "LICENCIA DE TRANSITO":
                model_class = LicenciaTransito
                if not numero_documento : # Fecha expedición puede ser opcional para Licencia
                    warnings_log.append(f"Row {row_num} (L.Trans for {placa_str}): Skipped - Missing num.")
                    continue
                lookup_keys.update({'numero_documento': numero_documento})
                defaults.update({'fecha_inicio_vigencia': fecha_ini_vigencia, 'fecha_fin_vigencia': fecha_fin_vigencia})
            else:
                warnings_log.append(f"Row {row_num} (Placa: {placa_str}): Skipped - Unhandled document type name '{detalle_documento_excel}'.")
                continue

            final_model_defaults = {k: v for k, v in defaults.items() if hasattr(model_class, k.split('__')[0]) and v is not None}
            valid_lookup_keys = {k: v for k, v in lookup_keys.items() if hasattr(model_class, k.split('__')[0])}

            if model_class.objects.filter(**valid_lookup_keys).exists():
                warnings_log.append(f"Row {row_num} ({detalle_documento_excel} {numero_documento if numero_documento else ''} for {placa_str}): Skipped - Exists: {valid_lookup_keys}.")
                continue
            
            display_text = f"Placa: {placa_str}, Tipo: {detalle_documento_excel}, Num: {numero_documento if numero_documento else 'S/N'}, VigHasta: {fecha_fin_vigencia if fecha_fin_vigencia else 'N/A'}"
            if detalle_aseguradora_excel: display_text += f", Aseg: {detalle_aseguradora_excel}"
            
            proposed_creations.append({
                'model_class': model_class, 'lookup_keys': valid_lookup_keys, 'defaults': final_model_defaults,
                'display_text': display_text, 'is_policy': is_policy_type,
                'aseguradora_to_be_created_key': aseguradora_data_for_creation_key,
                'existing_aseguradora_obj': aseguradora_instance_for_doc,
                'original_detalle_documento': detalle_documento_excel # Para el resumen
            })

        if not proposed_creations and not aseguradoras_to_create_details:
            self.stdout.write(self.style.SUCCESS("No new documents or insurers to import based on criteria."))
            for warning in warnings_log: self.stdout.write(self.style.WARNING(warning))
            return

        self.stdout.write(self.style.HTTP_INFO("\n--- Summary of Proposed Creations ---"))
        if aseguradoras_to_create_details:
            self.stdout.write(self.style.SUCCESS("\nProposed New Insurers:"))
            for i, (key, detail) in enumerate(aseguradoras_to_create_details.items()):
                self.stdout.write(f"  {i+1}. Nombre: {detail['nombre']}, NIT: {detail.get('nit', 'N/A')}")
        
        if proposed_creations:
            self.stdout.write(self.style.SUCCESS("\nProposed New Policy Documents (Soat, Poliza Contractual, etc.):"))
            policy_count = sum(1 for prop in proposed_creations if prop['is_policy'])
            if policy_count > 0:
                for prop in proposed_creations:
                    if prop['is_policy']: self.stdout.write(f"  - {prop['display_text']}")
            else: self.stdout.write("  No new policy-type documents to list.")

            self.stdout.write(self.style.SUCCESS("\nProposed Other New Documents (Tarjeta Operacion, RTM, Fichas, Licencias):"))
            other_doc_count = sum(1 for prop in proposed_creations if not prop['is_policy'])
            if other_doc_count > 0:
                for prop in proposed_creations:
                    if not prop['is_policy']: self.stdout.write(f"  - {prop['display_text']}")
            else: self.stdout.write("  No other new documents to list.")
        
        if warnings_log:
            self.stdout.write(self.style.WARNING("\n--- Warnings (Skipped Rows/Docs) ---"))
            for warning in warnings_log: self.stdout.write(self.style.WARNING(warning))

        if not proposed_creations and not aseguradoras_to_create_details:
            self.stdout.write(self.style.SUCCESS("\nNo actions to confirm after filtering."))
            return

        confirmation = input(f"\nProceed with creating {len(aseguradoras_to_create_details)} insurer(s) and {len(proposed_creations)} document(s)? (yes/no): ").lower()
        if confirmation != 'yes':
            self.stdout.write(self.style.ERROR("Import aborted by user."))
            return
        
        self.stdout.write(self.style.HTTP_INFO("\nProceeding with import..."))
        created_aseguradoras_map = {}
        
        for key, detail in aseguradoras_to_create_details.items():
            nombre_aseg, nit_aseg = detail['nombre'], detail.get('nit')
            try:
                q_params_aseg = {}
                defaults_aseg = {'nombre': nombre_aseg}
                if nit_aseg: # Si hay NIT, es la clave principal para get_or_create
                    q_params_aseg = {'nit': nit_aseg}
                    defaults_aseg['nit'] = nit_aseg # Asegurarse que esté en defaults también
                else: # Si no hay NIT, el nombre es la clave
                    q_params_aseg = {'nombre__iexact': nombre_aseg} # Búsqueda insensible a mayúsculas
                    defaults_aseg['nit'] = None # explícitamente
                
                aseg_obj, created = Aseguradora.objects.get_or_create(**q_params_aseg, defaults=defaults_aseg)
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created Aseguradora: {aseg_obj.nombre} (NIT: {aseg_obj.nit or 'N/A'})"))
                created_aseguradoras_map[key] = aseg_obj # key es (nombre_upper, nit)
            except IntegrityError as ie: # Podría ocurrir si el nit es único pero el nombre difiere, o viceversa.
                fetched_aseg = None
                if nit_aseg: fetched_aseg = Aseguradora.objects.filter(nit=nit_aseg).first()
                if not fetched_aseg and nombre_aseg: fetched_aseg = Aseguradora.objects.filter(nombre__iexact=nombre_aseg).first()
                if fetched_aseg:
                    created_aseguradoras_map[key] = fetched_aseg
                    warnings_log.append(f"Aseguradora '{nombre_aseg}' (NIT: {nit_aseg or 'N/A'}) fetch after IntegrityError: {fetched_aseg.id}.")
                else:
                    errors_log.append(f"IntegrityError for Aseguradora '{nombre_aseg}' (NIT: {nit_aseg or 'N/A'}): {ie}. Not found after error.")
            except Exception as e:
                errors_log.append(f"Error with Aseguradora '{nombre_aseg}': {e}")
        
        successful_docs = 0
        for prop_data in proposed_creations:
            model_cls = prop_data['model_class']
            final_doc_defaults = prop_data['defaults'].copy()
            
            current_aseguradora_obj_for_doc = prop_data.get('existing_aseguradora_obj')
            newly_created_aseg_key = prop_data.get('aseguradora_to_be_created_key') # Este es (nombre_upper, nit)
            if newly_created_aseg_key and newly_created_aseg_key in created_aseguradoras_map:
                current_aseguradora_obj_for_doc = created_aseguradoras_map[newly_created_aseg_key]

            if hasattr(model_cls, 'aseguradora'): # Solo si el modelo tiene campo 'aseguradora'
                if current_aseguradora_obj_for_doc:
                    final_doc_defaults['aseguradora'] = current_aseguradora_obj_for_doc
                else: 
                    # Si el campo FK 'aseguradora' es nullable=True en el modelo, se puede poner None.
                    # Si es nullable=False, se debe quitar de los defaults si no hay objeto, o fallará.
                    # Asumimos que los modelos están definidos para permitir None si no hay aseguradora o ya se quitó de defaults.
                    if model_cls._meta.get_field('aseguradora').null:
                         final_doc_defaults['aseguradora'] = None
                    else: # Si no es nullable y no hay objeto, quitarlo para evitar error si no está en lookup_keys
                         final_doc_defaults.pop('aseguradora', None)


            try:
                obj = model_cls.objects.create(**prop_data['lookup_keys'], **final_doc_defaults)
                self.stdout.write(self.style.SUCCESS(f"CREATED {model_cls.__name__}: {prop_data['display_text']} (ID: {obj.pk})"))
                successful_docs +=1
            except IntegrityError as ie:
                 errors_log.append(f"IntegrityError {model_cls.__name__} ({prop_data['display_text']}): {ie}. LKP: {prop_data['lookup_keys']}, DFLT: {final_doc_defaults}")
            except Exception as e:
                errors_log.append(f"Error {model_cls.__name__} ({prop_data['display_text']}): {type(e).__name__} - {e}. LKP: {prop_data['lookup_keys']}, DFLT: {final_doc_defaults}")
        
        self.stdout.write(self.style.SUCCESS(f"\n--- Importation Finished ---"))
        self.stdout.write(f"Successfully created {successful_docs} document(s).")
        self.stdout.write(f"Processed {len(created_aseguradoras_map)} insurer(s) marked for creation (either created or retrieved).")

        if warnings_log:
            self.stdout.write(self.style.WARNING("\n--- Final Warnings List ---"))
            for warn in warnings_log: self.stdout.write(self.style.WARNING(warn))
        if errors_log:
            self.stdout.write(self.style.ERROR("\n--- Final Errors List ---"))
            for err in errors_log: self.stdout.write(self.style.ERROR(err))
        
        if not errors_log:
             self.stdout.write(self.style.SUCCESS("\nDocument import process completed with no critical errors during database operations."))
        else:
             self.stdout.write(self.style.ERROR("\nDocument import process completed with errors. Please review."))