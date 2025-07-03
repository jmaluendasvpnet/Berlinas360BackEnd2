from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from openpyxl.styles import Font, Alignment
from openpyxl import load_workbook
from datetime import datetime
import json
import pytz
import os
import io


@csrf_exempt
@require_http_methods(["POST"])
def generarRptoAlcoholimetria(request):
    if request.method == 'POST':
        # Verificar si hay datos en la solicitud
        if request.body:
            # Decodificar los datos JSON de la solicitud
            results = json.loads(request.body)

            datos = results['results']
            tipoInforme = int(results['tipoInforme'])
            print(tipoInforme)

            # Obtener la ruta absoluta de la plantilla Excel en el mismo directorio que el script
            script_dir = os.path.dirname(__file__)

            if tipoInforme == 0:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_Alcoholimetria_Detallado.xlsx')
            elif tipoInforme == 1:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_CuotaAdmin_Ciudades.xlsx')
            elif tipoInforme == 2:
                plantilla_path = os.path.join(
                    script_dir, '../docs/Plantillas/Plantilla_Rpto_CuotaAdmin_Propietarios.xlsx')

            # Verificar si existe el archivo
            if os.path.exists(plantilla_path):
                # Cargar la plantilla Excel
                workbook = load_workbook(plantilla_path)
                sheet = workbook.active

                # Obtener la fecha y hora actual en UTC
                current_datetime_utc = datetime.now(pytz.utc)

                # Convertir la hora a la zona horaria deseada
                timezone = pytz.timezone('America/Bogota')
                current_datetime_bogota = current_datetime_utc.astimezone(
                    timezone)

                # Formatear la fecha y hora
                current_date = current_datetime_bogota.strftime('%Y-%m-%d')
                current_time = current_datetime_bogota.strftime('%H:%M:%S')

                if tipoInforme == 0:
                    # Ubicación específica para la columna 1 en la celda B9
                    start_column_col1 = 'A'
                    start_row_col1 = 8

                    # Ubicación específica para la columna 2 en la celda D9
                    start_column_col2 = 'D'
                    start_row_col2 = 8

                    # Ubicación específica para la columna 3 en la celda F9
                    start_column_col3 = 'F'
                    start_row_col3 = 8

                    # Ubicación específica para la columna 4 en la celda H9
                    start_column_col4 = 'H'
                    start_row_col4 = 8

                    # Escribir la fecha actual en la celda B6
                    cell_c6 = sheet['B6']
                    cell_c6.value = current_date

                    # Escribir la hora actual en la celda D6
                    cell_d6 = sheet['D6']
                    cell_d6.value = current_time

                    for index, colaborador in enumerate(datos, start=1):
                        for col_index, (col_name, col_value) in enumerate(colaborador.items(), start=1):

                            # Escribir en la columna 1
                            if col_index == 1:
                                cell_col1 = sheet[f'{start_column_col1}{start_row_col1 + index}']
                                cell_col1.value = col_value
                                cell_col1.alignment = Alignment(
                                    horizontal='center')

                            # Escribir en la columna 2
                            elif col_index == 2:
                                cell_col2 = sheet[f'{start_column_col2}{start_row_col2 + index}']
                                cell_col2.value = col_value
                                cell_col2.alignment = Alignment(
                                    horizontal='center')

                            # Escribir en la columna 3
                            elif col_index == 3:
                                cell_col3 = sheet[f'{start_column_col3}{start_row_col3 + index}']
                                cell_col3.value = col_value
                                cell_col3.alignment = Alignment(
                                    horizontal='center')

                            # Escribir en la columna 4
                            elif col_index == 4:
                                cell_col4 = sheet[f'{start_column_col4}{start_row_col4 + index}']
                                cell_col4.value = col_value
                                cell_col4.alignment = Alignment(
                                    horizontal='center')

                elif tipoInforme == 4:
                    # Ubicación específica para la columna 1 en la celda G6
                    start_column_col1 = 'B'
                    start_row_col1 = 8

                    # Ubicación específica para la columna 3 en la celda I6
                    start_column_col3 = 'C'
                    start_row_col3 = 8

                    # Ubicación específica para la columna 4 en la celda C9
                    start_column_col4 = 'D'
                    start_row_col4 = 8

                    # Ubicación específica para la columna 5 en la celda D9
                    start_column_col5 = 'F'
                    start_row_col5 = 8

                    # Ubicación específica para la columna 6 en la celda F9
                    start_column_col6 = 'H'
                    start_row_col6 = 8

                    # Escribir la fecha actual en la celda B6
                    cell_c6 = sheet['B6']
                    cell_c6.value = current_date

                    # Escribir la hora actual en la celda D6
                    cell_d6 = sheet['D6']
                    cell_d6.value = current_time

                    # Escribir los datos de datos en ubicaciones específicas
                    # Variable para almacenar la suma de la columna 6 (flotante)
                    sum_col5 = 0.0
                    # Variable para almacenar la suma de la columna 6 (flotante)
                    sum_col6 = 0.0

                    for index, colaborador in enumerate(datos, start=1):
                        for col_index, (col_name, col_value) in enumerate(colaborador.items(), start=1):

                            # Escribir en la columna 1
                            if col_index == 1:
                                cell_col1 = sheet[f'{start_column_col1}{start_row_col1 + index}']
                                cell_col1.value = col_value

                            # Escribir en la columna 3
                            elif col_index == 3:
                                cell_col3 = sheet[f'{start_column_col3}{start_row_col3 + index}']
                                cell_col3.value = col_value

                            # Escribir en la columna 4
                            elif col_index == 4:
                                cell_col4 = sheet[f'{start_column_col4}{start_row_col4 + index}']
                                cell_col4.value = col_value

                            elif col_index == 5:
                                cell_col5 = sheet[f'{start_column_col5}{start_row_col5 + index}']
                                cell_col5.value = col_value
                                # Convertir a flotante y sumar los valores de la columna 6
                                sum_col5 += float(col_value)

                            # Escribir en la columna 6
                            elif col_index == 6:
                                cell_col6 = sheet[f'{start_column_col6}{start_row_col6 + index}']
                                cell_col6.value = col_value
                                # Convertir a flotante y sumar los valores de la columna 6
                                sum_col6 += float(col_value)

                    # Escribir las sumas al final de las filas de resultados y aplicar el estilo en negrita
                    cell_sum_col5 = sheet[f'{start_column_col5}{start_row_col5 + len(datos) + 1}']
                    cell_sum_col5.value = sum_col5
                    cell_sum_col5.font = Font(bold=True)
                    cell_sum_col5.alignment = Alignment(horizontal='right')

                    # Escribir las sumas al final de las filas de resultados y aplicar el estilo en negrita
                    cell_sum_col6 = sheet[f'{start_column_col6}{start_row_col6 + len(datos) + 1}']
                    cell_sum_col6.value = sum_col6
                    cell_sum_col6.font = Font(bold=True)
                    cell_sum_col6.alignment = Alignment(horizontal='right')

                    # Escribir "-totales-" en negrita en la columna 3 al final de los datos
                    cell_totals = sheet[f'{start_column_col4}{start_row_col4 + len(datos) + 1}']
                    cell_totals.value = "Totales"
                    cell_totals.font = Font(bold=True)

                elif tipoInforme == 5:
                    # Ubicación específica para la columna 1 en la celda B9
                    start_column_col1 = 'B'
                    start_row_col1 = 8

                    # Ubicación específica para la columna 2 en la celda D9
                    start_column_col2 = 'D'
                    start_row_col2 = 8

                    # Ubicación específica para la columna 3 en la celda F9
                    start_column_col3 = 'F'
                    start_row_col3 = 8

                    # Ubicación específica para la columna 4 en la celda H9
                    start_column_col4 = 'H'
                    start_row_col4 = 8

                    # Escribir la hora actual en la celda D6
                    cell_d6 = sheet['D6']
                    cell_d6.value = current_time

                    # Escribir los datos de datos en ubicaciones específicas
                    # Variable para almacenar la suma de la columna 3 (flotante)
                    sum_col3 = 0.0
                    # Variable para almacenar la suma de la columna 4 (flotante)
                    sum_col4 = 0.0

                    for index, colaborador in enumerate(datos, start=1):
                        for col_index, (col_name, col_value) in enumerate(colaborador.items(), start=1):

                            # Escribir en la columna 1
                            if col_index == 1:
                                cell_col1 = sheet[f'{start_column_col1}{start_row_col1 + index}']
                                cell_col1.value = col_value

                            # Escribir en la columna 2
                            elif col_index == 2:
                                cell_col2 = sheet[f'{start_column_col2}{start_row_col2 + index}']
                                cell_col2.value = col_value

                            # Escribir en la columna 3
                            elif col_index == 3:
                                cell_col3 = sheet[f'{start_column_col3}{start_row_col3 + index}']
                                cell_col3.value = col_value
                                # Convertir a flotante y sumar los valores de la columna 6
                                sum_col3 += float(col_value)

                            # Escribir en la columna 4
                            elif col_index == 4:
                                cell_col4 = sheet[f'{start_column_col4}{start_row_col4 + index}']
                                cell_col4.value = col_value
                                # Convertir a flotante y sumar los valores de la columna 6
                                sum_col4 += float(col_value)

                    # Escribir las sumas al final de las filas de resultados y aplicar el estilo en negrita
                    cell_sum_col3 = sheet[f'{start_column_col3}{start_row_col3 + len(datos) + 1}']
                    cell_sum_col3.value = sum_col3
                    cell_sum_col3.font = Font(bold=True)
                    cell_sum_col3.alignment = Alignment(horizontal='right')

                    # Escribir las sumas al final de las filas de resultados y aplicar el estilo en negrita
                    cell_sum_col4 = sheet[f'{start_column_col4}{start_row_col4 + len(datos) + 1}']
                    cell_sum_col4.value = sum_col4
                    cell_sum_col4.font = Font(bold=True)
                    cell_sum_col4.alignment = Alignment(horizontal='right')

                    # Escribir "-totales-" en negrita en la columna 1 al final de los datos
                    cell_totals = sheet[f'{start_column_col1}{start_row_col1 + len(datos) + 1}']
                    cell_totals.value = "Totales"
                    cell_totals.font = Font(bold=True)

                # Crear un objeto BytesIO para guardar temporalmente el archivo Excel
                buffer = io.BytesIO()
                workbook.save(buffer)
                buffer.seek(0)

                # Crear la respuesta con el nuevo archivo Excel
                response = HttpResponse(
                    buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=Plantilla_Rpto_CuotaAdmin.xlsx'

                return response
            else:
                return JsonResponse({'error': 'El archivo de la plantilla no fue encontrado'})
        else:
            return JsonResponse({'error': 'Se esperaba una solicitud POST'})
    else:
        return JsonResponse({'error': 'Se esperaba una solicitud POST'})
