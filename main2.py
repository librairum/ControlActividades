import os
import json
import re
import socket
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkinter import ttk

# Obtener ruta dinamica del archivo settings.json según el usuario del sistema
SETTINGS_PATH = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Local", "activitywatch", "activitywatch", "aw-server", "settings.json"
)

# Cargar reglas de categorización desde settings.json exportado de ActivityWatch
def cargar_reglas_desde_json(ruta_json):
    if not os.path.exists(ruta_json):
        print(f"❌ No se encontró settings.json en: {ruta_json}")
        return []
    with open(ruta_json, 'r', encoding='utf-8') as f:
        configuracion = json.load(f)
    return configuracion.get("classes", [])

# Compilar expresiones regulares desde el JSON
def compilar_reglas(rules_json):
    reglas_compiladas = []
    for regla in rules_json:
        nombre_categoria = regla.get("name", ["Sin nombre"])[0]
        regex = regla.get("rule", {}).get("regex")
        if regex:
            pattern = re.compile(regex, re.IGNORECASE)
            reglas_compiladas.append((nombre_categoria, pattern))
    return reglas_compiladas

# Determinar el nombre del equipo
def obtener_nombre_equipo_por_defecto():
    try:
        return socket.gethostname()
    except socket.error:
        return "equipo_desconocido"

# Detectar bucket de ventana activo
def obtener_nombre_bucket_ventana():
    try:
        response = requests.get("http://localhost:5600/api/0/buckets")
        response.raise_for_status()
        buckets_data = response.json()
        for bucket_id in buckets_data:
            if bucket_id.startswith("aw-watcher-window_"):
                return bucket_id
        return None
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo conectar con ActivityWatch: {e}")
        return None

# Construir la URL de consulta de eventos
def construir_url_eventos(nombre_bucket, fecha_inicio, fecha_fin):
    return f"http://localhost:5600/api/0/buckets/{nombre_bucket}/events?start={fecha_inicio.isoformat()}Z&end={fecha_fin.isoformat()}Z"

# Consultar eventos de ActivityWatch
def obtener_eventos(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo obtener eventos: {e}")
        return []

# Clasificar eventos en base a las reglas cargadas desde settings.json
def clasificar_evento_por_reglas(evento, reglas_compiladas):
    app = evento['data'].get('app', '').lower()
    title = evento['data'].get('title', '').lower()
    texto = f"{app} {title}"
    for categoria, pattern in reglas_compiladas:
        if pattern.search(texto):
            return categoria
    return "Sin clasificar"

# Generar y mostrar el reporte
def generar_reporte():
    try:
        fi = datetime.strptime(entry_inicio.get(), "%Y-%m-%d %H:%M")
        ff = datetime.strptime(entry_fin.get(), "%Y-%m-%d %H:%M")
        if fi > ff:
            messagebox.showwarning("Fechas inválidas", "La fecha de inicio debe ser menor que la de fin.")
            return
    except:
        messagebox.showwarning("Formato incorrecto", "Usa el formato YYYY-MM-DD HH:MM")
        return

    reglas = compilar_reglas(cargar_reglas_desde_json(SETTINGS_PATH))
    if not reglas:
        messagebox.showerror("Error", "No se encontraron reglas en settings.json")
        return

    bucket = obtener_nombre_bucket_ventana()
    if not bucket:
        return

    eventos = obtener_eventos(construir_url_eventos(bucket, fi, ff))
    categoria_filtro = combo_categoria.get()
    duracion_filtro = combo_duracion.get()

    for row in tree.get_children():
        tree.delete(row)

    for evento in eventos:
        duracion = evento.get('duration', 0)
        if duracion is None:
            continue

        minutos = duracion / 60
        if duracion_filtro == "2+ min" and minutos < 2:
            continue
        if duracion_filtro == "5+ min" and minutos < 5:
            continue
        if duracion_filtro == "10+ min" and minutos < 10:
            continue

        categoria = clasificar_evento_por_reglas(evento, reglas)
        if categoria_filtro != "Todas" and categoria != categoria_filtro:
            continue

        

        hora = datetime.fromisoformat(evento["timestamp"].replace("Z", "+00:00")).strftime("%H:%M:%S")
        app = evento['data'].get("app", "")
        title = evento['data'].get("title", "")
        tree.insert("", "end", values=(hora, app, title, f"{duracion:.2f}", categoria))

        print(f"[DEBUG] App: {app} | Title: {title} → Categoría asignada: {categoria}")
        print("DEBUG ---")
        print("App:", evento['data'].get('app', ''))
        print("Título:", evento['data'].get('title', ''))
        print("Duración:", evento.get('duration', 0))
        print("Categoría detectada:", clasificar_evento_por_reglas(evento, reglas))
        print("-------------------")

# Interfaz gráfica con Tkinter
ventana = tk.Tk()
ventana.title("Filtro de Actividades - ActivityWatch")

tk.Label(ventana, text="Fecha inicio (YYYY-MM-DD HH:MM):").grid(row=0, column=0, sticky="w")
entry_inicio = tk.Entry(ventana, width=20)
entry_inicio.grid(row=0, column=1)

tk.Label(ventana, text="Fecha fin (YYYY-MM-DD HH:MM):").grid(row=1, column=0, sticky="w")
entry_fin = tk.Entry(ventana, width=20)
entry_fin.grid(row=1, column=1)

tk.Label(ventana, text="Filtrar duración:").grid(row=2, column=0, sticky="w")
combo_duracion = ttk.Combobox(ventana, values=["2+ min", "5+ min", "10+ min"], state="readonly")
combo_duracion.grid(row=2, column=1)
combo_duracion.current(0)

tk.Label(ventana, text="Filtrar categoría:").grid(row=3, column=0, sticky="w")
combo_categoria = ttk.Combobox(ventana, values=["Todas", "Productiva", "No productiva", "Comunicación", "Sin clasificar"], state="readonly")
combo_categoria.grid(row=3, column=1)
combo_categoria.current(0)

tk.Button(ventana, text="Generar Reporte", command=generar_reporte).grid(row=4, columnspan=2, pady=10)

tree = ttk.Treeview(ventana, columns=("Hora", "App", "Título", "Duración", "Categoría"), show="headings")
tree.heading("Hora", text="Hora")
tree.heading("App", text="App")
tree.heading("Título", text="Título")
tree.heading("Duración", text="Duración (seg)")
tree.heading("Categoría", text="Categoría")
tree.column("Hora", width=80)
tree.column("App", width=120)
tree.column("Título", width=250)
tree.column("Duración", width=100)
tree.column("Categoría", width=100)
tree.grid(row=5, columnspan=2)

ventana.mainloop()