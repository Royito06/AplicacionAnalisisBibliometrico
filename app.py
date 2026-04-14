from flask import Flask, request, jsonify, render_template
import pandas as pd
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No hay archivo"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    # Guardar archivo
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Procesar con Pandas
    try:
        extension = os.path.splitext(file.filename)[1].lower()
        if extension == '.csv':
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, engine='openpyxl')

        # Ejemplo: obtener las primeras 5 filas para confirmar
        datos_previa = df.head().to_dict(orient='records')
        
        return jsonify({
            "mensaje": "Archivo procesado",
            "columnas": list(df.columns),
            "previa": datos_previa
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)