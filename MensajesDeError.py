# --- VALIDACIÓN DE ENTRADA Y MANEJO DE EXCEPCIONES ---

# Verificar la presencia del objeto 'file' en los archivos de la solicitud
# Garantiza que el cliente haya enviado un cuerpo multipart/form-data con la clave correcta
from flask import Flask, request, jsonify, render_template, send_file

@app.route('/upload', methods=['POST'])
def upload_file():
    global ultimo_df_procesado  # <--- CRUCIAL: Para que las descargas funcionen
    if 'file' not in request.files:
        return jsonify({
            "status": "error",
            "message": "Solicitud malformada: Falta el parámetro 'file'."
        }), 400

    file = request.files['file']

    # Validar si el nombre del archivo está vacío
    # Maneja el caso en que el usuario envía el formulario sin haber seleccionado un archivo
    if file.filename == '':
        return jsonify({
            "status": "error",
            "message": "Operación cancelada: No se seleccionó ningún archivo."
        }), 400

    except Exception as e:
        # Captura de errores en tiempo de ejecución durante el parsing o guardado

    return jsonify({
            "status": "error",
            "message": "Error interno al procesar el conjunto de datos.",
            "details": str(e)
        }), 500