from django.views.decorators.http import require_http_methods
from .AdminDBUtilsConn import ConexionDB, formatResults
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from dateutil import parser
import pyodbc


def execute_stored_procedure(stored_procedure, params):
    conn = ConexionDB()
    cursor = conn.cursor()
    try:
        try:
            cursor.execute(stored_procedure, params)
        except Exception as e:
            print(e)

        # Lee el primer conjunto de resultados
        rows_list = formatResults(cursor)

        # Verifica si hay mas conjuntos de resultados
        results_list = [rows_list]
        while cursor.nextset():
            rows_list = formatResults(cursor)
            results_list.append(rows_list)

        # print(results_list)

        return results_list
    finally:
        cursor.close()
        conn.close()


@csrf_exempt
@require_http_methods(["POST"])
def UsuarioFrecuente(request):
    if request.method == "POST":
        try:
            cedula = request.POST.get('dni', None)
            rows_list = execute_stored_procedure(
                "{CALL UsuarioFrecuente (?)}", (cedula,))
            return JsonResponse({'results': [rows_list]})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def RP_Dominicales(request):
    if request.method == "POST":
        try:
            fechaInicio = request.POST.get('startDate', None)
            fechaFinal = request.POST.get('endDate', None)
            try:
                EmpID = int(request.POST.get('empresa', None))
            except:
                pass
            opcion = int(request.POST.get('Opcion', None))
            rows_list = execute_stored_procedure(
                "{CALL RP_Dominicales (?, ?, ?, ?)}", (EmpID, fechaInicio, fechaFinal, opcion))
            return JsonResponse({'results': [rows_list]})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def VO_ViajeroFrecuente(request):
    try:
        if request.method == "POST":
            cedula = request.POST.get('dni', None)
            op = 3

            conn = ConexionDB()
            cursor = conn.cursor()

            cursor.execute(
                "{CALL VO_ViajeroFrecuente (?, ?)}", (cedula, op))

            cursor.close()
            conn.close()

            return JsonResponse({'results': "Correctamente"})
        else:
            print("error")
    except pyodbc.Error as ex:
        print("Error:", ex)


