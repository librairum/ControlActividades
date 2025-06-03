import os
import json
import re
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta

# Ruta dinámica al settings.json de ActivityWatch
# --------------------------------------------------
def abrir_filtro_actividades(dni_usuario):
    SETTINGS_PATH = os.path.join(
        os.path.expanduser("~"),
        "AppData", "Local", "activitywatch", "activitywatch", "aw-server", "settings.json"
    )

    # Leer la sección "classes" del JSON de configuración
    # --------------------------------------------------
    def cargar_reglas_desde_json(ruta_json):
        """
        Abre el JSON en ruta_json y retorna la lista de clases (categories).
        Si no existe el archivo, devuelve lista vacía.
        """
        if not os.path.exists(ruta_json):
            print(f"No se encontró settings.json en: {ruta_json}")
            return []
        with open(ruta_json, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        # En el settings oficial, la sección de categorías se llama "classes"
        return cfg.get("classes", [])

    # Compilar tanto las regex explícitas como el fallback "none"
    # --------------------------------------------------
    def compilar_reglas(classes_json):
        """
        De cada entrada en classes_json extrae:
        - name (lista de strings, e.g., ["Productiva", "Programación"])
        - rule.regex como patrón
        Además, al final se añade una regla ".*" para todos los type="none".
        Devuelve lista de tuplas (lista_nombres, Pattern_compilado).
        """
        reglas = []
        # Primero: todas las reglas de tipo "regex"
        for clase in classes_json:
            rule = clase.get("rule", {})
            if rule.get("type") == "regex" and "regex" in rule:
                nombres = clase["name"] # Esto ya es una lista, e.g., ["Productiva", "IA"]
                pattern = re.compile(rule["regex"], re.IGNORECASE)
                reglas.append((nombres, pattern))
        # Luego: todas las reglas de tipo "none" como catch-all
        for clase in classes_json:
            rule = clase.get("rule", {})
            if rule.get("type") == "none":
                nombres = clase["name"]
                patronesito = re.compile(".*", re.IGNORECASE)
                reglas.append((nombres, patronesito))
        return reglas

    # Detectar automáticamente el bucket de ventana
    # --------------------------------------------------
    def obtener_bucket_window():
        """
        Consulta /api/0/buckets y devuelve el primer bucket que empiece
        con "aw-watcher-window_" o None si falla.
        """
        try:
            resp = requests.get("http://localhost:5600/api/0/buckets")
            resp.raise_for_status()
            for b in resp.json():
                if b.startswith("aw-watcher-window_"):
                    return b
        except Exception:
            pass
        return None

    # Construir URL de consulta de eventos
    # --------------------------------------------------
    def construir_url(bucket, inicio_utc, fin_utc):
        """
        Forma la URL:
        GET /api/0/buckets/{bucket}/events?start=...Z&end=...Z
        """
        return (
            f"http://localhost:5600/api/0/buckets/{bucket}/events"
            f"?start={inicio_utc.isoformat()}Z&end={fin_utc.isoformat()}Z"
        )

    # Pedir al servidor los eventos
    # --------------------------------------------------
    def obtener_eventos(url):
        """
        Realiza la petición GET y devuelve la lista JSON de eventos
        o lista vacía si hay un error.
        """
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []

    # Clasificar un único evento según las reglas compiladas
    # --------------------------------------------------
    def clasificar_evento(ev, reglas):
        """
        Toma el campo ev['data']['app'] + ev['data']['title'], los
        concatena, pasa a minúsculas y prueba cada regex en orden.
        Devuelve la categoría más específica (main y subcategoría) cuyo patrón matchee.
        Si no encuentra nada, devuelve ("Sin clasificar", "").
        """
        texto = (ev['data'].get('app', '') + ' ' + ev['data'].get('title', '')).lower()

        # Inicializa con valores predeterminados
        mejor_categoria_principal = "Sin clasificar"
        mejor_subcategoria = "" # Cadena vacía si no hay subcategoría

        # Usaremos la longitud del array 'name' en settings.json para determinar la especificidad.
        # Por ejemplo, ["PRODUCTIVO", "IA"] tiene longitud 2 (más específico)
        # ["PRODUCTIVO"] tiene longitud 1 (menos específico)
        max_especificidad_encontrada = 0

        # Iterar sobre TODAS las reglas para encontrar la más específica
        # El orden de las reglas en settings.json es importante para el desempate
        # si múltiples reglas tienen la misma especificidad.
        for nombres_de_categoria, patron in reglas:
            if patron.search(texto):
                especificidad_actual = len(nombres_de_categoria)

                # Si encontramos una regla más específica, la seleccionamos.
                # O si es la primera coincidencia.
                if especificidad_actual > max_especificidad_encontrada:
                    mejor_categoria_principal = nombres_de_categoria[0]
                    # Si la especificidad es > 1, significa que hay una subcategoría (nombres_de_categoria[1])
                    mejor_subcategoria = nombres_de_categoria[1] if especificidad_actual > 1 else ""
                    max_especificidad_encontrada = especificidad_actual
                # Si se encuentra una regla con la misma especificidad (e.g. ambas tienen subcategoría)
                # no hacemos nada, ya que la primera encontrada (por el orden de `reglas`) ya se seleccionó.

        return mejor_categoria_principal, mejor_subcategoria

    # Conversión local <-> UTC (UTC−5 para Perú)
    # --------------------------------------------------
    def local_a_utc(dt_local):
        """Suma 5h a la hora local para obtener UTC."""
        return dt_local + timedelta(hours=5)

    def utc_a_local(dt_utc):
        """Resta 5h a UTC para mostrar en local."""
        return dt_utc - timedelta(hours=5)

    # Función principal: leer UI, convertir horas, filtrar, clasificar y poblar tabla
    # --------------------------------------------------
    def generar_reporte():
        # 9.1) Leer fecha y hora de los widgets; combinarlos en datetime
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

        # 9.2) Convertir a UTC para la consulta
        inicio_utc = local_a_utc(inicio_local)
        fin_utc    = local_a_utc(fin_local)

        # 9.3) Cargar y compilar reglas
        clases_json = cargar_reglas_desde_json(SETTINGS_PATH)
        reglas = compilar_reglas(clases_json)
        if not reglas:
            messagebox.showerror("Error", "No se encontraron reglas de categorización.")
            return

        # 9.4) Obtener el bucket de ventana
        bucket = obtener_bucket_window()
        if not bucket:
            messagebox.showerror("Error", "No se encontró bucket aw-watcher-window_.")
            return

        # 9.5) Llamar a la API y obtener eventos
        url = construir_url(bucket, inicio_utc, fin_utc)
        eventos = obtener_eventos(url)

        # 9.6) Leer filtros de duración y categoría
        dur_filtro = combo_d.get()
        cat_filtro = combo_c.get()

        # 9.7) Vaciar la tabla
        for row in tree.get_children():
            tree.delete(row)

        # 9.8) Iterar eventos, aplicar filtros y clasificar
        for ev in eventos:
            dur = ev.get('duration', 0) or 0
            mins = dur / 60.0
            # filtro de duración
            if dur_filtro=="2+ min" and mins<2: continue
            if dur_filtro=="5+ min" and mins<5: continue
            if dur_filtro=="10+ min" and mins<10: continue

            # CLASIFICACIÓN: AHORA RECIBE UNA TUPLA (CATEGORIA_PRINCIPAL, SUBCATEGORIA)
            categoria_principal, subcategoria = clasificar_evento(ev, reglas)

            # Filtro de categoría: ahora debe revisar la categoría principal
            if cat_filtro!="Todas" and categoria_principal!=cat_filtro:
                continue

            # timestamp UTC → datetime → hora local mostrada
            ts_utc = datetime.fromisoformat(ev["timestamp"].replace("Z","+00:00"))
            ts_loc = utc_a_local(ts_utc).strftime("%H:%M:%S")

            # INSERTAR EN TABLA: AHORA CON UNA COLUMNA ADICIONAL PARA LA SUBCATEGORÍA
            tree.insert("", "end", values=(
                ts_loc,
                ev['data'].get('app',''),
                ev['data'].get('title',''),
                f"{dur:.2f}",
                categoria_principal,  # Categoría principal
                subcategoria          # Subcategoría
            ))

    # ===== INICIO DE LA CONSTRUCCIÓN DE LA INTERFAZ =====
    # --------------------------------------------------
    # Cargar las categorías principales de settings.json para el ComboBox de filtro
    # Esto se hace una vez al inicio.
    try:
        clases_para_filtro_inicial = cargar_reglas_desde_json(SETTINGS_PATH)
        categorias_principales_unicas = set()
        for clase in clases_para_filtro_inicial:
            if "name" in clase and len(clase["name"]) > 0:
                categorias_principales_unicas.add(clase["name"][0])

        # Convertir el set a una lista y ordenarla alfabéticamente
        lista_categorias_para_filtro = sorted(list(categorias_principales_unicas))
        # Añadir "Todas" al principio de la lista
        lista_categorias_para_filtro.insert(0, "Todas")
    except Exception as e:
        # En caso de error al cargar settings.json al inicio, usa una lista por defecto
        print(f"Error al cargar categorías para filtro: {e}")
        lista_categorias_para_filtro = ["Todas", "PRODUCTIVO", "NO PRODUCTIVO", "APP DE COMUNICACION", "Uncategorized", "Sin clasificar"]

    root = tk.Toplevel()
    root.title("Filtro de Actividades - ActivityWatch")

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
    print()

    tk.Label(root, text="Categoría:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
    combo_c = ttk.Combobox(root,
                            # AHORA LOS VALORES SE CARGAN DINÁMICAMENTE DESDE settings.json
                            values=lista_categorias_para_filtro,
                            state="readonly", width=20)
    combo_c.grid(row=3, column=1, columnspan=2, sticky="w", pady=2)
    combo_c.current(0) # Esto establecerá "Todas" por defecto si es el primer elemento

    # — Botón Generar —
    btn = ttk.Button(root, text="Generar Reporte", command=generar_reporte)
    btn.grid(row=4, column=0, columnspan=3, pady=8)
    # campo del dni ingresado
    tk.Label(root, text="DNI:").grid(row=4, column=1, padx=5, pady=2, sticky="e")
    entry = tk.Entry(root)
    entry.insert(0,dni_usuario)
    entry.config(state="readonly")
    entry.grid(row=4, column=2, columnspan=2, padx=5, pady=2, sticky="w")

    # — Tabla de resultados —
    cols = ("Hora","App","Título","Duración","Categoría","Subcategoría")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=15)
    for c in cols:
        tree.heading(c, text=c)
    tree.column("Hora",      width=80,   anchor="center")
    tree.column("App",       width=170, anchor="w")
    tree.column("Título",    width=340, anchor="w")
    tree.column("Duración",  width=85,   anchor="center")
    tree.column("Categoría", width=120, anchor="w")
    tree.column("Subcategoría", width=120, anchor="w")
    tree.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

    # Permitir que la tabla crezca con la ventana
    root.grid_rowconfigure(5, weight=1)
    root.grid_columnconfigure(2, weight=1)

    root.mainloop()
