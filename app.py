# Equivalente a tus "#include" en C++. Traemos herramientas específicas de la librería Flask.
from flask import Flask, request, jsonify, render_template

# Librería estándar de Python para interactuar con el sistema operativo (crear carpetas, buscar rutas).
import os

# Importamos tu propia función desde el módulo que creamos.
from src.data_loader import leer_archivo_datos

# Aquí "instanciamos" la aplicación. Es como crear el objeto principal de tu programa.
# __name__ es una variable especial de Python que le dice a Flask dónde buscar las cosas.
app = Flask(__name__)

# Definimos una constante con el nombre de la carpeta donde guardaremos los CSV temporales.
UPLOAD_FOLDER = 'uploads'

# Esto le dice al sistema operativo: "Crea la carpeta 'uploads'". 
# exist_ok=True evita que el programa se caiga (crash) si la carpeta ya existe.
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- RUTAS DE FLASK ---
# El símbolo @ denota un "Decorador". Básicamente le dice a Flask: 
# "Cuando alguien entre a la URL principal ('/'), ejecuta la función que está justo abajo".

@app.route('/')
def index():
    # render_template busca automáticamente en la carpeta "templates" y envía ese HTML al navegador.
    return render_template('index.html')


# Esta ruta es diferente. '/upload' es a donde tu formulario de Dropzone envía el archivo.
# methods=['POST'] significa que esta ruta solo acepta envío de datos, no se puede entrar escribiéndola en el navegador.
@app.route('/upload', methods=['POST'])
def upload_file():
    
    # request.files contiene lo que el usuario subió. Si no hay nada llamado 'file', devolvemos un error 400 (Bad Request).
    if 'file' not in request.files:
        return jsonify({"error": "No hay archivo"}), 400
    
    # Extraemos el archivo de la petición y lo guardamos en una variable.
    file = request.files['file']
    
    # Validamos que el archivo realmente tenga un nombre (a veces los navegadores envían archivos vacíos fantasma).
    if file.filename == '':
        return jsonify({"error": "Nombre vacío"}), 400

    # os.path.join une la ruta de la carpeta con el nombre del archivo de forma segura (ej. "uploads/dataset.csv").
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    
    # Guardamos físicamente el archivo en el disco duro de la computadora.
    file.save(filepath)
    
    # Llamamos a tu función de Pandas. Pasamos la ruta y nos devuelve un DataFrame (tabla de datos).
    df = leer_archivo_datos(filepath)

    # En Python, "is not None" es el equivalente a comprobar si un puntero no es NULL (df != nullptr).
    if df is not None:
        
        # list(df.columns) extrae los nombres de las columnas (ej. Autor, Año, Citas) y los vuelve un arreglo (lista).
        columnas = list(df.columns)
        
        # len() funciona como el .size() de C++, nos da la cantidad total de filas que tiene el archivo.
        total_filas = len(df)
        
        # jsonify convierte nuestro diccionario de Python en un formato JSON que el navegador y Dropzone entienden.
        # El 200 es el código de éxito HTTP.
        return jsonify({
            "mensaje": "Archivo cargado y procesado",
            "columnas": columnas,
            "total_registros": total_filas
        }), 200
        
    else:
        # Si la función devolvió None (hubo un error al leer el CSV), mandamos un error 500 (Error interno del servidor).
        return jsonify({"error": "No se pudo procesar el contenido del archivo"}), 500


# Este bloque "if" es el equivalente directo a tu función "int main()" en C++.
# Solo se ejecuta si corres este archivo directamente desde la terminal (python app.py).
if __name__ == '__main__':
    # Arrancamos el servidor. debug=True hace que el servidor se reinicie solo cuando guardas cambios en el código.
    app.run(debug=True)