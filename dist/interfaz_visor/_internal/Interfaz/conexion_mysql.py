import json
import os
import sys
import mysql.connector
from mysql.connector import Error

def resource_path(relative_path):
    """Obtiene la ruta absoluta compatible con ejecutable y desarrollo."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def leer_config():
    ruta_config = resource_path('Interfaz/config.json')
    with open(ruta_config, 'r', encoding='utf-8') as archivo:
        return json.load(archivo)

def conectar_mysql():
    try:
        config = leer_config()
        db_config = config['database']

        conexion = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['dbname'],
            auth_plugin='mysql_native_password'
        )

        if conexion.is_connected():
            print('Conexión lograda')
            return conexion

    except Error as e:
        print(f'Error al conectar a la base de datos: {e}')
        return None

if __name__ == '__main__':
    conectar_mysql()

