from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import datetime
import os
import io
from typing import Any, Dict
from werkzeug.utils import secure_filename
from src.data_loader import leer_archivo_datos
from src.cleaner import limpiar_dataset
from src.metrics import (
    obtener_rango_anios,
    calcular_promedio_publicaciones,
    obtener_top_10_autores,
    obtener_articulo_sin_citas,
    excel_descargar,
    word_descargar,
    calcular_h_index,       
    distribucion_documentos
)



app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ultimo_df_procesado = None

# --- Funciones ---    
def es_autor_unico(valor):
        partes = [p.strip() for p in valor.split(';') if p.strip()]
        if len(partes) > 1:
            return False   # los autores suelen separarse por ;
        if len(partes) == 1:
            return True    # 
        # si no hay ; revisa por comas (formato Scopus)
        return len([p for p in valor.split(',') if p.strip()]) <= 2

def formatear_apa(fila, col_revista, col_volumen, col_numero, col_paginas):
    autores_sin_formato = str(fila.get('Authors', ''))
    autores_lista = [ a.strip() for a in autores_sin_formato.split(';') if a.strip()]
    if len(autores_lista) == 1:
        autores_apa = autores_lista[0]
    elif len(autores_lista)>1:
        autores_apa = ', '.join(autores_lista[:-1])+ ', & ' + autores_lista[-1]
    else:
        autores_apa = 'Autor desconocido'
        
    anio     = str(fila.get('Year',         ''))
    titulo   = str(fila.get('Title',        ''))
    revista  = str(fila.get(col_revista,    '')) if col_revista else ''
    volumen  = str(fila.get(col_volumen,    '')) if col_volumen else ''
    numero   = str(fila.get(col_numero,     '')) if col_numero  else ''
    paginas  = str(fila.get(col_paginas,    '')) if col_paginas else ''
    
        # Construir progresivamente — solo agrega lo que existe
    ref = f"{autores_apa}. ({anio}). {titulo}."
    if revista:
        ref += f" {revista}"
        if volumen:
            ref += f", {volumen}"
            if numero:
                ref += f"({numero})"
        if paginas:
            ref += f", {paginas}"
        ref += "."

    return ref
  

