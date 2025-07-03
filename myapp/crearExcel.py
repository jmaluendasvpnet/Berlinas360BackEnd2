import io
import json
import pandas as pd
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["POST"])
def generar_excel(request):
    if request.method == 'POST':
        if request.body:
            JsonData = json.loads(request.body)

            if isinstance(JsonData.get("results"), str):
                JsonData = json.loads(JsonData["results"])

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for idx, data in enumerate(JsonData, start=1):
                    if isinstance(data, list):
                        dataframe = pd.DataFrame(data)
                    elif isinstance(data, dict):
                        if idx == 1:
                            dataframe = pd.DataFrame(JsonData)
                        else:
                            continue
                    else:
                        return JsonResponse({'error': 'Los datos deben ser una lista o un diccionario'})

                    dataframe.to_excel(
                        writer, index=False, sheet_name=f'Sheet{idx}')

                    worksheet = writer.sheets[f'Sheet{idx}']

                    for column in worksheet.columns:
                        max_length = 0
                        column = [cell for cell in column]
                        try:
                            max_length = max(len(str(cell.value))
                                             for cell in column)
                        except:
                            pass
                        adjusted_width = (max_length + 2)
                        worksheet.column_dimensions[column[0]
                                                    .column_letter].width = adjusted_width

            output.seek(0)

            response = HttpResponse(output.getvalue(),
                                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=JsonData.xlsx'

            return response

        return JsonResponse({'error': 'No se recibieron datos de JsonData en el cuerpo de la solicitud'})
    return JsonResponse({'error': 'Se esperaba una solicitud POST'})
