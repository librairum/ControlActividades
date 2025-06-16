import mysql.connector
from PIL import Image
import io

# Conexión
conexion = mysql.connector.connect(
    host="mysql-a21bb78-sistemasnet26-321c.k.aivencloud.com",
    port=10658,
    user="avnadmin",
    password="AVNS_85euRnRiqGGv-rmyWsj",
    database="gmadministracion",
    auth_plugin='mysql_native_password'
)

cursor = conexion.cursor()

# Seleccionar una imagen por id
cursor.execute("SELECT imagen_en_bytes FROM asistencia_imagenes WHERE id_foto = 19")  # Cambia el id_foto si es necesario
imagen_bytes = cursor.fetchone()[0]

# Mostrar la imagen
imagen = Image.open(io.BytesIO(imagen_bytes))
imagen.show()

cursor.close()
conexion.close()
