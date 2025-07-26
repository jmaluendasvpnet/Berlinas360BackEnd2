# myapp/management/commands/check_documentos.py

import requests
import pandas as pd
from django.core.management.base import BaseCommand
from myapp.models import (
    Soat,
    RevisionTecnomecanica,
    TarjetaOperacion,
    PolizaContractual,
    PolizaExtracontractual,
)

class Command(BaseCommand):
    help = 'Revisa URLs de documentos con estado=True, detecta 404 y soportes vacíos, y genera reporte Excel.'

    def handle(self, *args, **options):
        records = []
        specs = [
            ('Soat', Soat, 'vigencia_desde', 'vigencia_hasta'),
            ('RevisionTecnomecanica', RevisionTecnomecanica, 'fecha_expedicion', 'fecha_vencimiento'),
            ('TarjetaOperacion', TarjetaOperacion, 'fechaInicialVigencia', 'fechaFinVigencia'),
            ('PolizaContractual', PolizaContractual, 'fecha_inicio_vigencia', 'fecha_fin_vigencia'),
            ('PolizaExtracontractual', PolizaExtracontractual, 'fecha_inicio_vigencia', 'fecha_fin_vigencia'),
        ]

        for model_name, Model, start_field, end_field in specs:
            for obj in Model.objects.filter(estado=True):
                url = (obj.soporte or '').strip()
                # placa: si existe atributo placa, sino tomar de obj.vehiculo.placa
                placa = ''
                if hasattr(obj, 'placa') and obj.placa:
                    placa = obj.placa
                elif obj.vehiculo and hasattr(obj.vehiculo, 'placa') and obj.vehiculo.placa:
                    placa = obj.vehiculo.placa

                inicio = getattr(obj, start_field)
                fin = getattr(obj, end_field)

                if not url:
                    records.append({
                        'modelo': model_name,
                        'placa': placa,
                        'url': url,
                        'vigencia_inicio': inicio,
                        'vigencia_fin': fin,
                        'error': 'Soporte vacío',
                    })
                elif url.lower().startswith('http'):
                    try:
                        r = requests.head(url, allow_redirects=True, timeout=10)
                        if r.status_code == 404:
                            records.append({
                                'modelo': model_name,
                                'placa': placa,
                                'url': url,
                                'vigencia_inicio': inicio,
                                'vigencia_fin': fin,
                                'error': '404 Not Found',
                            })
                    except requests.RequestException as e:
                        records.append({
                            'modelo': model_name,
                            'placa': placa,
                            'url': url,
                            'vigencia_inicio': inicio,
                            'vigencia_fin': fin,
                            'error': str(e),
                        })

        if records:
            df = pd.DataFrame(records)
            output_path = 'documentos_fallidos3.xlsx'
            df.to_excel(output_path, index=False)
            self.stdout.write(self.style.SUCCESS(f'Reporte generado en {output_path}'))
        else:
            self.stdout.write('No se encontraron documentos con errores.')
