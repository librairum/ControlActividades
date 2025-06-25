import os
import json
import re
import requests
from datetime import timedelta, datetime, timezone
import pytz

LOCAL_TIMEZONE = pytz.timezone('America/Lima')

def cargar_reglas_desde_json(ruta_json):
    if not os.path.exists(ruta_json):
        print(f"No se encontró settings.json en: {ruta_json}")
        return []
    with open(ruta_json, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    return cfg.get("classes", [])

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
            patronesito = re.compile(".*", re.IGNORECASE)
            reglas.append((nombres, patronesito))
    return reglas

def obtener_bucket_window():
    try:
        resp = requests.get("http://localhost:5600/api/0/buckets")
        resp.raise_for_status()
        for b in resp.json():
            if b.startswith("aw-watcher-window_"):
                return b
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con ActivityWatch al obtener bucket: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al obtener bucket de ventana: {e}")
        pass
    return None

def construir_url(bucket, inicio_utc, fin_utc):
    start_str = inicio_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = fin_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    return (
        f"http://localhost:5600/api/0/buckets/{bucket}/events"
        f"?start={start_str}&end={end_str}"
    )

def obtener_eventos(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener eventos de ActivityWatch: {e}")
        return []
    except Exception as e:
        print(f"Ocurrió un error inesperado al obtener eventos: {e}")
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

def local_a_utc(dt_local_naive):
    dt_local_aware = LOCAL_TIMEZONE.localize(dt_local_naive)
    return dt_local_aware.astimezone(timezone.utc)

def utc_a_local(dt_utc_aware):
    return dt_utc_aware.astimezone(LOCAL_TIMEZONE)

def load_db_config(config_file_path):
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('database')
    except FileNotFoundError:
        print(f"Error: El archivo de configuración '{config_file_path}' no se encontró.")
        return None
    except json.JSONDecodeError:
        print(f"Error: El archivo de configuración '{config_file_path}' no tiene un formato JSON válido.")
        return None
    except Exception as e:
        print(f"Ocurrió un error inesperado al cargar la configuración de la base de datos: {e}")
        return None
