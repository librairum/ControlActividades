import os
import time
from datetime import datetime
import mss
import base64
import psutil
import tkinter as tk
import insertar_db
from tkinter import messagebox

def obtener_dni():
    dni_capturado = []

    def on_submit():
        dni = entry.get().strip()
        if not dni:
            messagebox.showwarning("Campo vacío", "Por favor, ingrese su número de DNI...")
        else:
            dni_capturado.append(dni)
            root.destroy()

    def on_closing():
        messagebox.showwarning("DNI requerido", "Por favor, ingrese su número de DNI...")

    root = tk.Tk()
    root.title("Ingreso de DNI")

    tk.Label(root, text="Coloque su DNI:").grid(
        row=0, column=0, padx=10, pady=10)
    entry = tk.Entry(root)
    entry.grid(row=0, column=1, padx=10, pady=10)
    tk.Button(root, text="Ingresar", command=on_submit).grid(
        row=1, columnspan=2, pady=10)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

    return dni_capturado[0] if dni_capturado else None

def esta_activitywatch_activo():
    procesos_a_verificar = ['aw-server', 'aw-server.exe',
                            'aw-watcher-window', 'aw-watcher-window.exe']
    for p in psutil.process_iter(['name']):
        if p.info['name'] in procesos_a_verificar:
            return True
    return False

def obtener_ruta_guardado():
    carpeta = os.path.join(os.path.dirname(__file__), "Screen_Caps")
    os.makedirs(carpeta, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo = f"captura_{timestamp}.jpg"
    return os.path.join(carpeta, nombre_archivo), timestamp

def tomar_captura(ruta_archivo):
    with mss.mss() as sct:
        sct.shot(output=ruta_archivo)
    print(f"[Captura] Imagen guardada en: {ruta_archivo}")

def convertir_a_base64(ruta_imagen):
    with open(ruta_imagen, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string

def guardar_en_txt_append(base64_string, timestamp):
    carpeta_txt = os.path.join(os.path.dirname(__file__), "Img_to_Binary")
    os.makedirs(carpeta_txt, exist_ok=True)
    ruta_txt = os.path.join(carpeta_txt, "capturas_base64.txt")

    with open(ruta_txt, "a", encoding="utf-8") as txt_file:
        txt_file.write(f"\n\n--- Imagen capturada en {timestamp} ---\n")
        txt_file.write("Imagen en binario:\n\n")
        txt_file.write(base64_string)
    print(f"[TXT] Base64 agregado a: {ruta_txt}")

def esperar_hora_programada(hora_objetivo):
    print(f"[Captura] Esperando hasta las {hora_objetivo}...")
    while True:
        ahora = datetime.now().strftime("%H:%M")
        if ahora == hora_objetivo:
            print("[Captura] ¡Hora alcanzada!")
            return
        time.sleep(1)

def ejecutar_captura_programada():
    hora_objetivo = "09:36"  # Cambia esta hora según lo necesites
    esperar_hora_programada(hora_objetivo)
    ruta_imagen, timestamp = obtener_ruta_guardado()
    tomar_captura(ruta_imagen)
    base64_string = convertir_a_base64(ruta_imagen)
    guardar_en_txt_append(base64_string, timestamp)

if __name__ == "__main__":
    dni = obtener_dni()  # muestra la ventana y captura el DNI
    print(f"DNI capturado: {dni}")

    # Aquí continúa tu lógica normal
    if esta_activitywatch_activo():
        ejecutar_captura_programada()
        # Luego insertas en DB con el DNI capturado
        insertar_db.insertar_desde_txt(dni)
    else:
        print("[Captura] ActivityWatch no está en ejecución. Terminando script.")
