from flask import Flask, request, jsonify, render_template
import pandas as pd
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Funciones ---
def leer_archivo_datos(ruta_archivo):
    """
    Lee un archivo CSV o Excel y devuelve un DataFrame de Pandas.
    """
    extension = os.path.splitext(ruta_archivo)[1].lower()
    try:
        if extension == '.csv':
            df = pd.read_csv(ruta_archivo)
        elif extension in ['.xls', '.xlsx']:
            df = pd.read_excel(ruta_archivo, engine='openpyxl')
        else:
            return None
        return df
    except Exception as e:
        print(f"Error interno: {e}")
        return None

# --- RUTAS DE FLASK ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No hay archivo"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre vacío"}), 400

    # Se guarda temporalmente
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    
    df = leer_archivo_datos(filepath)

    if df is not None:
        #Aquí se maneja el dataframe
        columnas = list(df.columns)
        total_filas = len(df)
        
        return jsonify({
            "mensaje": "Archivo cargado y procesado",
            "columnas": columnas,
            "total_registros": total_filas
        }), 200
    else:
        return jsonify({"error": "No se pudo procesar el contenido del archivo"}), 500


if __name__ == '__main__':
    app.run(debug=True)