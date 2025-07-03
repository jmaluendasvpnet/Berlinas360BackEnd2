from django.core.management.base import BaseCommand
from django.db import transaction
from dateutil.relativedelta import relativedelta
from datetime import timedelta 
from django.db.models import F
# Asegúrate de reemplazar 'myapp' con el nombre real de tu aplicación Django
from myapp.models import Soat, RevisionTecnomecanica, TarjetaOperacion

class Command(BaseCommand):
    help = 'Actualiza SOATs, RTMs y T.O. cuyas fechas son iguales, sin usar Excel.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        changes_to_propose = []
        
        # --- Proceso para SOAT ---
        self.stdout.write("Buscando SOATs con fecha_inicio == fecha_fin...")
        soats_to_fix = Soat.objects.filter(
            vigencia_desde__isnull=False, 
            vigencia_hasta__isnull=False, 
            vigencia_desde=F('vigencia_hasta')
        )
        self.stdout.write(f"Se encontraron {soats_to_fix.count()} SOATs para corregir.")
        for soat_obj in soats_to_fix:
            placa = soat_obj.vehiculo.placa if soat_obj.vehiculo else "SIN PLACA ASOCIADA"
            current_hasta_date = soat_obj.vigencia_hasta
            new_desde_date = current_hasta_date - relativedelta(years=1) + timedelta(days=1)
            changes_to_propose.append({
                'type': 'Soat',
                'obj': soat_obj,
                'placa': placa,
                'old_desde': soat_obj.vigencia_desde,
                'old_hasta': soat_obj.vigencia_hasta,
                'new_desde': new_desde_date,
                'new_hasta': current_hasta_date, 
            })

        # --- Proceso para RevisionTecnomecanica ---
        self.stdout.write("Buscando RTMs con fecha_expedicion == fecha_vencimiento...")
        rtms_to_fix = RevisionTecnomecanica.objects.filter(
            fecha_expedicion__isnull=False, 
            fecha_vencimiento__isnull=False, 
            fecha_expedicion=F('fecha_vencimiento')
        )
        self.stdout.write(f"Se encontraron {rtms_to_fix.count()} RTMs para corregir.")
        for rtm_obj in rtms_to_fix:
            placa = rtm_obj.vehiculo.placa if rtm_obj.vehiculo else "SIN PLACA ASOCIADA"
            current_vencimiento_date = rtm_obj.fecha_vencimiento
            new_expedicion_date = current_vencimiento_date - relativedelta(years=1)
            changes_to_propose.append({
                'type': 'RTM',
                'obj': rtm_obj,
                'placa': placa,
                'old_expedicion': rtm_obj.fecha_expedicion,
                'old_vencimiento': rtm_obj.fecha_vencimiento,
                'new_expedicion': new_expedicion_date,
                'new_vencimiento': current_vencimiento_date,
            })

        # --- Proceso para TarjetaOperacion ---
        self.stdout.write("Buscando Tarjetas de Operación con fecha_inicio == fecha_fin...")
        tos_to_fix = TarjetaOperacion.objects.filter(
            fechaInicialVigencia__isnull=False, 
            fechaFinVigencia__isnull=False, 
            fechaInicialVigencia=F('fechaFinVigencia')
        )
        self.stdout.write(f"Se encontraron {tos_to_fix.count()} T.O. para corregir.")
        for to_obj in tos_to_fix:
            placa = to_obj.vehiculo.placa if to_obj.vehiculo else "SIN PLACA ASOCIADA"
            current_fin_date = to_obj.fechaFinVigencia
            new_inicio_date = current_fin_date - relativedelta(years=2)
            changes_to_propose.append({
                'type': 'TO',
                'obj': to_obj,
                'placa': placa,
                'old_inicio': to_obj.fechaInicialVigencia,
                'old_fin': to_obj.fechaFinVigencia,
                'new_inicio': new_inicio_date,
                'new_fin': current_fin_date,
            })


        # --- Mostrar Cambios y Confirmar ---
        if not changes_to_propose:
            self.stdout.write(self.style.SUCCESS("No se encontraron registros que cumplan las condiciones para actualizar."))
            return

        self.stdout.write(self.style.HTTP_INFO("\nCambios Propuestos (SOATs, RTMs y T.O. con fechas iguales):\n" + "="*70))

        for change in changes_to_propose:
            obj = change['obj']
            self.stdout.write(f"Placa: {change['placa']}, ID: {obj.id}")
            if change['type'] == 'Soat':
                self.stdout.write(f"  Tipo: SOAT, Póliza: {obj.numero_poliza}")
                self.stdout.write(f"    Antiguo: {change['old_desde']} -> {change['old_hasta']}")
                self.stdout.write(self.style.SUCCESS(f"    Nuevo:   {change['new_desde']} -> {change['new_hasta']}"))
            elif change['type'] == 'RTM':
                self.stdout.write(f"  Tipo: RTM, Certificado: {obj.no_certificado}")
                self.stdout.write(f"    Antiguo: Exp: {change['old_expedicion']}, Vence: {change['old_vencimiento']}")
                self.stdout.write(self.style.SUCCESS(f"    Nuevo:   Exp: {change['new_expedicion']}, Vence: {change['new_vencimiento']}"))
            else: # TO
                self.stdout.write(f"  Tipo: T.Operación, Número: {obj.numero}")
                self.stdout.write(f"    Antiguo: Inicio: {change['old_inicio']}, Fin: {change['old_fin']}")
                self.stdout.write(self.style.SUCCESS(f"    Nuevo:   Inicio: {change['new_inicio']}, Fin: {change['new_fin']}"))
            self.stdout.write("-" * 20)

        confirmation = input(f"\nSe proponen {len(changes_to_propose)} actualizaciones. ¿Desea aplicar estos cambios? (si/no): ").lower()

        # --- Aplicar Cambios ---
        if confirmation == 'si':
            self.stdout.write(self.style.HTTP_INFO("Aplicando cambios..."))
            updated_count = 0
            error_count = 0

            with transaction.atomic():
                for change in changes_to_propose:
                    obj = change['obj']
                    try:
                        if change['type'] == 'Soat':
                            obj.vigencia_desde = change['new_desde']
                            obj.save(update_fields=['vigencia_desde'])
                        elif change['type'] == 'RTM':
                            obj.fecha_expedicion = change['new_expedicion']
                            obj.save(update_fields=['fecha_expedicion'])
                        else: # TO
                            obj.fechaInicialVigencia = change['new_inicio']
                            obj.save(update_fields=['fechaInicialVigencia'])
                        updated_count += 1
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"  ERROR al actualizar {change['type']} ID {obj.id} (Placa: {change['placa']}): {e}"))
                        error_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"Proceso finalizado. {updated_count} registros actualizados, {error_count} errores."))
        else:
            self.stdout.write("Los cambios no fueron aplicados.")