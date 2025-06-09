import mysql.connector
from mysql.connector import Error
import os
from activity.aw_utils import load_db_config # <--- Esta línea es crucial

def insertar_actividades(lista_actividades, config_file_path): # <--- Asegúrate de que el parámetro 'config_file_path' esté aquí
    conn = None
    try:
        db_config = load_db_config(config_file_path) # <--- Aquí se llama a la función

        if not db_config:
            print("Error: No se pudo cargar la configuración de la base de datos.")
            return False

        conn = mysql.connector.connect(
            host=db_config.get('host'),
            port=db_config.get('port'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            database=db_config.get('dbname')
        )
        cursor = conn.cursor()
        sql = """
            INSERT IGNORE INTO actividad
            (hora, app, titulo, duracion, categoria, subcategoria, dni, fecha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(sql, lista_actividades)
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error al insertar actividades en MySQL: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado en insertar_actividades: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()