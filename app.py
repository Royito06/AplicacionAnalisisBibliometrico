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
            df = pd.read_excel(ruta_archivo)
        else:
            return None
        return df
    except Exception as e:
        print(f"Error interno: {e}")
        return None

# Por el momento solo genera un resumen, para sprints siguientes
# se espera la bibliometría completa
def procesar_bibliometria(df,nombre_archivo):
    if df is None:
        return {"error": "El dataframe está vacío o es inválido"}
    
    # Busca una columna que contenga la palabra "Affiliation" o "Institu" sin importar mayúsculas
    col_afiliacion = next((c for c in df.columns if 'affilia' in c.lower() or 'institu' in c.lower()), None)
    
    conteo_vacios = 0
    if col_afiliacion:
        conteo_vacios = int(df[col_afiliacion].isna().sum())
        df[col_afiliacion] = df [col_afiliacion].fillna('Afiliación Desconocida')
        print(f"Se limpió la columna:{col_afiliacion}")
    else:
        print("No se encontró columna de afiliación.")
    
    #Esto es para el resumen: nomas tira cuantas "filas" tiene el archivo
    total_importados = int(df.shape[0])
    
    # Resumen: muestra algo así como un preview de los datos del archivo importado
    # Para que no truene si no se lama Title mejor buscamos el nombre primero
    col_titulo = next((c for c in df.columns if 'titl' in c.lower()), None)
    if col_titulo:
        # Descubrí que se puede cambiar internamente el nombre de la columna para que
        # el código siempre use 'Title' de ahí en adelante
        df.rename(columns={col_titulo: 'Title'}, inplace=True)
    
    # Resumen: Deja las puras filas con titulos, es para limpiar datos
    registros_con_titulo = int(df['Title'].dropna().count()) if 'Title' in df.columns else 0
    
    libros_resumen = df['Title'].head(5).tolist() if 'Title' in df.columns else []
    autores_resumen = df['Authors'].head(5).tolist() if 'Authors' in df.columns else []  #Revisar si la columna si se llama authors
    
    resumen = {
        "confirmación": {
            "archivo": nombre_archivo,
            "mensaje": "Carga y procesamiento exitoso"
        },
        
        "metricas": {
            "total_articulos": total_importados,      
            "articulos_validos": registros_con_titulo,
            "afiliaciones_corregidas": conteo_vacios
        },
        "resumen_contenido": {
            "libros": libros_resumen,
            "autores": autores_resumen
        },
        
    }
    return resumen

# --- RUTAS DE FLASK ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
        "status": "error",
        "message": "Solicitud malformada: No se encontró el archivo."
    }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
        "status": "error",
        "message": "Operación cancelada: No se seleccionó ningún archivo/Nombre vacío."
    }), 400
    try: 
    # Se guarda temporalmente
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Se leen los datos
        df = leer_archivo_datos(filepath)
        if df is not None:
            resumen = procesar_bibliometria(df, file.filename)
            return jsonify(resumen), 200
        else:
            return jsonify({
            "status": "error",
            "message": "No se pudo procesar"
            }), 500
            
        """
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
            
            return jsonify({
                "status": "error",
                "message": "No se pudo procesar el contenido. Verifica el formato del archivo."
            }), 500
            
            
        """
    except Exception as e:
        # Error crítico (ej. no se pudo guardar el archivo en disco)
        return jsonify({
            "status": "error",
            "message": "Error crítico en el servidor.",
            "details": str(e)
        }), 500
        
    


if __name__ == '__main__':
    app.run(debug=True)
    
    
    """
    Esto es para prueba
    
ruta= "simon&pumba.csv"
dataframe = leer_archivo_datos(ruta)
resultado_final = procesar_bibliometria(dataframe, os.path.basename(ruta))

print(resultado_final)
    """