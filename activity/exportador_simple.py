import os
import json
import threading
from datetime import datetime, timedelta
from activity.conexion_mysql import insertar_actividades
from activity.aw_utils import (
    cargar_reglas_desde_json,
    compilar_reglas,
    obtener_bucket_window,
    construir_url,
    obtener_eventos,
    clasificar_evento,
    local_a_utc,
    utc_a_local
)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
DURACION_MIN = 2
DNI_USUARIO = '77475987'

def leer_intervalo_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        return int(cfg.get("intervalo_min", 10))
    except Exception:
        return 10

def exportar_actividad_periodica():
    SETTINGS_PATH = os.path.join(
        os.path.expanduser("~"),
        "AppData", "Local", "activitywatch", "activitywatch", "aw-server", "settings.json"
    )
    print("Exportador automático corriendo...")

    clases_json = cargar_reglas_desde_json(SETTINGS_PATH)
    reglas = compilar_reglas(clases_json)
    bucket = obtener_bucket_window()
    if not reglas or not bucket:
        print("No se pudo iniciar la exportación automática (sin reglas o bucket).")
        return

    exportar_actividad_periodica.ciclo_count = 1

    def ciclo():
        INTERVALO_MIN = leer_intervalo_config()
        ahora = datetime.now()
        inicio_local = ahora - timedelta(minutes=INTERVALO_MIN)
        fin_local = ahora
        inicio_utc = local_a_utc(inicio_local)
        fin_utc = local_a_utc(fin_local)
        url = construir_url(bucket, inicio_utc, fin_utc)
        eventos = obtener_eventos(url)

        lista_a_insertar = []
        for ev in eventos:
            dur = ev.get('duration', 0) or 0
            mins = dur / 60.0
            if mins < DURACION_MIN:
                continue

            categoria_principal, subcategoria = clasificar_evento(ev, reglas)
            ts_utc = datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00"))
            ts_loc = utc_a_local(ts_utc).strftime("%H:%M:%S")
            fecha_local = utc_a_local(ts_utc).date()

            tupla = (
                ts_loc,
                ev['data'].get('app', ''),
                ev['data'].get('title', ''),
                float(f"{dur:.2f}"),
                categoria_principal,
                subcategoria,
                DNI_USUARIO,
                fecha_local
            )
            lista_a_insertar.append(tupla)

        subidas = ["Primera", "Segunda", "Tercera", "Cuarta", "Quinta"]
        n = exportar_actividad_periodica.ciclo_count
        if n <= len(subidas):
            print(f"{subidas[n-1]} subida al MySQL a las {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"Subida #{n} al MySQL a las {datetime.now().strftime('%H:%M:%S')}")

        exportar_actividad_periodica.ciclo_count += 1

        if lista_a_insertar:
            insertar_actividades(lista_a_insertar, CONFIG_PATH)
            print(f"Insertados {len(lista_a_insertar)} registros a MySQL.")
        else:
            print("Nada nuevo que insertar...")

        threading.Timer(INTERVALO_MIN * 60, ciclo).start()

    ciclo()

if __name__ == "__main__":
    exportar_actividad_periodica()
