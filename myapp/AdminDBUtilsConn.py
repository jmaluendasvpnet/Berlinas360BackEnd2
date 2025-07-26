from datetime import datetime
from decimal import Decimal
import pyodbc


def ConexionDB():
    # server = 'd1.berlinasdelfonce.com'
    server = '172.16.0.25'
    database = 'Dynamix'
    username = 'Developer'
    password = '123456'

    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+password)
        return conn
    except pyodbc.Error as ex:
        print("Error al establecer la conexión a la base de datos:", ex)
        return None


def formatResults(cursor):
    columns = [column[0] for column in cursor.description]
    results = cursor.fetchall()

    rows_list = []
    for row in results:
        row_dict = {}
        for index, value in enumerate(row):
            column_name = columns[index]
            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, str):
                value = value.rstrip()  # Eliminar espacios al final de la cadena
            elif isinstance(value, Decimal):  # Verificar si el valor es Decimal
                value = float(value)  # Convertir Decimal a float
                value = round(value)  # Redondear si es necesario
            row_dict[column_name] = value
        rows_list.append(row_dict)

    return rows_list
