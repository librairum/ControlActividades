# Dentro de aw_utils.py
"""
aw_utils.py
-----------
Funciones auxiliares para:
- Leer reglas de settings.json
- Compilar expresiones regulares de categorización
- Detección de buckets en ActivityWatch
- Construcción de URLs para la API
- Conversión local <-> UTC
- Clasificación de eventos
- Cargar configuración de base de datos desde config.json
"""

import os
import json
import re
import requests
from datetime import timedelta, datetime # Asegúrate de que datetime también esté importado si se usa en otras funciones

# --- Función para cargar reglas (ya existente) ---
def cargar_reglas_desde_json(ruta_json):
    if not os.path.exists(ruta_json):
        print(f"No se encontró settings.json en: {ruta_json}")
        return []
    with open(ruta_json, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    return cfg.get("classes", [])

# --- Función para compilar reglas (ya existente) ---
def compilar_reglas(classes_json):
    reglas = []
    for clase in classes_json:
        rule = clase.get("rule", {})
        if rule.get("type") == "regex" and "regex" in rule:
            nombres = clase["name"]
            pattern = re.compile(rule["regex"], re.IGNORECASE)
            reglas.append((nombres, pattern))
    for clase in classes_json:
        rule = clase.get("rule", {})
        if rule.get("type") == "none":
            nombres = clase["name"]
            patronesito = re.compile(".*", re.IGNORECASE) # Un patrón que siempre coincide
            reglas.append((nombres, patronesito)) # Añadir la regla "none"
    return reglas

# --- Funciones de utilidad de ActivityWatch (ya existentes) ---
def obtener_bucket_window():
    try:
        resp = requests.get("http://localhost:5600/api/0/buckets")
        resp.raise_for_status()
        for b in resp.json():
            if b.startswith("aw-watcher-window_"):
                return b
    except Exception as e: # Captura la excepción para depuración
        print(f"Error al obtener bucket de ventana: {e}")
        pass
    return None

def construir_url(bucket, inicio_utc, fin_utc):
    return (
        f"http://localhost:5600/api/0/buckets/{bucket}/events"
        f"?start={inicio_utc.isoformat()}Z&end={fin_utc.isoformat()}Z"
    )

def obtener_eventos(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except Exception as e: # Captura la excepción para depuración
        print(f"Error al obtener eventos: {e}")
        return []

def clasificar_evento(ev, reglas):
    texto = (ev['data'].get('app', '') + ' ' + ev['data'].get('title', '')).lower()
    mejor_categoria_principal = "Sin clasificar"
    mejor_subcategoria = ""
    max_especificidad_encontrada = 0
    for nombres_de_categoria, patron in reglas:
        if patron.search(texto):
            especificidad_actual = len(nombres_de_categoria)
            if especificidad_actual > max_especificidad_encontrada:
                mejor_categoria_principal = nombres_de_categoria[0]
                mejor_subcategoria = nombres_de_categoria[1] if len(nombres_de_categoria) > 1 else ""
                max_especificidad_encontrada = especificidad_actual
    return mejor_categoria_principal, mejor_subcategoria

def local_a_utc(dt_local):
    """Convierte un objeto datetime local a UTC."""
    return dt_local.astimezone(timedelta(0)) # Esto es una simplificación, considera timezone.utc

def utc_a_local(dt_utc):
    """Convierte un objeto datetime UTC a la hora local."""
    # Esto asume que el sistema tiene una zona horaria configurada.
    # Para mayor robustez, se podría usar pytz.
    return dt_utc.astimezone()


# --- ¡NUEVA FUNCIÓN PARA CARGAR LA CONFIGURACIÓN DE LA BASE DE DATOS! ---
def load_db_config(config_file_path):
    """
    Carga la configuración de la base de datos desde un archivo JSON.

    Args:
        config_file_path (str): La ruta completa al archivo de configuración JSON (config.json).

    Returns:
        dict: Un diccionario que contiene la configuración de la base de datos (host, port, user, password, dbname).
              Retorna None si el archivo no se encuentra o hay un error de formato.
    """
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('database') # Retorna solo la sección 'database'
    except FileNotFoundError:
        print(f"Error: El archivo de configuración '{config_file_path}' no se encontró.")
        return None
    except json.JSONDecodeError:
        print(f"Error: El archivo de configuración '{config_file_path}' no tiene un formato JSON válido.")
        return None
    except Exception as e:
        print(f"Ocurrió un error inesperado al cargar la configuración de la base de datos: {e}")
        return None