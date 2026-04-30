from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import os
import io
import base64
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from src.cleaner import limpiar_dataset
import src.metrics

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ultimo_df_procesado = None
historial_busquedas = []

def leer_archivo_datos(ruta_archivo):
    extension = os.path.splitext(ruta_archivo)[1].lower()
    try:
        if extension == '.csv':
            return pd.read_csv(ruta_archivo)
        elif extension in ['.xls', '.xlsx']:
            return pd.read_excel(ruta_archivo)
        return None
    except Exception:
        return None

def generar_wordcloud(df):
    if 'Title' not in df.columns or df['Title'].empty:
        return None
    texto = " ".join(titulo for titulo in df['Title'].astype(str))
    wc = WordCloud(width=800, height=400, background_color='white').generate(texto)
    img = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(img, format='png', bbox_inches='tight')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def procesar_bibliometria(df, nombre_archivo):
    col_afiliacion = next((c for c in df.columns if 'affilia' in c.lower() or 'institu' in c.lower()), None)
    conteo_vacios = 0
    if col_afiliacion:
        conteo_vacios = int(df[col_afiliacion].isna().sum())
        df[col_afiliacion] = df[col_afiliacion].fillna('Afiliación Desconocida')
    
    total_importados = int(df.shape[0])
    col_titulo = next((c for c in df.columns if 'titl' in c.lower()), None)
    if col_titulo:
        df.rename(columns={col_titulo: 'Title'}, inplace=True)
    
    registros_con_titulo = int(df['Title'].dropna().count()) if 'Title' in df.columns else 0
    
    return {
        "confirmación": {"archivo": nombre_archivo},
        "metricas": {
            "total_articulos": total_importados,
            "articulos_validos": registros_con_titulo,
            "afiliaciones_corregidas": conteo_vacios
        }
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global ultimo_df_procesado, historial_busquedas

    if 'file' not in request.files:
        return jsonify({"status": "error"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error"}), 400

    try: 
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        df_base = leer_archivo_datos(filepath)
        
        if df_base is not None:
            df_limpio = limpiar_dataset(df_base)
            
            anio_inicio = request.form.get('anio_inicio', type=int)
            anio_fin = request.form.get('anio_fin', type=int)
            
            registro = {
                "archivo": file.filename,
                "fecha": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                "filtro_inicio": anio_inicio if anio_inicio else "N/A",
                "filtro_fin": anio_fin if anio_fin else "N/A",
                "registros": len(df_limpio)
            }
            historial_busquedas.append(registro)

            ultimo_df_procesado = df_limpio.copy()

            resumen = procesar_bibliometria(df_limpio, file.filename)
            resumen['wordcloud'] = generar_wordcloud(df_limpio)
            resumen['analisis_avanzado'] = {
                "rango": src.metrics.obtener_rango_anios(df_limpio),
                "productividad": src.metrics.calcular_promedio_publicaciones(df_limpio),
                "top_10": src.metrics.obtener_top_10_autores(df_limpio),
                "top_citas_anuales": src.metrics.obtener_top_citas_anuales(df_limpio),
                "tasa_crecimiento": src.metrics.calcular_tasa_crecimiento(df_limpio)
            }
            
            return jsonify(resumen), 200
        return jsonify({"status": "error"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/historial', methods=['GET'])
def obtener_historial():
    return jsonify({"datos": historial_busquedas[::-1]}), 200

@app.route('/download/excel')
def descargar_excel():
    if ultimo_df_procesado is not None:
        buffer = src.metrics.excel_descargar(ultimo_df_procesado)
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='reporte.xlsx')
    return jsonify({"error": "Sin datos"}), 400

@app.route('/download/word')
def descargar_word():
    if ultimo_df_procesado is not None:
        buffer = src.metrics.word_descargar(ultimo_df_procesado, titulo="Reporte Bibliométrico")
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', as_attachment=True, download_name='reporte.docx')
    return jsonify({"error": "Sin datos"}), 400

if __name__ == '__main__':
    app.run(debug=True)
    """
    Esto es para prueba
    
ruta= "simon&pumba.csv"
dataframe = leer_archivo_datos(ruta)
resultado_final = procesar_bibliometria(dataframe, os.path.basename(ruta))

print(resultado_final)
    """