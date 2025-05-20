import sqlite3
import os
import socket
import base64
from datetime import datetime

def extraer_capturas_desde_txt():
    ruta_txt = os.path.join(os.path.dirname(__file__), "Img_to_Binary", "capturas_base64.txt")
    with open(ruta_txt, "r", encoding="utf-8") as f:
        contenido = f.read()

    bloques = contenido.split("--- Imagen capturada en ")
    capturas = []

    for bloque in bloques[1:]:
        try:
            partes = bloque.split("---")
            timestamp_str = partes[0].strip()

            if "Imagen en binario:" in bloque:
                partes_b64 = bloque.split("Imagen en binario:")
                base64_lines = partes_b64[1].strip().splitlines()
                base64_string = base64_lines[0].strip()

                if base64_string:
                    capturas.append((timestamp_str, base64_string))
        except Exception as e:
            print(f"[WARN] Bloque mal formado: {e}")
            continue

    return capturas

def insertar_en_db(dni, nombre_equipo, fecha, hora, imagen_bytes):
    ruta_db = os.path.join(os.path.dirname(__file__), 'imagenes.db')
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO fotos (dni, nombre_equipo, fecha, hora, imagen_en_bytes)
        VALUES (?, ?, ?, ?, ?)
    """, (dni, nombre_equipo, fecha, hora, imagen_bytes))

    conn.commit()
    conn.close()
    print(f"[DB] Inserción exitosa para {fecha} {hora}")

def insertar_desde_txt(dni):
    try:
        capturas = extraer_capturas_desde_txt()
        print(f"[INFO] Total de capturas encontradas: {len(capturas)}")

        nombre_equipo = socket.gethostname()

        for timestamp_str, base64_str in capturas:
            try:
                fecha_obj = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                fecha_formato = fecha_obj.strftime("%d/%m/%y")
                hora_formato = fecha_obj.strftime("%H:%M:%S")
                imagen_bytes = base64.b64decode(base64_str)

                insertar_en_db(dni, nombre_equipo, fecha_formato, hora_formato, imagen_bytes)
            except Exception as e:
                print(f"[ERROR] Error al insertar captura con timestamp {timestamp_str}: {e}")

    except Exception as e:
        print(f"[ERROR] {e}")