@csrf_exempt
@require_http_methods(["POST"])
def RP_Prueba_Alcoholimetria(request):
    if request.method == "POST":
        try:
            FechaDesde = request.POST.get('startDate', None)
            FechaHasta = request.POST.get('endDate', None)
            operacion = request.POST.get('concepto', None)
            EmpId_Param = request.POST.get('empresa', None)
            Valor_Prueba = "1000"

            rows_list = execute_stored_procedure(
                "{CALL RP_Prueba_Alcoholimetria (?, ?, ?, ?, ?)}",
                (EmpId_Param, FechaDesde, FechaHasta, Valor_Prueba, operacion))
            return JsonResponse({'results': rows_list})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def RP_ConsultaVO(request):
    if request.method == "POST":
        try:
            fechainicio = request.POST.get('startDate', None)
            fechaFinal = request.POST.get('endDate', None)
            desviacion = 5
            opcion = int(request.POST.get('opcion', None))
            Consulta = int(request.POST.get('concepto', None))
            Servicio = 1
            print(fechainicio, fechaFinal, 'Opcion: ', opcion,
                  ' Consulta: ', Consulta, ' Servicio: ', Servicio)

            rows_list = execute_stored_procedure(
                "{CALL RP_ConsultaVO (?, ?, ?, ?, ?, ?)}",
                (fechainicio, fechaFinal, desviacion, opcion, Consulta, Servicio,))
            print(rows_list)
            return JsonResponse({'results': rows_list})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def RP_CuotaAdmon(request):
    if request.method == "POST":
        try:
            FechaInicio = request.POST.get('startDate', None)
            FechaFinal = request.POST.get('endDate', None)
            codigo = request.POST.get('codigo', None)
            tipo_informe = request.POST.get('tipoInforme', None)
            concepto = request.POST.get('concepto', None)
            EmpId = request.POST.get('empresa', None)

            fecha_inicio_obj = parser.parse(FechaInicio)
            mes = fecha_inicio_obj.month
            anio = fecha_inicio_obj.year

            rows_list = execute_stored_procedure(
                "{CALL RP_CuotaAdmon (?, ?, ?, ?, ?, ?, ?, ?)}",
                (EmpId, anio, mes, FechaInicio, FechaFinal, 0, concepto, tipo_informe))
            return JsonResponse({'results': rows_list})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def Rp_VF3(request):
    if request.method == "POST":
        try:
            year = request.POST.get('year', None)
            mes = request.POST.get('month', None)
            operacion = request.POST.get('tipoInforme', None)
            rows_list = execute_stored_procedure(
                "{CALL Rp_VF3 (?, ?, ?)}", (year, mes, operacion))
            return JsonResponse({'results': [rows_list]})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def RP_Consultas05(request):
    if request.method == "POST":
        try:
            Empid = request.POST.get('empresa', None)
            fechaInicio = request.POST.get('startDate', None)
            fechaFinal = request.POST.get('endDate', None)
            Opcion = int(request.POST.get('Opcion', None))
            SubOpcion = request.POST.get('SubOpcion', None)
            Cadena01 = request.POST.get('Cadena01', None)
            Cadena02 = "VACIO"

            if Opcion == 12 or Opcion == 14:
                Cadena01 = request.POST.get('Cadena01', None)
            elif Opcion == 22:
                if SubOpcion == 0:
                    Cadena01 = "65"
                    Cadena02 = "VACIO"
                elif SubOpcion == 1:
                    Cadena01 = "VACIO"
                    Cadena02 = "1"
            elif Cadena01 == None and (Opcion == 13):
                Cadena01 = "24445"

            if Opcion == 14:
                Cadena02 = request.POST.get('Cadena02', None)
            elif Opcion == 22:
                Cadena02 = '1'
            elif Opcion == 28:
                Cadena02 = '65'
            else:
                Cadena02 = "VACIO"

            valor = 100
            try:
                rows_list = execute_stored_procedure("{CALL RP_Consultas05 (?, ?, ?, ?, ?, ?, ?, ?)}",
                                                     (Empid, fechaInicio, fechaFinal, Opcion, SubOpcion, Cadena01, Cadena02, valor))
            except Exception as e:
                print("Eroor:", e)
            return JsonResponse({'results': rows_list})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def Sp_RptHistoFuec(request):
    if request.method == "POST":
        try:
            EmpID = request.POST.get('empresa', None)
            Fechaini = request.POST.get('startDate', None)
            Fechafin = request.POST.get('endDate', None)
            rows_list = execute_stored_procedure("{CALL Sp_RptHistoFuec (?, ?, ?)}",
                                                 (Fechaini, Fechafin, EmpID))
            return JsonResponse({'results': rows_list})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def RP_consultas01(request):
    try:
        if request.method == "POST":
            EmpID = request.POST.get('empresa', None)
            Fechainicio = request.POST.get('startDate', None)
            FechaFinal = request.POST.get('endDate', None)
            Opcion = request.POST.get('Opcion', None)
            datocontrol = '0'

            results_list = execute_stored_procedure(
                "{CALL RP_consultas01 (?, ?, ?, ?, ?)}",
                (EmpID, Fechainicio, FechaFinal, datocontrol, Opcion)
            )

            return JsonResponse({'results': results_list})
        else:
            print("error")
    except pyodbc.Error as ex:
        print("Error:", ex)


