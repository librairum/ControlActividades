import tkinter as tk
from tkinter import ttk

# Días de la semana
dias = ["Lunes", "Martes", "Miercoles", "Juves", "Sabado", "Domingo"]

# Crear ventana principal
ventana = tk.Tk()
ventana.title("Programa horario")

# Título principal
titulo = ttk.Label(ventana, text="Programa horario", font=("Arial", 12, "bold"))
titulo.grid(row=0, column=0, columnspan=3, pady=5)

# Encabezados
ttk.Label(ventana, text="").grid(row=1, column=0)
ttk.Label(ventana, text="hora inicio", font=("Arial", 10, "bold")).grid(row=1, column=1, padx=10)
ttk.Label(ventana, text="hora fin", font=("Arial", 10, "bold")).grid(row=1, column=2, padx=10)

# Diccionarios para almacenar entradas
entradas_inicio = {}
entradas_fin = {}

# Entradas por cada día
for i, dia in enumerate(dias):
    ttk.Label(ventana, text=dia).grid(row=i+2, column=0, padx=10, pady=2)
    
    entrada_inicio = ttk.Entry(ventana, width=10)
    entrada_inicio.insert(0, "8:00")
    entrada_inicio.grid(row=i+2, column=1)
    entradas_inicio[dia] = entrada_inicio

    entrada_fin = ttk.Entry(ventana, width=10)
    entrada_fin.insert(0, "17:00")
    entrada_fin.grid(row=i+2, column=2)
    entradas_fin[dia] = entrada_fin

# Botones
boton_guardar = ttk.Button(ventana, text="Guardar")
boton_guardar.grid(row=len(dias)+2, column=0, pady=10)

boton_cancelar = ttk.Button(ventana, text="cancelar")
boton_cancelar.grid(row=len(dias)+2, column=1, columnspan=2)

# Ejecutar ventana
ventana.mainloop()
