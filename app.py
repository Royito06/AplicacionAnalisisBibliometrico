from flask import Flask, request, jsonify, render_template, session, redirect, Response
import os
import pandas as pd

# Importamos las funciones desde los módulos que creamos.
from src.data_loader import leer_archivo_datos
from src.metrics import (obtener_rango_anios, calcular_promedio_publicaciones, 
                         obtener_top_10_autores, obtener_top_10_trabajos, 
                         contabilizar_coautorias, obtener_articulos_por_universidad, 
                         calcular_promedio_citas, obtener_lista_paises, 
                         obtener_detalle_articulo, calcular_proporcion_citadas)

app = Flask(__name__)

# Para que Flask pueda recordar datos del usuario (Sesiones)
app.secret_key = 'super_clave_secreta_bibliometrica' 

# Definimos la carpeta donde guardaremos los CSV temporales
UPLOAD_FOLDER = 'uploads'

# Esto le dice al sistema operativo: "Crea la carpeta 'uploads'". 
# exist_ok=True evita que el programa crashee si la carpeta ya existe.
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------------------------ RUTAS DE FLASK -------------------------------------------------

@app.route('/')
def index():
    # render_template busca automáticamente en la carpeta templates y envía ese html al navegador
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    
    # request.files contiene lo que el usuario subió.
    if 'file' not in request.files:
        return jsonify({"error": "No hay archivo"}), 400
    
    # Extraemos el archivo de la petición
    file = request.files['file']
    
    # Validamos que el archivo realmente tenga un nombre
    if file.filename == '':
        return jsonify({"error": "Nombre vacío"}), 400

    # os.path.join une la ruta de la carpeta con el nombre del archivo de forma segura
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    
    # Guardamos físicamente el archivo en el disco duro de la computadora.
    file.save(filepath)
    
    # Registramos este archivo como el proyecto activo en la memoria de la sesión
    session['proyecto_actual'] = file.filename
    
    # Llamamos a la función, pasamos la ruta y nos devuelve un DataFrame
    df = leer_archivo_datos(filepath)

    # Verificamos si el puntero no es null
    if df is not None:
        
        columnas = list(df.columns)
        total_filas = len(df)

        # Ejecución de todas las métricas
        resultado_anios = obtener_rango_anios(df)
        resultado_promedio = calcular_promedio_publicaciones(df)
        top_10 = obtener_top_10_autores(df)
        coautorias = contabilizar_coautorias(df)
        promedio_citas = calcular_promedio_citas(df)
        proporcion_citas = calcular_proporcion_citadas(df)
        
        # jsonify convierte el diccionario de Python en un formato JSON que Dropzone entiende
        return jsonify ({
            "mensaje": "Archivo cargado y procesado",
            "columnas": columnas,
            "total_registros": total_filas,
            "rango_anios": resultado_anios,
            "promedio_autores": resultado_promedio,
            "top_10_autores": top_10,
            "coautorias": coautorias,
            "impacto_citas": promedio_citas,
            "proporcion_citadas": proporcion_citas
        }), 200 # Código de éxito HTTP
        
    else:
        # Si la función devolvió None, mandamos un error 500
        return jsonify({"error": "No se pudo procesar el contenido del archivo"}), 500

#-----------------------------------------------------------------------------------------------

@app.route('/top-trabajos')
def top_trabajos():
    proyecto_actual = session.get('proyecto_actual')
    
    if not proyecto_actual:
        return "Primero debes subir un archivo o seleccionar un proyecto existente."
        
    ruta_archivo = os.path.join(UPLOAD_FOLDER, proyecto_actual)
    df = leer_archivo_datos(ruta_archivo)
    
    if df is not None:
        top_10_data = obtener_top_10_trabajos(df)
        return render_template('top_trabajos.html', trabajos=top_10_data)
    else:
        return "Hubo un error al leer el archivo de datos."

#-----------------------------------------------------------------------------------------------

