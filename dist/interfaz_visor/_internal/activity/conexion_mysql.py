import mysql.connector
from mysql.connector import Error
from activity.aw_utils import load_db_config

def insertar_actividades(lista_actividades, config_file_path):
    conn = None
    try:
        with open('reporte_log.txt', 'a', encoding='utf-8') as log:
            log.write("[DEBUG] Entrando a insertar_actividades\n")
            log.write(f"[DEBUG] Total actividades a insertar: {len(lista_actividades)}\n")

        db_config = load_db_config(config_file_path)
        if not db_config:
            with open('reporte_log.txt', 'a', encoding='utf-8') as log:
                log.write("[ERROR] No se pudo cargar la configuración de la base de datos.\n")
            return False

        conn = mysql.connector.connect(
            host=db_config.get('host'),
            port=db_config.get('port'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            database=db_config.get('dbname')
        )

        cursor = conn.cursor()

        with open('reporte_log.txt', 'a', encoding='utf-8') as log:
            log.write(f"[DEBUG] Conectado a DB: {db_config.get('dbname')}@{db_config.get('host')}:{db_config.get('port')}\n")

        sql = """
            INSERT INTO actividad
            (hora, app, titulo, duracion, categoria, subcategoria, dni, fecha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            duracion = VALUES(duracion)
        """
        cursor.executemany(sql, lista_actividades)
        conn.commit()

        with open('reporte_log.txt', 'a', encoding='utf-8') as log:
            log.write(f"[INFO] Insertadas {cursor.rowcount} nuevas actividades.\n")

        cursor.close()
        return True

    except Error as e:
        with open('reporte_log.txt', 'a', encoding='utf-8') as log:
            log.write(f"[ERROR] Error MySQL: {e}\n")
        return False
    except Exception as e:
        with open('reporte_log.txt', 'a', encoding='utf-8') as log:
            log.write(f"[ERROR] Error inesperado: {e}\n")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

