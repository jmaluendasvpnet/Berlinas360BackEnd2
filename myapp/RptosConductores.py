from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from openpyxl.styles import Alignment
from openpyxl import load_workbook
from datetime import datetime
import json
import pytz
import os
import io


@csrf_exempt
@require_http_methods(["POST"])
def generarRptoConductores(request):
    if request.method == 'POST':
        # Verificar si hay datos en la solicitud
        if request.body:
            # Decodificar los datos JSON de la solicitud
            results = json.loads(request.body)

            datos = json.loads(results['results'])
            Opcion = int(results['Opcion'])
            try:
                year = results['year']
                month = results['month']
            except:
                pass

            # Obtener la ruta absoluta de la plantilla Excel en el mismo directorio que el script
            script_dir = os.path.dirname(__file__)

            if Opcion == 0:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_TurismoEstadisticaViajeroFrecuenteBerlinas.xlsx')
            elif Opcion == 1:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_TurismoEstadisticaViajeroFrecuenteServicioEspecial.xlsx')
            elif Opcion == 2:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_TurismoEstadisticaViajeroFrecuenteDuo.xlsx')
            elif Opcion == 3:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_TurismoEstadisticaViajerosFrecuentes.xlsx')
            elif Opcion == 4:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_TurismoEstadisticaTiqueteViajeroFrecuenteBerlinas.xlsx')
            elif Opcion == 5:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_TurismoEstadisticaTiqueteViajeroFrecuenteServicioEspecial.xlsx')
            elif Opcion == 6:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_TurismoEstadisticaTiqueteViajeroFrecuenteDuo.xlsx')
            elif Opcion == 7:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_TurismoEstadisticaVentaOnline.xlsx')
            elif Opcion == 8:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_TurismoEstadisticaProspectoParaIngresarAViajeroFrecuente.xlsx')
            elif Opcion == 99:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_Reportes_RptoConductores.xlsx')

            # Verificar si existe el archivo
            if os.path.exists(plantilla_path):
                try:
                    # Carga de la plantilla Excel
                    workbook = load_workbook(plantilla_path)
                except Exception as e:
                    print(f"Error al cargar la plantilla: {e}")
                    return JsonResponse({'error': f"Error al cargar la plantilla: {e}"})

                sheet = workbook.active

                # Obtener la fecha y hora actual en UTC
                current_datetime_utc = datetime.now(pytz.utc)

                # Convertir la hora a la zona horaria deseada
                current_datetime_bogota = current_datetime_utc.astimezone(
                    pytz.timezone('America/Bogota'))

                # Formatear la fecha y hora
                current_date = current_datetime_bogota.strftime('%Y-%m-%d')
                current_time = current_datetime_bogota.strftime('%H:%M:%S')

                # Ubicación para month y year del reporte
                try:
                    cell_year = sheet['D6']
                    cell_year.value = year

                    cell_month = sheet['F6']
                    cell_month.value = month
                except:
                    pass

                # Escribir la fecha actual en la celda B6
                cell_c6 = sheet['B6']
                cell_c6.value = current_date

                # Escribir la hora actual en la celda D6
                cell_d6 = sheet['A6']
                cell_d6.value = current_time

                for index, colaborador in enumerate(datos, start=1):
                    for col_index, (col_name, col_value) in enumerate(colaborador.items(), start=1):
                        if col_index <= 19:  # Hacer el bucle solo hasta la columna 19
                            column_letter = chr(ord('B') + col_index - 1)
                            # 8 es el numero de fila start
                            cell_col = sheet[f'{column_letter}{8 + index}']
                            cell_col.value = col_value
                            cell_col.alignment = Alignment(horizontal='center')

                # Crear un objeto BytesIO para guardar temporalmente el archivo Excel
                buffer = io.BytesIO()
                workbook.save(buffer)
                buffer.seek(0)

                # Crear la respuesta con el nuevo archivo Excel
                response = HttpResponse(
                    buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=Result.xlsx'

                return response
            else:
                return JsonResponse({'error': 'El archivo de la plantilla no fue encontrado'})
        else:
            return JsonResponse({'error': 'Se esperaba una solicitud POST'})
    else:
        return JsonResponse({'error': 'Se esperaba una solicitud POST'})
