import tkinter as tk

def crear_interfaz():
    root = tk.Tk()
    root.title("VisorActividad")
    root.geometry("400x200")
    root.resizable(False, False)

    # Marco principal con borde
    frame = tk.Frame(root, bd=2, relief="solid", padx=10, pady=10)
    frame.pack(padx=20, pady=20)

    # Fila de título con fondo celeste
    fila_titulo = tk.Frame(frame, bg="lightblue")
    fila_titulo.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

    titulo = tk.Label(fila_titulo, text="VisorActividad", font=("Arial", 14, "bold"), bg="lightblue")
    titulo.pack(fill="both", expand=True)

    # Botones distribuidos
    btn_iniciar = tk.Button(frame, text="Iniciar Programa", width=20)
    btn_iniciar.grid(row=1, column=0, padx=5, pady=5)

    btn_detener = tk.Button(frame, text="Detener Programa", width=20)
    btn_detener.grid(row=1, column=1, padx=5, pady=5)

    btn_horario = tk.Button(frame, text="Programa horario", width=20)
    btn_horario.grid(row=2, column=0, padx=5, pady=5)

    btn_config = tk.Button(frame, text="Configuracion Avanzada", width=20)
    btn_config.grid(row=2, column=1, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    crear_interfaz()
