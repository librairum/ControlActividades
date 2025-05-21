import tkinter as tk
from tkinter import ttk

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

def guardar_programacion():
    dia = combo_dia.get()
    hora1 = entry_hora1.get()
    hora2 = entry_hora2.get()
    programacion[dia] = [hora1, hora2]

def ver_programacion():
    for item in tree.get_children():
        tree.delete(item)

    for i, captura in enumerate(["hora 1era captura", "hora 2da captura"], start=1):
        valores = [captura]
        for dia in dias:
            hora = programacion[dia][0] if i == 1 else programacion[dia][1]
            valores.append(hora)
        tree.insert('', 'end', values=[i] + valores)

# Interfaz gráfica
root = tk.Tk()
root.title("Captura de pantalla")

dias = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']

# Parte superior
tk.Label(root, text="Captura de pantalla", font=("Arial", 14)).grid(row=0, column=0, columnspan=5, pady=10)

tk.Button(root, text="Nuevo", width=10).grid(row=1, column=0, padx=5)
tk.Button(root, text="Modificar", width=10).grid(row=1, column=1, padx=5)

# Sección de día y horas
tk.Label(root, text="Día").grid(row=2, column=0, sticky='e',pady=10)
combo_dia = ttk.Combobox(root, values=dias, state="readonly")
combo_dia.set("Lunes")
combo_dia.grid(row=2, column=1,pady=10)

tk.Label(root, text="Hora 1era Captura").grid(row=3, column=0, sticky='e')
entry_hora1 = tk.Entry(root)
entry_hora1.grid(row=3, column=1)

tk.Label(root, text="Hora 2da Captura").grid(row=4, column=0, sticky='e')
entry_hora2 = tk.Entry(root)
entry_hora2.grid(row=4, column=1)

tk.Button(root, text="Ver programación", command=lambda:[guardar_programacion(), ver_programacion()], width=15).grid(row=5, column=0, columnspan=2, pady=10)

# Tabla de programación
columns = ['Item', 'Toma Imagen'] + dias
tree = ttk.Treeview(root, columns=columns, show='headings')
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=100, anchor='center')

tree.grid(row=6, column=0, columnspan=7, pady=10)

root.mainloop()
