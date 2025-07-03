from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .AdminDBUtilsConn import ConexionDB
from django.http import JsonResponse
from datetime import datetime
from .models import RptoFuec
from decimal import Decimal
import pyodbc
import json
import os


@csrf_exempt
@require_http_methods(["POST"])
def rptoFuec(request):
    try:
        if request.method == "POST":
            fecha = request.POST.get('fecha', None)
            bus = request.POST.get('bus', None)

            if not fecha:
                fecha = datetime.now()

            print("Bus: " + str(bus) + " Fecha: " + str(fecha))

            conn = ConexionDB()
            cursor = conn.cursor()
            cursor.execute("{CALL RP_FS_BUS (?, ?)}", (bus, fecha))
            results = cursor.fetchall()

            rows_list = []
            for row in results:
                rows_list.append({
                    'viaje': row[0],
                    'fecha': row[1].strftime('%Y-%m-%d %H:%M:%S'),
                    'origen': row[2],
                    'destino': row[3]
                })

            cursor.close()
            conn.close()

            return JsonResponse({'results': [rows_list]})
        else:
            print("error")
    except pyodbc.Error as ex:
        print("Error:", ex)


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def convert_to_dict(row, columns):
    converted_row = []
    for value, column in zip(row, columns):
        if isinstance(value, datetime):
            value = value.strftime("%Y-%m-%d %H:%M:%S")
        converted_row.append(value)
    return converted_row


@csrf_exempt
@require_http_methods(["POST"])
def rptoFuecPDF(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print(data)
        Nviaje = int(data['viaje'])
        Motivo = 'TRANSPORTE DE PARTICULARES (GRUPO - PERSONA NATURAL)'
        Cliente = 860015624
        op = 1

        conn = ConexionDB()
        cursor = conn.cursor()
        cursor.execute(
            "{CALL RP_Formato_ServicioEspecial (?, ?, ?, ?)}", (Nviaje, Motivo, Cliente, op))

        cursor.execute("SELECT [Viaje], [FechaPartida], [Bus], [Placa], [Descripcion_Clase], [Descripcion_Marca], [Modelo], [Origen], [Destino], [Empresa_Registrado], [Nit_Emp], [dir_Emp], [tel_emp], [tel_emp1], [ema_emp], [Ciudad_Empresa], [Num_Tarjeta_Operacion], [Nombre_Conductor1], [Apellido_Conductor1], [Cedula_Conductor1], [Pase1_Conductor1], [fechavencimiento1_Conductor1], [Nombre_Conductor2], [Apellido_Conductor2], [Cedula_Conductor2], [Pase1_Conductor2], [fechavencimiento1_Conductor2], [NIT_Cliente], [Nombre_Cliente], [Direccion_Cliente], [Ciudad_Cliente], [Telefono_Cliente], [Objeto_Contrato], [Rep_cedula], [Rep_Apellidos], [Rep_Nombres], [Rep_Telefono], [Consecutivo_FUEC], [Modificar], [Talonario], [Usuario], [Fechasistema] FROM [DynamiX].[dbo].[FUEC_Transaccion] WHERE Viaje = ?", Nviaje)
        row = cursor.fetchone()
        # print(row)

        if row is not None:
            columns = [column[0] for column in cursor.description]
            converted_row = convert_to_dict(row, columns)

            # Conversion a diccionario
            resultss = dict(zip(columns, converted_row))
            results = {key: value.rstrip() if isinstance(
                value, str) else value for key, value in resultss.items()}

            conn.commit()
            conn.close()

            return JsonResponse({'results': results})
        else:
            return JsonResponse({'error': 'No se encontraron resultados para el viaje especificado'})
    else:
        print("error")


def saveRpto(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        modifiedFields = request.POST.get('modifiedFields', '')
        bus = request.POST.get('bus', '')
        viaje = request.POST.get('viaje', '')
        username = request.POST.get('username', '')
        file_path = os.path.join('./docs/Fuec', pdf_file.name)
        print(bus, viaje)

        with open(file_path, 'wb') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)

        num_bus = request.POST.get('bus')
        try:
            num_bus = int(num_bus)
            RptoFuec.objects.create(nom_fuec=pdf_file.name, modificaciones=modifiedFields,
                                    num_bus=num_bus, num_viaje=viaje, user_creo=username)
            print("Guardado en servidor para el bus " +
                  str(num_bus) + " con viaje " + viaje)
            return JsonResponse({'message': 'Archivo PDF guardado exitosamente'})
        except ValueError:
            return JsonResponse({'message': 'El campo num_bus debe ser un número válido'}, status=400)
    else:
        return JsonResponse({'message': 'No se ha proporcionado un archivo PDF'}, status=400)