@csrf_exempt
@require_http_methods(["POST"])
def Rp_certificaciones(request):
    if request.method == "POST":
        try:
            documento = request.POST.get('documento', None)
            rows_list = execute_stored_procedure("{CALL Rp_certificaciones (?)}",
                                                 (documento))
            return JsonResponse({'results': [rows_list]})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def RP_CondvigFICS(request):
    if request.method == "POST":
        try:
            rows_list = execute_stored_procedure(
                "{CALL RP_CondvigFICS ()}", ())
            return JsonResponse({'results': [rows_list]})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def RP_Macarena(request):
    if request.method == "POST":
        try:
            Fechaini = request.POST.get('startDate', None)
            Fechafin = request.POST.get('endDate', None)
            Opcion = int(request.POST.get('Opcion', None))
            rows_list = execute_stored_procedure("{CALL RP_Macarena (?, ?, ?)}",
                                                 (Fechaini, Fechafin, Opcion))
            return JsonResponse({'results': [rows_list]})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def Fics_MicroSegurosGET(request):
    if request.method == "POST":
        try:
            Desde = request.POST.get('startDate', None)
            Hasta = request.POST.get('endDate', None)
            Tipo = 1
            rows_list = execute_stored_procedure(
                "{CALL Fics_MicroSegurosGET (?, ?, ?)}", (Desde, Hasta, Tipo))
            return JsonResponse({'results': [rows_list]})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def RP_Consultas04(request):
    if request.method == "POST":
        try:
            EmpiD = request.POST.get('empresa', None)
            fechaInicio = request.POST.get('startDate', None)
            fechaFinal = request.POST.get('endDate', None)
            Opcion = request.POST.get('Opcion', None)
            SubOpcion = request.POST.get('SubOpcion', None)
            Cadena01 = "VACIO"
            Cadena02 = "VACIO"
            valor01 = 100
            rows_list = execute_stored_procedure(
                "{CALL RP_Consultas04 (?, ?, ?, ?, ?, ?, ?, ?)}", (EmpiD, fechaInicio, fechaFinal, Opcion, SubOpcion, Cadena01, Cadena02, valor01))
            return JsonResponse({'results': rows_list})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def RP_MIGRACION(request):
    if request.method == "POST":
        try:
            EmpID = 1
            Viaje = 5612
            Terminal = request.POST.get('Terminal', None)
            Fecha = request.POST.get('selectedDate', None)
            Opcion = request.POST.get('Opcion', None)
            rows_list = execute_stored_procedure("{CALL RP_MIGRACION (?, ?, ?, ?, ?)}",
                                                 (EmpID, Viaje, Terminal, Fecha, Opcion))
            return JsonResponse({'results': rows_list})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def RPT_EstadisticaXTaquilla(request):
    if request.method == "POST":
        try:
            Mes = int(request.POST.get('month', None))
            Year = int(request.POST.get('year', None))
            Taquilla = request.POST.get('Opcion', None)
            try:
                Documento = request.POST.get('Documento', None)
            except:
                Documento = None
            try:
                Fecha = request.POST.get('Fecha', None)
            except:
                Fecha = None

            if Documento:
                Opcion = 2
            elif Fecha:
                Opcion = 3
            else:
                Opcion = 1

            rows_list = execute_stored_procedure(
                "{CALL RPT_EstadisticaXTaquilla (?, ?, ?, ?, ?, ?)}", (Mes, Year, Fecha, Documento, Opcion, Taquilla))
            return JsonResponse({'results': rows_list})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def Rp_CRM(request):
    if request.method == "POST":
        try:
            fechaInicio = request.POST.get('startDate', None)
            fechaFinal = request.POST.get('endDate', None)
            fecTransaccion = request.POST.get('Date', None)
            Opcion = request.POST.get('Opcion', None)
            rows_list = execute_stored_procedure("{CALL Rp_CRM (?, ?, ?, ?)}",
                                                 (fechaInicio, fechaFinal, fecTransaccion, Opcion))
            return JsonResponse({'results': [rows_list]})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def PD_GetExtractoTER(request):
    if request.method == "POST":
        try:
            EmpresaID = request.POST.get('empresa', None)
            FechaInicio = request.POST.get('startDate', None)
            Fechafinal = request.POST.get('endDate', None)
            TerceroID = request.POST.get('TerceroID', None)
            bProcID = 1

            print(EmpresaID, FechaInicio, Fechafinal, TerceroID)

            rows_list = execute_stored_procedure(
                "{CALL PD_GetExtractoTER (?, ?, ?, ?, ?)}",
                (EmpresaID, FechaInicio, Fechafinal, TerceroID, bProcID))

            print(rows_list)

            return JsonResponse({'results': rows_list})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")


@csrf_exempt
@require_http_methods(["POST"])
def AC_ComTaqNoNomina(request):
    if request.method == "POST":
        try:
            Caj_EmpID = int(request.POST.get('empresa', None))
            Caj_Year = int(request.POST.get('year', None))
            Caj_Mes = int(request.POST.get('month', None))
            print(Caj_EmpID, Caj_Year, Caj_Mes)
            print(type(Caj_EmpID), type(Caj_Year), type(Caj_Mes))
            rows_list = execute_stored_procedure(
                "{CALL AC_ComTaqNoNomina (?, ?, ?)}", (Caj_EmpID, Caj_Year, Caj_Mes))
            print(rows_list)
            return JsonResponse({'results': rows_list})
        except pyodbc.Error as ex:
            return JsonResponse({'error': 'Error de base de datos'}, status=500)
    else:
        print("error")
