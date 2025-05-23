import tkinter as tk
from tkinter import ttk
import os

# Estructura para almacenar la programación
programacion = {
    'Lunes': ['', ''],
    'Martes': ['', ''],
    'Miercoles': ['', ''],
    'Jueves': ['', ''],
    'Viernes': ['', ''],
    'Sabado': ['', ''],
    'Domingo': ['', '']
}

def obtener_horas_desde_txt():
    """
    Lee las dos horas desde el archivo hora_cap.txt y las devuelve como una tupla (hora1, hora2).
    """
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        ruta_txt = os.path.join(base_dir, "captura", "hora_programada", "hora_cap.txt")
        with open(ruta_txt, "r", encoding="utf-8") as f:
            lineas = [line.strip() for line in f.readlines() if line.strip()]
            horas = []
            for linea in lineas:
                if ": " in linea:
                    _, hora = linea.split(": ", 1)
                    horas.append(hora.strip())
            # Rellenar si falta alguna
            while len(horas) < 2:
                horas.append("")
            return horas[0], horas[1]
    except:
        return "", ""

def mostrar_configuracion_avanzada():
    hora1_txt, hora2_txt = obtener_horas_desde_txt()
    dias = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    
    ventana = tk.Toplevel()
    ventana.title("Configuración Avanzada")
    ventana.geometry("950x450")

    # Parte superior
    tk.Label(ventana, text="Captura de pantalla", font=("Arial", 14)).grid(row=0, column=0, columnspan=5, pady=10)

    tk.Button(ventana, text="Nuevo", width=10).grid(row=1, column=0, padx=5)
    tk.Button(ventana, text="Modificar", width=10).grid(row=1, column=1, padx=5)

    # Día y horas
    tk.Label(ventana, text="Día").grid(row=2, column=0, sticky='e', pady=10)
    combo_dia = ttk.Combobox(ventana, values=dias, state="readonly")
    combo_dia.set("Lunes")
    combo_dia.grid(row=2, column=1, pady=10)

    tk.Label(ventana, text="Hora 1era Captura").grid(row=3, column=0, sticky='e')
    entry_hora1 = tk.Entry(ventana)
    entry_hora1.insert(0, hora1_txt)
    entry_hora1.grid(row=3, column=1)

    tk.Label(ventana, text="Hora 2da Captura").grid(row=4, column=0, sticky='e')
    entry_hora2 = tk.Entry(ventana)
    entry_hora2.insert(0, hora2_txt)
    entry_hora2.grid(row=4, column=1)

    # Tabla
    columns = ['Item', 'Toma Imagen'] + dias
    tree = ttk.Treeview(ventana, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor='center')

    tree.grid(row=6, column=0, columnspan=7, pady=10)

    def guardar_programacion():
        dia = combo_dia.get()
        hora1 = entry_hora1.get()
        hora2 = entry_hora2.get()
        programacion[dia] = [hora1, hora2]

    def ver_programacion():
        for item in tree.get_children():
            tree.delete(item)

        for i, captura in enumerate(["hora 1era captura", "hora 2da captura"], start=1):
            valores = [i, captura]
            for dia in dias:
                hora = programacion[dia][0] if i == 1 else programacion[dia][1]
                valores.append(hora)
            tree.insert('', 'end', values=valores)

    tk.Button(
        ventana,
        text="Ver programación",
        command=lambda: [guardar_programacion(), ver_programacion()],
        width=15
    ).grid(row=5, column=0, columnspan=2, pady=10)
