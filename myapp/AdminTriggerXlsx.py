from openpyxl.styles import Alignment, Font
from datetime import datetime
import pytz


def write_name_company(sheet, empresa, column_colEmp, row_colEmp):
    cell_colEmp = sheet[f'{column_colEmp}{row_colEmp}']
    if empresa == 277:
        cell_colEmp.value = "Berlinas del Fonce S.A."
    elif empresa == 278:
        cell_colEmp.value = "Berlitur S.A.S"
    elif empresa == 300:
        cell_colEmp.value = "Compañia Libertador S.A."
    elif empresa == 310:
        cell_colEmp.value = "Cartagena International Travels S.A.S"
    elif empresa == 9001:
        cell_colEmp.value = "Servicio Especial"
    elif empresa == 320:
        cell_colEmp.value = "Tourline Express S.A.S"

    cell_colEmp.alignment = Alignment(horizontal='center')
    cell_colEmp.font = Font(bold=True)

    return cell_colEmp


def write_month_year(sheet, month, year, column_colMes, row_colMes, column_colYear, row_colYear):
    # Obtener la fecha y hora actual en UTC
    current_datetime_utc = datetime.now(pytz.utc)

    # Convertir la hora a la zona horaria deseada
    timezone = pytz.timezone('America/Bogota')
    current_datetime_bogota = current_datetime_utc.astimezone(timezone)

    # Formatear la fecha y hora
    current_date = current_datetime_bogota.strftime('%Y-%m-%d')
    current_time = current_datetime_bogota.strftime('%H:%M:%S')

    # Escribir Month
    cell_colMonth = sheet[f'{column_colMes}{row_colMes}']
    cell_colMonth.value = month
    cell_colMonth.alignment = Alignment(horizontal="left")

    # Escribir Year
    cell_colYear = sheet[f'{column_colYear}{row_colYear}']
    cell_colYear.value = year
    cell_colYear.alignment = Alignment(horizontal="left")

    # Escribir la fecha actual en la celda B6
    cell_dateNow = sheet['B6']
    cell_dateNow.value = current_date

    # Escribir la hora actual en la celda D6
    cell_hourNow = sheet['D6']
    cell_hourNow.value = current_time

    return (cell_colMonth, cell_colYear, cell_dateNow, cell_hourNow)


def write_cell(sheet, column, row, value, alignment='center', number_format="#,###"):
    cell = sheet[f'{column}{row}']
    cell.value = value
    cell.alignment = Alignment(horizontal=alignment)
    if isinstance(value, (int)) and value != 0:
        cell.number_format = number_format


def write_totals(sheet, start_column, start_row, sum_values, num_rows, bold=True, number_format="#,###", columns_to_average=None):
    for i, sum_value in enumerate(sum_values, start=start_column):
        column_letter = chr(ord("A") + i)
        cell_sum = sheet[f'{column_letter}{start_row}']
        # Escribe la suma solo si la columna no esta promediada
        if columns_to_average and i not in columns_to_average:
            cell_sum.value = sum_value
            cell_sum.font = Font(bold=bold)
            cell_sum.alignment = Alignment(
                horizontal='center')
            if number_format:
                cell_sum.number_format = number_format

    if columns_to_average and start_column in columns_to_average:
        # Calculo e impresion del promedio
        average_value = round(
            sum(sum_values) / num_rows, 2)
        column_letter = chr(ord("A") + start_column)
        cell_average = sheet[f'{column_letter}{start_row}']
        cell_average.value = average_value
        cell_average.font = Font(bold=bold)
        cell_average.alignment = Alignment(
            horizontal='center')


def process_data(sheet, datos, start_row_col, columns_to_sum=None, columns_to_average=None):
    num_columns = len(datos[0])
    num_rows = len(datos)
    sum_cols = [0] * num_columns

    for index, colaborador in enumerate(datos, start=1):
        for col_index, (col_name, col_value) in enumerate(colaborador.items(), start=1):
            if col_index:
                column_letter = chr(ord('A') + col_index)
                try:
                    # Intentar convertir a entero solo si el valor no comienza con 0
                    if not str(col_value).startswith('0'):
                        col_value = int(col_value)
                except:
                    try:
                        col_value = round(float(col_value), 2)
                    except:
                        pass

                write_cell(sheet, column_letter,
                           start_row_col + index, col_value)
                if isinstance(col_value, (int, float)):
                    sum_cols[col_index -
                             1] += float(col_value)

    # Escribir totales al final de cada columna que se haya sumado
    for col_index, sum_value in enumerate(sum_cols, start=1):
        if col_index in columns_to_sum:
            column_letter = chr(ord('A') + col_index)
            write_totals(sheet, col_index, start_row_col + len(datos) + 1, [
                sum_value], num_rows, columns_to_average=columns_to_average)

    # Escribir "Totales" en negrita
    cell_totals = sheet[f'A{start_row_col + len(datos) + 1}']
    cell_totals.value = "Totales"
    cell_totals.font = Font(bold=True)
    cell_totals.alignment = Alignment(horizontal='center')

    return sheet