@app.route('/universidad/<nombre_universidad>')
def articulos_universidad(nombre_universidad):
    proyecto_actual = session.get('proyecto_actual')
    
    if not proyecto_actual:
        return "Primero debes subir un archivo o seleccionar un proyecto existente."
        
    ruta_archivo = os.path.join(UPLOAD_FOLDER, proyecto_actual)
    df = leer_archivo_datos(ruta_archivo)
    
    if df is not None:
        articulos_encontrados = obtener_articulos_por_universidad(df, nombre_universidad)
        return render_template('universidad.html', 
                               nombre_buscado=nombre_universidad, 
                               articulos=articulos_encontrados)
    else:
        return "Error al leer el archivo."

#-----------------------------------------------------------------------------------------------

@app.route('/paises')
def lista_paises():
    proyecto_actual = session.get('proyecto_actual')
    
    if not proyecto_actual:
        return "Primero debes subir un archivo o seleccionar un proyecto existente."
        
    ruta_archivo = os.path.join(UPLOAD_FOLDER, proyecto_actual)
    df = leer_archivo_datos(ruta_archivo)
    
    if df is not None:
        datos_paises = obtener_lista_paises(df)
        return render_template('paises.html', paises=datos_paises)
    else:
        return "Error al leer el archivo de datos."

#-----------------------------------------------------------------------------------------------

@app.route('/articulo/<path:titulo>')
def detalle_articulo(titulo):
    proyecto_actual = session.get('proyecto_actual')
    
    if not proyecto_actual:
        return "Primero debes subir un archivo o seleccionar un proyecto existente."
        
    ruta_archivo = os.path.join(UPLOAD_FOLDER, proyecto_actual)
    df = leer_archivo_datos(ruta_archivo)
    
    if df is not None:
        datos_completos = obtener_detalle_articulo(df, titulo)
        return render_template('articulo.html', detalle=datos_completos)
    else:
        return "Error al leer el archivo de datos."

#-----------------------------------------------------------------------------------------------

@app.route('/proyectos')
def gestor_proyectos():
    archivos_disponibles = os.listdir(UPLOAD_FOLDER)
    proyecto_activo = session.get('proyecto_actual')
    return render_template('proyectos.html', archivos=archivos_disponibles, actual=proyecto_activo)

#-----------------------------------------------------------------------------------------------

@app.route('/seleccionar-proyecto/<nombre_archivo>')
def seleccionar_proyecto(nombre_archivo):
    session['proyecto_actual'] = nombre_archivo
    return redirect('/')

#-----------------------------------------------------------------------------------------------

@app.route('/exportar/<metrica>')
def exportar_csv(metrica):
    # Verificamos que haya un proyecto activo
    proyecto_actual = session.get('proyecto_actual')
    if not proyecto_actual:
        return "Primero debes subir un archivo.", 400
        
    ruta_archivo = os.path.join(UPLOAD_FOLDER, proyecto_actual)
    df = leer_archivo_datos(ruta_archivo)
    
    if df is None:
        return "Error al leer los datos.", 500

    # Dependiendo de qué botón presionó el usuario, calculamos esa métrica específica
    if metrica == 'paises':
        datos = obtener_lista_paises(df)
        nombre_archivo = "lista_paises.csv"
    elif metrica == 'top_trabajos':
        datos = obtener_top_10_trabajos(df)
        nombre_archivo = "top_10_trabajos.csv"
    elif metrica == 'top_autores':
        datos = obtener_top_10_autores(df)
        nombre_archivo = "top_10_autores.csv"
    else:
        return "Métrica no válida para exportación.", 404

    # Convertimos la lista de resultados en un DataFrame temporal de Pandas
    df_export = pd.DataFrame(datos)
    
    # Lo transformamos a formato texto CSV (index=False evita que se imprima la columna de números 0,1,2...)
    csv_data = df_export.to_csv(index=False)
    
    # Devolvemos el texto disfrazado de archivo descargable
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={nombre_archivo}"}
    )

#-----------------------------------------------------------------------------------------------

if __name__ == '__main__':
    # Arrancamos el servidor.
    app.run(debug=True)