import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from myapp.models import Vehiculos # Ensure this import matches your app structure

def to_str_or_none(value):
    if pd.isna(value) or value is None or (isinstance(value, str) and str(value).strip().upper() == 'NULL'):
        return None
    val_str = str(value).strip()
    return val_str

class Command(BaseCommand):
    help = 'Inactivates vehicles in the database if their license plates are not found in the provided validator Excel files.'

    def add_arguments(self, parser):
        parser.add_argument('validator1_file', type=str, help='Path to the first validator Excel file (e.g., validator.xlsx)')
        parser.add_argument('validator2_file', type=str, help='Path to the second validator Excel file (e.g., validator2.xlsx)')

    @transaction.atomic
    def handle(self, *args, **options):
        validator1_file_path = options['validator1_file']
        validator2_file_path = options['validator2_file']

        self.stdout.write(self.style.SUCCESS("Starting vehicle inactivation process..."))

        validator_plates = set()
        files_processed_count = 0

        try:
            df_val1 = pd.read_excel(validator1_file_path, sheet_name=0, dtype=str)
            for _, row in df_val1.iterrows():
                placa = to_str_or_none(row.get('PLACA'))
                if placa:
                    validator_plates.add(placa.upper())
            self.stdout.write(self.style.SUCCESS(f"Successfully read {len(df_val1)} rows from {validator1_file_path}"))
            files_processed_count += 1
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Error: Validator file '{validator1_file_path}' not found."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading '{validator1_file_path}': {e}"))

        try:
            df_val2 = pd.read_excel(validator2_file_path, sheet_name=0, dtype=str)
            for _, row in df_val2.iterrows():
                placa = to_str_or_none(row.get('PLACA'))
                if placa:
                    validator_plates.add(placa.upper())
            self.stdout.write(self.style.SUCCESS(f"Successfully read {len(df_val2)} rows from {validator2_file_path}"))
            files_processed_count += 1
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Error: Validator file '{validator2_file_path}' not found."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading '{validator2_file_path}': {e}"))

        if not validator_plates and files_processed_count < 2 :
             self.stdout.write(self.style.ERROR("No plates loaded from validator files or not all files could be read. Aborting to prevent unintended inactivations."))
             return

        if not validator_plates:
            self.stdout.write(self.style.WARNING("No plates found in any validator file. All vehicles might be inactivated if this proceeds. However, the script will continue to check DB vehicles."))


        self.stdout.write(self.style.SUCCESS(f"Total unique plates loaded from validator files: {len(validator_plates)}"))

        db_vehiculos = Vehiculos.objects.all()
        total_db_vehiculos = db_vehiculos.count()
        vehiculos_inactivated_count = 0
        vehiculos_already_inactive_skipped_count = 0
        vehiculos_found_active_count = 0

        self.stdout.write(f"Processing {total_db_vehiculos} vehicles from the database...")

        for vehiculo in db_vehiculos:
            db_placa_upper = None
            if vehiculo.placa:
                db_placa_upper = vehiculo.placa.upper()

            if not db_placa_upper:
                self.stdout.write(self.style.WARNING(f"Vehicle with ID {vehiculo.id} has no plate. Skipping."))
                continue

            if db_placa_upper not in validator_plates:
                if vehiculo.estado != 'INACTIVO':
                    vehiculo.estado = 'INACTIVO'
                    vehiculo.save(update_fields=['estado'])
                    vehiculos_inactivated_count += 1
                    self.stdout.write(f"Vehicle {db_placa_upper} inactivated.")
                else:
                    vehiculos_already_inactive_skipped_count +=1
            else:
                vehiculos_found_active_count +=1


        self.stdout.write(self.style.SUCCESS("\n--- Inactivation Summary ---"))
        self.stdout.write(f"Total vehicles in database: {total_db_vehiculos}")
        self.stdout.write(f"Vehicles found in validator files (and kept active or already active): {vehiculos_found_active_count}")
        self.stdout.write(f"Vehicles newly inactivated: {vehiculos_inactivated_count}")
        self.stdout.write(f"Vehicles already inactive and not found in validators (skipped): {vehiculos_already_inactive_skipped_count}")

        if not validator_plates and files_processed_count > 0:
             self.stdout.write(self.style.WARNING("Warning: No plates were loaded from the validator files. This means all vehicles not already INACTIVO might have been set to INACTIVO if they had a placa."))
        elif not validator_plates and files_processed_count == 0:
             self.stdout.write(self.style.ERROR("CRITICAL: No validator files were processed and no plates were loaded. No vehicles were inactivated based on this check, but the files were not found or readable."))


        self.stdout.write(self.style.SUCCESS("Vehicle inactivation process completed."))