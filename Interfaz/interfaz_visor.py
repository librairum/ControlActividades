import os, sys, time, base64, socket, threading, sqlite3
import winreg
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import psutil, mss

from Interfaz.conf_avanz import mostrar_configuracion_avanzada
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from activity import main2

# === FUNCIONES AUXILIARES ===
dni_guardado = None
def leer_horas_programadas():
    """
    Lee las horas programadas desde 'captura/hora_programada/hora_cap.txt'
    y retorna una lista de horas en formato HH:MM.
    """
    horas = []
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        ruta_txt = os.path.join(base_dir, "captura", "hora_programada", "hora_cap.txt")

        with open(ruta_txt, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if not linea:
                    continue
                # Extraer la hora (lo que está después de ": ")
                if ": " in linea:
                    _, hora = linea.split(": ", 1)
                    if len(hora) == 5 and hora[2] == ":":
                        horas.append(hora)
    except FileNotFoundError:
        messagebox.showerror("Error", "No se encontró el archivo hora_cap.txt.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al leer horas programadas: {e}")
    return horas

def agregar_a_inicio():
    clave = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Run",
                           0, winreg.KEY_SET_VALUE)
    ruta_ejecutable = os.path.realpath(sys.argv[0])
    winreg.SetValueEx(clave, "VisorActividad", 0, winreg.REG_SZ, ruta_ejecutable)
    winreg.CloseKey(clave)

def eliminar_de_inicio():
    try:
        clave = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Run",
                               0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(clave, "VisorActividad")
        winreg.CloseKey(clave)
    except FileNotFoundError:
        pass

def esta_activitywatch_activo():
    return any(p.info['name'] in ['aw-server', 'aw-server.exe', 'aw-watcher-window', 'aw-watcher-window.exe']
               for p in psutil.process_iter(['name']))

def verificar_activitywatch():
    if esta_activitywatch_activo():
        crear_interfaz()
    else:
        ventana_error = tk.Tk()
        ventana_error.withdraw()  # Oculta la ventana principal

        respuesta = messagebox.askretrycancel(
            "Error", 
            "ActivityWatch no está en ejecución.\n¿Desea reintentar?"
        )
        ventana_error.destroy()

        if respuesta:
            verificar_activitywatch()
        else:
            sys.exit()

def obtener_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    caps_dir = os.path.join(base_dir, "captura", "Screen_Caps")
    bin_dir = os.path.join(base_dir, "captura", "Img_to_Binary")
    db_path = os.path.join(base_dir, "captura", "imagenes.db")
    os.makedirs(caps_dir, exist_ok=True)
    os.makedirs(bin_dir, exist_ok=True)
    return caps_dir, bin_dir, db_path

def tomar_captura_y_guardar(caps_dir):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(caps_dir, f"captura_{timestamp}.jpg")
    with mss.mss() as sct:
        sct.shot(output=path)
    print(f"[Captura] Imagen guardada: {path}")
    return path, timestamp

def convertir_a_base64(path):
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode("utf-8")

def guardar_en_txt(bin_dir, contenido, timestamp):
    with open(os.path.join(bin_dir, "capturas_base64.txt"), "a", encoding="utf-8") as f:
        f.write(f"\n\n--- Imagen capturada en {timestamp} ---\nImagen en binario:\n\n{contenido}")
    print("[TXT] Base64 guardado.")

def esperar_hora(hora_objetivo):
    print(f"[Captura] Esperando hasta las {hora_objetivo}...")
    while datetime.now().strftime("%H:%M") != hora_objetivo:
        time.sleep(1)
    print("[Captura] ¡Hora alcanzada!")

