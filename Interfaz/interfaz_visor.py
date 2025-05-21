import tkinter as tk
import psutil
import os
import mss
import base64
import time
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from captura import insertar_db
from datetime import datetime
from conf_avanz import mostrar_configuracion_avanzada

def ejecutar_captura_programada():
    hora_objetivo = "15:56"  # Cambia esta hora según lo necesites
    esperar_hora_programada(hora_objetivo)
    ruta_imagen, timestamp = obtener_ruta_guardado()
    tomar_captura(ruta_imagen)
    base64_string = convertir_a_base64(ruta_imagen)
    guardar_en_txt_append(base64_string, timestamp)

def esta_activitywatch_activo():
    procesos_a_verificar = ['aw-server', 'aw-server.exe',
                            'aw-watcher-window', 'aw-watcher-window.exe']
    for p in psutil.process_iter(['name']):
        if p.info['name'] in procesos_a_verificar:
            return True
    return False

def obtener_ruta_guardado():
    # Subir un nivel desde Interfaz y entrar a /captura/Screen_Caps
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    carpeta = os.path.join(base_dir, "captura", "Screen_Caps")
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
    # Subir un nivel desde Interfaz y entrar a /captura/Img_to_Binary
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    carpeta_txt = os.path.join(base_dir, "captura", "Img_to_Binary")
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

def crear_interfaz():
    root = tk.Tk()
    root.title("VisorActividad")
    root.resizable(False, False)

    # Dimensiones deseadas
    ancho_ventana = 500
    alto_ventana = 250

    # Obtener dimensiones de la pantalla
    ancho_pantalla = root.winfo_screenwidth()
    alto_pantalla = root.winfo_screenheight()

    # Calcular coordenadas para centrar la ventana
    x = (ancho_pantalla // 2) - (ancho_ventana // 2)
    y = (alto_pantalla // 2) - (alto_ventana // 2)

    # Establecer la geometría de la ventana centrada
    root.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")

    # Marco principal con borde
    frame = tk.Frame(root, bd=2, relief="solid", padx=10, pady=10)
    frame.pack(padx=20, pady=20, fill='both', expand=True)

    # Fila de título con fondo celeste
    fila_titulo = tk.Frame(frame, bg="lightblue")
    fila_titulo.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))

    titulo = tk.Label(fila_titulo, text="VisorActividad", font=("Arial", 14, "bold"), bg="lightblue")
    titulo.pack(fill="both", expand=True)

    # Configurar columnas para que se expandan proporcionalmente
    for col in range(3):
        frame.columnconfigure(col, weight=1)

    # Etiqueta para mostrar mensajes
    mensaje = tk.Label(frame, text="", fg="red")
    mensaje.grid(row=4, column=0, columnspan=3)

    # Función para validar DNI
    def validar_dni():
        dni_capturado = []
        dni = entry.get().strip()
        if dni:
            if esta_activitywatch_activo():
                ejecutar_captura_programada()
                insertar_db.insertar_desde_txt(dni)
            else:
                print("[Captura] ActivityWatch no está en ejecución. Terminando script.")

        if not dni:
            mensaje.config(text="Por favor ingrese su DNI...", fg="red")
        else:
            mensaje.config(text="DNI ingresado", fg="green")
            dni_capturado.append(dni)
        return dni_capturado[0] if dni_capturado else None
            # Aquí podrías continuar con el flujo principal del programa...

    # Botones distribuidos que se expanden
    btn_iniciar = tk.Button(frame, text="Iniciar Programa", command=validar_dni)
    btn_iniciar.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    btn_detener = tk.Button(frame, text="Detener Programa")
    btn_detener.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    btn_horario = tk.Button(frame, text="Programa horario")
    btn_horario.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

    tk.Button(frame, text="Configuracion Avanzada", command=mostrar_configuracion_avanzada)\
        .grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    # Sección de DNI en tres columnas
    tk.Label(frame, text="Coloque su DNI:").grid(row=3, column=0, padx=5, pady=10, sticky="e")
    entry = tk.Entry(frame)
    entry.grid(row=3, column=1, padx=5, pady=10, sticky="ew")

    root.mainloop()

if __name__ == "__main__":
    crear_interfaz()
    if esta_activitywatch_activo():
        ejecutar_captura_programada()
    else:
        print("[Captura] ActivityWatch no está en ejecución. Terminando script.")
