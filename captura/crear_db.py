import sqlite3
import os

# Ruta de la base de datos
ruta_db = os.path.join(os.path.dirname(__file__), 'imagenes.db')

# Conexión a la base de datos
conn = sqlite3.connect(ruta_db)
cursor = conn.cursor()

# Crear la tabla 'fotos'
cursor.execute("""
CREATE TABLE IF NOT EXISTS fotos (
    id_foto INTEGER PRIMARY KEY AUTOINCREMENT,
    dni TEXT,
    nombre_equipo TEXT,
    fecha TEXT,
    hora TEXT,
    imagen_en_bytes BLOB
)
""")

# Guardar cambios y cerrar conexión
conn.commit()
conn.close()

print("Base de datos creada en:", ruta_db)