# === INTERFAZ GRÁFICA ===
def crear_interfaz():
    root = tk.Tk()
    root.title("VisorActividad")
    root.resizable(False, False)

    def detener_programa():
        root.destroy()
        sys.exit()
    
    def toggle_inicio():
        if var_inicio.get():
            agregar_a_inicio()
            messagebox.showinfo("Inicio automático", "La app se ejecutará al iniciar Windows.")
        else:
            eliminar_de_inicio()
            messagebox.showinfo("Inicio automático", "La app ya no se ejecutará al iniciar Windows.")


    # Dimensiones y centrado
    ancho_ventana, alto_ventana = 500, 250
    x = (root.winfo_screenwidth() // 2) - (ancho_ventana // 2)
    y = (root.winfo_screenheight() // 2) - (alto_ventana // 2)
    root.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")

    frame = tk.Frame(root, bd=2, relief="solid", padx=10, pady=10)
    frame.pack(padx=20, pady=20, fill='both', expand=True)

    # Variable para el checkbutton de inicio automático
    var_inicio = tk.BooleanVar()

    # Verificar si ya está en el inicio automático
    try:
        clave = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run")
        valor_actual, _ = winreg.QueryValueEx(clave, "VisorActividad")
        if os.path.realpath(sys.argv[0]) == valor_actual:
            var_inicio.set(True)
        winreg.CloseKey(clave)
    except FileNotFoundError:
        var_inicio.set(False)

    fila_titulo = tk.Frame(frame, bg="lightblue")
    fila_titulo.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))

    titulo = tk.Label(fila_titulo, text="VisorActividad", font=("Arial", 14, "bold"), bg="lightblue")
    titulo.pack(fill="both", expand=True)

    for col in range(3): frame.columnconfigure(col, weight=1)

    # Entrada DNI
    tk.Label(frame, text="Coloque su DNI:").grid(row=4, column=0, padx=5, pady=10, sticky="e")
    entry = tk.Entry(frame)
    entry.grid(row=4, column=1, padx=5, pady=10, sticky="ew")

    # Función principal
    def iniciar_programa():
        global dni_guardado
        dni = entry.get().strip()
        if not dni:
            messagebox.showwarning("Campo vacío", "Por favor, ingrese su número de DNI.")
            return
        else:
            dni_guardado=dni
            messagebox.showinfo("DNI","DNI guardado correctamente")

        horas = leer_horas_programadas()
        caps_dir, bin_dir, db_path = obtener_paths()

        def tarea():
            capturas = []
            for hora in horas:
                esperar_hora(hora)
                path, timestamp = tomar_captura_y_guardar(caps_dir)
                b64 = convertir_a_base64(path)
                guardar_en_txt(bin_dir, b64, timestamp)

                fecha_raw, hora_raw = timestamp.split("_")
                fecha = datetime.strptime(fecha_raw, "%Y%m%d").strftime("%d/%m/%y")
                hora_actual = datetime.strptime(hora_raw, "%H%M%S").strftime("%H:%M:%S")
                nombre_pc = socket.gethostname()
                imagen_bytes = base64.b64decode(b64)
                capturas.append((dni, nombre_pc, fecha, hora_actual, imagen_bytes))

            with sqlite3.connect(db_path) as conn:
                conn.executemany(
                    "INSERT INTO fotos (dni, nombre_equipo, fecha, hora, imagen_en_bytes) VALUES (?, ?, ?, ?, ?)",
                    capturas)
            messagebox.showinfo("Captura","capturas guardadas correctamente.")

        threading.Thread(target=tarea).start()

    # Botones
    tk.Button(frame, text="Iniciar Programa", command=iniciar_programa)\
        .grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    tk.Button(frame, text="Detener Programa", command=detener_programa)\
        .grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    tk.Button(frame, text="Programa horario")\
        .grid(row=2, column=0, padx=5, pady=5, sticky="ew")
    tk.Button(frame, text="Configuracion Avanzada", command=mostrar_configuracion_avanzada)\
        .grid(row=2, column=1, padx=5, pady=5, sticky="ew")
    def abrir_filtro_si_hay_dni():
        if not dni_guardado:
            messagebox.showwarning("Advertencia", "Primero debe ingresar y guardar su DNI.")
            return
        main2.abrir_filtro_actividades(dni_guardado)
    tk.Button(frame, text="Filtro de Actividades", command=abrir_filtro_si_hay_dni)\
        .grid(row=3, column=0, padx=5, pady=5, sticky="ew")
    #Inicio automático
    tk.Checkbutton(frame, text="Ejecutar al iniciar Windows",
               variable=var_inicio, command=toggle_inicio)\
    .grid(row=3, column=1, columnspan=2, padx=5, pady=10, sticky="w")

    root.mainloop()

# === EJECUCIÓN PRINCIPAL ===
if __name__ == "__main__":
    verificar_activitywatch()
