import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime

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
from activity.conexion_mysql import insertar_actividades

dni_usuario = '77475987'
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def guardar_intervalo_config(intervalo):
    """Guarda el intervalo seleccionado en config.json"""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump({"intervalo_min": intervalo}, f, indent=2)
    except Exception as e:
        print(f"Error guardando config.json: {e}")

def leer_intervalo_config():
    """Lee el intervalo actual de config.json"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        return int(cfg.get("intervalo_min", 10))
    except Exception:
        return 10  # Valor por defecto

def abrir_filtro_actividades(dni_usuario):
    SETTINGS_PATH = os.path.join(
        os.path.expanduser("~"),
        "AppData", "Local", "activitywatch", "activitywatch", "aw-server", "settings.json"
    )

    try:
        clases_para_filtro_inicial = cargar_reglas_desde_json(SETTINGS_PATH)
        categorias_principales_unicas = set()
        for clase in clases_para_filtro_inicial:
            if "name" in clase and len(clase["name"]) > 0:
                categorias_principales_unicas.add(clase["name"][0])
        lista_categorias_para_filtro = sorted(list(categorias_principales_unicas))
        lista_categorias_para_filtro.insert(0, "Todas")
    except Exception as e:
        print(f"Error al cargar categorías para filtro: {e}")
        lista_categorias_para_filtro = ["Todas", "PRODUCTIVO", "NO PRODUCTIVO", "APP DE COMUNICACION", "Uncategorized", "Sin clasificar"]

    root = tk.Tk()
    root.title("Filtro de Actividades - ActivityWatch")

    # -- Intervalo de exportación (ComboBox) --
    tk.Label(root, text="Intervalo de exportación (min):").grid(row=0, column=3, padx=5, pady=2, sticky="w")
    combo_intervalo = ttk.Combobox(root, values=["2", "5", "10", "15", "30", "60"], state="readonly", width=8)
    combo_intervalo.grid(row=0, column=4, sticky="w", pady=2)
    # Carga el valor de config.json (si existe)
    intervalo_actual = str(leer_intervalo_config())
    if intervalo_actual in combo_intervalo['values']:
        combo_intervalo.set(intervalo_actual)
    else:
        combo_intervalo.current(2)  # "10" min por defecto

    def on_cambio_intervalo(event):
        try:
            intervalo = int(combo_intervalo.get())
            guardar_intervalo_config(intervalo)
        except Exception as e:
            messagebox.showerror("Error", f"Valor de intervalo inválido: {e}")

    combo_intervalo.bind("<<ComboboxSelected>>", on_cambio_intervalo)

    # También guarda el intervalo al cerrar la ventana por seguridad
    def on_closing():
        try:
            guardar_intervalo_config(int(combo_intervalo.get()))
        except:
            pass
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # — Fecha/Hora Inicio —
    tk.Label(root, text="Inicio:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
    date_i = DateEntry(root, date_pattern='yyyy-MM-dd', locale='es_ES')
    date_i.grid(row=0, column=1, pady=2, sticky="w")
    h_i = tk.Entry(root, width=5)
    h_i.insert(0, "08:00")
    h_i.grid(row=0, column=2, padx=(2,15), pady=2, sticky="w")

    # — Fecha/Hora Fin —
    tk.Label(root, text="Fin:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
    date_f = DateEntry(root, date_pattern='yyyy-MM-dd', locale='es_ES')
    date_f.grid(row=1, column=1, pady=2, sticky="w")
    h_f = tk.Entry(root, width=5)
    h_f.insert(0, "17:00")
    h_f.grid(row=1, column=2, padx=(2,15), pady=2, sticky="w")

    # — Filtros de duración y categoría —
    tk.Label(root, text="Duración:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
    combo_d = ttk.Combobox(root, values=["2+ min","5+ min","10+ min"], state="readonly", width=10)
    combo_d.grid(row=2, column=1, columnspan=2, sticky="w", pady=2)
    combo_d.current(0)

    tk.Label(root, text="Categoría:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
    combo_c = ttk.Combobox(
        root,
        values=lista_categorias_para_filtro,
        state="readonly", width=20)
    combo_c.grid(row=3, column=1, columnspan=2, sticky="w", pady=2)
    combo_c.current(0)

    # — Botón Generar —
    btn = ttk.Button(root, text="Generar Reporte", command=lambda: generar_reporte(
        date_i, h_i, date_f, h_f, combo_d, combo_c, tree, dni_usuario, SETTINGS_PATH
    ))
    btn.grid(row=4, column=0, columnspan=3, pady=8)
    # campo del dni ingresado
    tk.Label(root, text="DNI:").grid(row=4, column=1, padx=5, pady=2, sticky="e")
    entry = tk.Entry(root)
    entry.insert(0, dni_usuario)
    entry.config(state="readonly")
    entry.grid(row=4, column=2, columnspan=2, padx=5, pady=2, sticky="w")

    # — Tabla de resultados —
    cols = ("Hora","App","Título","Duración","Categoría","Subcategoría")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=15)
    for c in cols:
        tree.heading(c, text=c)
    tree.column("Hora",      width=80,   anchor="center")
    tree.column("App",       width=170,  anchor="w")
    tree.column("Título",    width=340,  anchor="w")
    tree.column("Duración",  width=85,   anchor="center")
    tree.column("Categoría", width=120,  anchor="w")
    tree.column("Subcategoría", width=120, anchor="w")
    tree.grid(row=5, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)

    # Permitir que la tabla crezca con la ventana
    root.grid_rowconfigure(5, weight=1)
    root.grid_columnconfigure(2, weight=1)

    root.mainloop()

def generar_reporte(date_i, h_i, date_f, h_f, combo_d, combo_c, tree, dni_usuario, SETTINGS_PATH):
    try:
        inicio_local = datetime.combine(
            date_i.get_date(),
            datetime.strptime(h_i.get(), "%H:%M").time()
        )
        fin_local = datetime.combine(
            date_f.get_date(),
            datetime.strptime(h_f.get(), "%H:%M").time()
        )
        if inicio_local > fin_local:
            messagebox.showwarning("Error de fechas", "La fecha/hora de inicio debe ser menor que la de fin.")
            return
    except Exception:
        messagebox.showwarning("Formato incorrecto", "Introduce la hora en formato HH:MM.")
        return

    inicio_utc = local_a_utc(inicio_local)
    fin_utc    = local_a_utc(fin_local)

    clases_json = cargar_reglas_desde_json(SETTINGS_PATH)
    reglas = compilar_reglas(clases_json)
    if not reglas:
        messagebox.showerror("Error", "No se encontraron reglas de categorización.")
        return

    bucket = obtener_bucket_window()
    if not bucket:
        messagebox.showerror("Error", "No se encontró bucket aw-watcher-window_.")
        return

    url = construir_url(bucket, inicio_utc, fin_utc)
    eventos = obtener_eventos(url)

    dur_filtro = combo_d.get()
    cat_filtro = combo_c.get()

    for row in tree.get_children():
        tree.delete(row)

    lista_a_insertar = []
    for ev in eventos:
        dur = ev.get('duration', 0) or 0
        mins = dur / 60.0
        if dur_filtro=="2+ min" and mins<2: continue
        if dur_filtro=="5+ min" and mins<5: continue
        if dur_filtro=="10+ min" and mins<10: continue

        categoria_principal, subcategoria = clasificar_evento(ev, reglas)
        if cat_filtro != "Todas" and categoria_principal != cat_filtro:
            continue

        ts_utc = datetime.fromisoformat(ev["timestamp"].replace("Z","+00:00"))
        ts_loc = utc_a_local(ts_utc).strftime("%H:%M:%S")
        fecha_local = utc_a_local(ts_utc).date()

        tupla = (
            ts_loc,
            ev['data'].get('app', ''),
            ev['data'].get('title', ''),
            float(f"{dur:.2f}"),
            categoria_principal,
            subcategoria,
            dni_usuario,
            fecha_local
        )
        lista_a_insertar.append(tupla)

        tree.insert("", "end", values=(
            ts_loc,
            ev['data'].get('app',''),
            ev['data'].get('title',''),
            f"{dur:.2f}",
            categoria_principal,
            subcategoria
        ))
    if lista_a_insertar:
        insertar_actividades(lista_a_insertar, CONFIG_PATH)

if __name__ == "__main__":
    abrir_filtro_actividades(dni_usuario)