def procesar_bibliometria(df, nombre_archivo):
    if df is None or df.empty:
        return {"error": "El dataframe está vacío o es inválido"}

    #  Normalizar columnas (clave)
    df = df.copy()
    
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

    articulos_autor_unico = []
    total_autor_unico = 0

    if 'Authors' in df.columns and 'Title' in df.columns:


        col_au = df['Authors'].fillna('').astype(str)  
        autor_unico = col_au.apply(es_autor_unico)
        autor_unico = autor_unico & (col_au != '')

        df_unicos = df[autor_unico]
        total_autor_unico = int(len(df_unicos))
        articulos_autor_unico = (
            df_unicos[['Title', 'Authors']]
            .dropna(subset=['Title'])
            .head(20)
            .values.tolist()
        )
        
    #minimo y maximo de autores
    min_autores = 0
    max_autores = 0
    promedio_autores = 0
    
    if 'Authors' in df.columns:

        def contar_autores(valor):
            if pd.isna(valor) or str(valor).strip() == '':
                return None
            partes = [p.strip() for p in str(valor).split(';') if p.strip()]
            return len(partes)

        conteo = df['Authors'].apply(contar_autores).dropna()

        min_autores      = int(conteo.min())
        max_autores      = int(conteo.max())
        promedio_autores = round(float(conteo.mean()), 2)

    # ---------------- TOPS ----------------
    col_revista = next((c for c in df.columns if 'source' in c.lower() or 'journal' in c.lower()), None)
    col_citas = next((c for c in df.columns if 'cite' in c.lower()), None)
    col_ciudad = next((c for c in df.columns if 'city' in c.lower()), None)
    col_volumen = next((c for c in df.columns if c.lower() in ('volume', 'vol')), None)
    col_numero  = next((c for c in df.columns if c.lower() in ('issue', 'number')), None)
    col_paginas = next((c for c in df.columns if 'page' in c.lower()), None)
    col_anio    = next((c for c in df.columns if 'year' in c.lower()), None)

    top_revistas = []
    if col_revista:
        top_revistas = df[col_revista].value_counts().head(10).reset_index().values.tolist()

    
    top_citados = []
    if 'Title' in df.columns and col_citas:
        df[col_citas] = pd.to_numeric(df[col_citas], errors='coerce').fillna(0)
        top_df = df.sort_values(by=col_citas, ascending=False).head(10)
        
        top_citados = []
        for _, fila in top_df.iterrows():
            top_citados.append({
                'titulo': str(fila['Title']),
                'citas':  int(fila[col_citas]),
                'apa':    formatear_apa(fila,col_revista,col_volumen,col_numero,col_paginas)
            })

    # ---------------- Afiliaciones ----------------
    top_Afiliaciones = []
    top_Ciudades = []
    top_universidades = []

    if col_afiliacion:
        serieUniversidades = df[col_afiliacion].dropna().astype(str)
        top_Afiliaciones = df[col_afiliacion].astype(str)\
            .str.split(',').str[0]\
            .value_counts().head(10).reset_index().values.tolist()
        
        serie_explotada = (
            serieUniversidades
            .str.split(';')       # parte cada celda en lista de afiliaciones
            .explode()            # convierte cada elemento de la lista en su propia fila
            .str.strip()          # quita espacios sobrantes
            .loc[lambda s: s != '']  # descarta strings vacíos
        )
        universidades = (
            serie_explotada
            .str.split(',')
            .str[0]             
            .str.strip()
        )
        top_universidades = (
            universidades
            .value_counts()       # cuenta y ordena de mayor a menor automáticamente
            .head(10)
            .reset_index()
            .values.tolist()
        )
        # El if puede parecer algo largo pero si no se hace de esta manera puede tronar si no hay columna de afiliación
    
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
        
        
    # ---------------- Citas ----------------
    promedio_citas_anual = None
    #El promedio se calcula: citas totales/(año actual-año de publicación+1)
    if col_citas and col_anio: 
        anio_actual = datetime.datetime.now().year
        
        df_citas = df[[col_anio, col_citas]].copy()
        df_citas[col_anio] = pd.to_numeric(df_citas[col_anio], errors= 'coerce')
        df_citas[col_citas] = pd.to_numeric(df_citas[col_citas], errors='coerce')
        df_citas = df_citas.dropna() 
        
        # Años transcurridos desde publicación 
        df_citas['anios_activo'] = (anio_actual - df_citas[col_anio] + 1).clip(lower=1)

        # Citas por año para cada artículo
        df_citas['citas_por_anio'] = df_citas[col_citas] / df_citas['anios_activo']

        promedio_citas_anual = round(float(df_citas['citas_por_anio'].mean()), 2)
    # ---------------- Resultado ----------------
    resumen = {
        "confirmación": {
            "archivo": nombre_archivo,
            "mensaje": "Carga y procesamiento exitoso"
        },
        "metricas": {
            "total_articulos": total_importados,
            "articulos_validos": registros_con_titulo,
            "afiliaciones_corregidas": conteo_vacios,
            "min_autores": min_autores,
            "max_autores": max_autores,
            "promedio_autores": promedio_autores
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
            "Afiliaciones": top_Afiliaciones,
            "Universidades": top_universidades
        },
        "autor_unico": {
            "total":     total_autor_unico,
            "articulos": articulos_autor_unico   
        },
        "promedio_citas_anual": promedio_citas_anual
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




def actualizar_dataset(df_existente, df_nuevo):
    try:
        df_combinado  = pd.concat([df_existente, df_nuevo], ignore_index=True)
        df_actualizado = df_combinado.drop_duplicates(subset=['Title'], keep='last')  
        return df_actualizado
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return df_existente

# --- RUTAS DE FLASK ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global ultimo_df_procesado

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
        nombre_seguro = secure_filename(file.filename or "archivo_sin_nombre") #El nombre seguro no es necesario pero se usa para evitar errores
        filepath = os.path.join(UPLOAD_FOLDER, nombre_seguro)
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
            #Esta línea es para evitar una error con el tipado


            total_sin_citas = obtener_articulo_sin_citas(df)
            resumen: Dict[str, Any] = procesar_bibliometria(df, file.filename or "archivo")
            resumen['metricas']['articulos_sin_citas'] = int(total_sin_citas)
            resumen['analisis_avanzado'] = {
                "rango": obtener_rango_anios(df),
                "productividad": calcular_promedio_publicaciones(df),
                "top_10": obtener_top_10_autores(df)
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

@app.route('/buscar', methods=['POST'])
def buscar_datos():
    global ultimo_df_procesado                          # ← usa esto, no "df"

    if ultimo_df_procesado is None:
        return jsonify({"status": "error", "message": "No hay datos cargados"}), 400

    filtros = request.json
    if not filtros:
        return jsonify({"status": "error", "message": "No se recibieron filtros"}), 400

    try:
        df_filtrado = ultimo_df_procesado.copy()        # ← era df.copy(), incorrecto
        for columna, valor in filtros.items():
            if valor and columna in df_filtrado.columns:
                df_filtrado = df_filtrado[
                    df_filtrado[columna].astype(str).str.contains(str(valor), case=False)
                ]
        return jsonify({
            "status": "success",
            "resultados_encontrados": len(df_filtrado),
            "datos": df_filtrado.to_dict(orient='records')  # ← era df_[filtrado.to_dict], typo
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/analisis/conectores', methods=['GET'])
def identificar_conectores():
    global ultimo_df_procesado                          # ← usa esto, no "df"

    if ultimo_df_procesado is None:
        return jsonify({"status": "error", "message": "No hay datos cargados"}), 400

    try:
        df = ultimo_df_procesado.copy()
        col_autor = next(
            (c for c in df.columns if c.lower() in ('authors', 'author', 'au')), None
        )
        if col_autor is None:
            return jsonify({"status": "error", "message": "No se encontró columna de autores"}), 400

        # Explotar autores en filas individuales
        autores_explotados = (
            df[col_autor].dropna().astype(str)
            .str.split(';')
            .explode()
            .str.strip()
        )
        conectores = autores_explotados.value_counts().head(10).to_dict()  # ← lógica corregida

        return jsonify({
            "status": "success",
            "descripcion": "Autores con mayor número de publicaciones",
            "data": conectores
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/analisis/anomalias', methods=['GET'])
def detectar_anomalias():
    global ultimo_df_procesado                         

    if ultimo_df_procesado is None:
        return jsonify({"status": "error", "message": "No hay datos cargados"}), 400

    try:
        df = ultimo_df_procesado.copy()
        col_citas = next((c for c in df.columns if 'cite' in c.lower()), None)  # ← detecta la columna dinámicamente

        if col_citas is None:
            return jsonify({"status": "error", "message": "No se encontró columna de citas"}), 400

        data_puntos = pd.to_numeric(df[col_citas], errors='coerce').dropna()
        Q1  = data_puntos.quantile(0.25)
        Q3  = data_puntos.quantile(0.75)
        IQR = Q3 - Q1
        limite_superior = Q3 + 1.5 * IQR

        exitos = df[pd.to_numeric(df[col_citas], errors='coerce') > limite_superior]

        col_titulo = 'Title'   if 'Title'   in df.columns else None
        col_autor  = 'Authors' if 'Authors' in df.columns else None

        cols = [c for c in [col_titulo, col_autor, col_citas] if c]  # solo columnas que existen
        return jsonify({
            "status": "success",
            "total_anomalias_detectadas": len(exitos),
            "limite_calculado": limite_superior,
            "casos_extraordinarios": exitos[cols].to_dict(orient='records')
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



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
