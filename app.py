from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import os
import io
from src.data_loader import leer_archivo_datos
from src.cleaner import limpiar_dataset

from src.metrics import (
    obtener_rango_anios,
    calcular_promedio_publicaciones,
    obtener_top_10_autores,
    obtener_articulo_sin_citas,
    excel_descargar,
    word_descargar
)



app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ultimo_df_procesado = None

# --- Funciones ---

# Por el momento solo genera un resumen, para sprints siguientes
# se espera la bibliometría completa
def procesar_bibliometria(df, nombre_archivo):
    if df is None or df.empty:
        return {"error": "El dataframe está vacío o es inválido"}

    #  Normalizar columnas (clave)
    df.columns = df.columns.str.strip()

    print("Columnas detectadas:", df.columns.tolist())

    #  Mapear nombres comunes (WoS/Scopus/etc)
    mapa_columnas = {
        'ti': 'Title',
        'article title': 'Title',
        'article titles': 'Title',
        'au': 'Authors',
        'authors': 'Authors',
        'py': 'Year'
    }

    for col in df.columns:
        key = col.lower().strip()
        if key in mapa_columnas:
            df.rename(columns={col: mapa_columnas[key]}, inplace=True)

    # ---------------- Afiliaciones ----------------
    col_afiliacion = next((c for c in df.columns if 'affilia' in c.lower() or 'institu' in c.lower()), None)

    conteo_vacios = 0
    if col_afiliacion:
        conteo_vacios = int(df[col_afiliacion].isna().sum())
        df[col_afiliacion] = df[col_afiliacion].fillna('Afiliación Desconocida')
        print(f"Se limpió la columna: {col_afiliacion}")
    else:
        print("No se encontró columna de afiliación.")

    total_importados = int(df.shape[0])

    # ---------------- TITULOS ----------------
    if 'Title' not in df.columns:
        print(" No se encontró columna Title")
    
    registros_con_titulo = int(df['Title'].dropna().count()) if 'Title' in df.columns else 0
    libros_resumen = df['Title'].dropna().head(20).tolist() if 'Title' in df.columns else []

    print("Ejemplo títulos:", libros_resumen[:3])

    # ---------------- AUTORES ----------------
    autores_resumen = df['Authors'].dropna().head(20).tolist() if 'Authors' in df.columns else []

    # ---------------- TOPS ----------------
    col_revista = next((c for c in df.columns if 'source' in c.lower() or 'journal' in c.lower()), None)
    col_citas = next((c for c in df.columns if 'cite' in c.lower()), None)
    col_ciudad = next((c for c in df.columns if 'city' in c.lower()), None)

    top_revistas = []
    if col_revista:
        top_revistas = df[col_revista].value_counts().head(10).reset_index().values.tolist()

    # 🔥 FIX IMPORTANTE AQUÍ
    top_citados = []
    if 'Title' in df.columns and col_citas:
        df[col_citas] = pd.to_numeric(df[col_citas], errors='coerce').fillna(0)
        top_citados = df.sort_values(by=col_citas, ascending=False)\
                        .head(10)[['Title', col_citas]].values.tolist()

    # ---------------- Afiliaciones ----------------
    top_Afiliaciones = []
    top_Ciudades = []

    if col_afiliacion:
        top_Afiliaciones = df[col_afiliacion].astype(str)\
            .str.split(',').str[0]\
            .value_counts().head(10).reset_index().values.tolist()

    #if col_ciudad:
    #    top_Ciudades = df[col_ciudad].astype(str)\
    #        .str.split(',').str[-1].str.strip()\
    #        .value_counts().head(10).reset_index().values.tolist()
    if col_ciudad:
        top_Ciudades = (
            df[col_ciudad]
            .dropna()                          # elimina NaN reales antes de convertir
            .astype(str)
            .str.strip()
            .loc[lambda s: s != '']            # descarta strings vacíos
            .str.split(',')
            .apply(lambda x: x[-1].strip() if isinstance(x, list) and len(x) > 0 else None)
            .dropna()                          # elimina los None resultantes
            .value_counts().head(10).reset_index().values.tolist()
    )

    # ---------------- Resultado ----------------
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
        "tops": {
            "revistas": top_revistas,
            "citados": top_citados
        },
        "Afiliaciones": {
            "ciudades": top_Ciudades,
            "Afiliaciones": top_Afiliaciones
        }
    }

    return resumen

def filtrar_por_anio(df, inicio, fin):
    """
    Filtra el Dataframe por un rango de años
    """
    col_anio = next((c for c in df.columns if 'year' in c.lower() or 'año' in c.lower()), None)

    if col_anio and inicio is not None and fin is not None:
        df = df.copy()
        df[col_anio] = pd.to_numeric(df[col_anio], errors = 'coerce')
        df = df.dropna(subset = [col_anio])
        return df[(df[col_anio] >=inicio) & (df[col_anio] <= fin)]
    return df

def identificar_no_citados(df):
    """
    Cuenta cuántos artículos tienen 0 citas en WoS
    """
    col_citas = next((c for c in df.columns if 'times cited, wos' in c.lower()), None)
    if col_citas:
        conteo_sin_citas = (pd.to_numeric(df[col_citas], errors = 'coerce').fillna(0) == 0).sum()
        return int(conteo_sin_citas)
    return 0

# --- RUTAS DE FLASK ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    #global ultimo_df_procesado

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
            df = limpiar_dataset(df)
            anio_inicio = request.form.get('anio_inicio', type = int)
            anio_fin = request.form.get('anio_fin', type = int)
            if anio_inicio and anio_fin:
                df = filtrar_por_anio(df, anio_inicio, anio_fin)
            
            ultimo_df_procesado = df.copy()
            rango = obtener_rango_anios(df)
            promedio = calcular_promedio_publicaciones(df)
            top_10 = obtener_top_10_autores(df)
            total_sin_citas = identificar_no_citados(df)
            resumen = procesar_bibliometria(df, file.filename)
            resumen['metricas']['articulos_sin_citas'] = int(total_sin_citas)
            resumen['analisis_avanzado'] = {
                "rango": rango,
                "productividad": promedio,
                "top_10": top_10
            }
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

# Descargas de archivos(Excel y Word)
@app.route('/download/excel')
def descargar_excel():
    """Genera y descarga el archivo Excel basado en el último procesamiento."""
    global ultimo_df_procesado
    if ultimo_df_procesado is not None:
        # Llamamos a la función de exportación que tienes en metrics.py
        buffer = excel_descargar(ultimo_df_procesado)
        return send_file(
            buffer, 
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True, 
            download_name='reporte_bibliometrico.xlsx'
        )
    return jsonify({"error": "No hay datos procesados disponibles"}), 400

@app.route('/download/word')
def descargar_word():
    """Genera y descarga el reporte en Word basado en el último procesamiento."""
    global ultimo_df_procesado
    if ultimo_df_procesado is not None:
        # Llamamos a la función de exportación que tienes en metrics.py
        buffer = word_descargar(ultimo_df_procesado, titulo="Reporte de Análisis Bibliométrico")
        return send_file(
            buffer, 
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True, 
            download_name='reporte_bibliometrico.docx'
        )
    return jsonify({"error": "No hay datos procesados disponibles"}), 400

if __name__ == '__main__':
    
    app.run(debug=True)
    
    
    """
    Esto es para prueba
    
ruta= "simon&pumba.csv"
dataframe = leer_archivo_datos(ruta)
resultado_final = procesar_bibliometria(dataframe, os.path.basename(ruta))

print(resultado_final)
    """