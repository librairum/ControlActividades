import requests
import socket
from datetime import datetime

def obtener_nombre_equipo_por_defecto():
    try:
        return socket.gethostname()
    except socket.error:
        return "equipo_desconocido"

def obtener_nombre_bucket_ventana():
    try:
        response = requests.get("http://localhost:5600/api/0/buckets")
        response.raise_for_status()
        buckets_data = response.json()
        for bucket_id, bucket_info in buckets_data.items():
            if bucket_id.startswith("aw-watcher-window_"):
                return bucket_id
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con ActivityWatch API: {e}")
        return None

def construir_url_eventos(nombre_bucket, fecha_inicio, fecha_fin):
    start_iso = fecha_inicio.isoformat() + "Z"
    end_iso = fecha_fin.isoformat() + "Z"
    return f"http://localhost:5600/api/0/buckets/{nombre_bucket}/events?start={start_iso}&end={end_iso}"

def obtener_eventos(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener eventos: {e}")
        return None

# ✅ Clasificador por categoría
def clasificar_evento(evento):
    app = evento['data'].get('app', '').lower()
    title = evento['data'].get('title', '').lower()

    productivas = ['code.exe', 'devenv.exe', 'notepad++.exe', 'excel.exe', 'word.exe', 'chrome.exe']
    comunicacion = ['whatsapp', 'teams', 'zoom', 'gmail', 'outlook']
    no_productivas = ['netflix', 'spotify', 'youtube']

    if any(p in app or p in title for p in comunicacion):
        return "Comunicación"
    if any(p in app or p in title for p in no_productivas):
        return "No productiva"
    if any(p in app for p in productivas) or 'chatgpt' in title or 'docs.google' in title:
        return "Productiva"
    return "No clasificada"

def mostrar_reporte_diario(eventos):
    if not eventos:
        print("No se encontraron eventos para el rango de fechas especificado.")
        return

    eventos_por_dia = {}
    for evento in eventos:
        try:
            timestamp_str = evento['timestamp']
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            fecha = timestamp.strftime("%Y-%m-%d")
            if fecha not in eventos_por_dia:
                eventos_por_dia[fecha] = []
            eventos_por_dia[fecha].append(evento)
        except ValueError as e:
            print(f"Error al procesar timestamp: {timestamp_str}. Error: {e}")
            continue

    for fecha, eventos_del_dia in eventos_por_dia.items():
        print(f"\n--- Reporte del día: {fecha} ---")
        for evento in eventos_del_dia:
            duracion = evento.get('duration', 0)
            if duracion is None or duracion < 120:
                continue  # Solo eventos >= 2 minutos

            timestamp_str = evento.get('timestamp', 'Timestamp no encontrado')
            try:
                hora = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).strftime('%H:%M:%S')
            except ValueError:
                hora = "Hora no válida"

            app = evento['data'].get('app', 'App desconocida')
            title = evento['data'].get('title', 'Sin título')
            categoria = clasificar_evento(evento)

            print(f"  - Hora: {hora}, Duración: {duracion:.2f} segundos")
            print(f"    App: {app}")
            print(f"    Título: {title}")
            print(f"    Categoría: {categoria}")

if __name__ == "__main__":
    nombre_bucket_final = obtener_nombre_bucket_ventana()

    if not nombre_bucket_final:
        print("No se pudo encontrar automáticamente el nombre del bucket del watcher de ventana.")
        nombre_equipo_defecto = obtener_nombre_equipo_por_defecto()
        print(f"Considera usar un nombre de bucket como 'aw-watcher-window_{nombre_equipo_defecto}'.")
        exit()

    try:
        fecha_inicio_str = input("Introduce la fecha y hora de inicio (YYYY-MM-DD HH:MM): ")
        fecha_fin_str = input("Introduce la fecha y hora de fin (YYYY-MM-DD HH:MM): ")
        fecha_inicio_reporte = datetime.strptime(fecha_inicio_str, "%Y-%m-%d %H:%M")
        fecha_fin_reporte = datetime.strptime(fecha_fin_str, "%Y-%m-%d %H:%M")

        if fecha_inicio_reporte > fecha_fin_reporte:
            print("Error: La fecha de inicio debe ser anterior a la fecha de fin.")
            exit()

    except ValueError:
        print("Error: Formato de fecha y hora incorrecto. Usa YYYY-MM-DD HH:MM.")
        exit()

    url_reporte = construir_url_eventos(nombre_bucket_final, fecha_inicio_reporte, fecha_fin_reporte)
    eventos_reporte = obtener_eventos(url_reporte)

    if eventos_reporte:
        mostrar_reporte_diario(eventos_reporte)
    else:
        print("No se pudieron obtener los eventos del bucket.")
