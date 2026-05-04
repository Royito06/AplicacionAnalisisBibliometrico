# Cálculos (Top 10, tasas de crecimiento)

import pandas as pd
import datetime
import io 
from docx import Document
import networkx as nx     

#--------------------------------------------------------------------------------------------

def obtener_rango_anios(df):
    """
    Busca la columna de años en el DataFrame y devuelve el año más antiguo y el más reciente.
    """
    # Los CSV de bases bibliométricas pueden llamar a la columna de distintas formas.
    # Aquí definimos las más comunes para que tu código sea a prueba de balas.
    posibles_nombres = ['Año', 'Year', 'PY', 'Publication Year', 'año', 'year']
    
    columna_anio = None
    
    # Buscamos cuál de esos nombres existe realmente en tu archivo
    for col in df.columns:
        if col in posibles_nombres:
            columna_anio = col
            break
            
    # Si el archivo no tiene columna de año, devolvemos un error controlado
    if columna_anio is None:
        return {"error": "No se encontró la columna de Año en el dataset."}
    
    # Eliminamos las filas que tengan esa celda vacía (NaN) para que la matemática no falle
    df_limpio = df.dropna(subset=[columna_anio])
    
    # Aquí ocurre la magia de Pandas. Equivalente a tu ciclo for para buscar min y max.
    # Usamos int() para asegurarnos de que el año salga como 2020 y no como 2020.0 (decimal)
    anio_minimo = int(df_limpio[columna_anio].min())
    anio_maximo = int(df_limpio[columna_anio].max())
    
    # Retornamos un diccionario (similar a un struct o mapa en C++) con los resultados
    return {
        "minimo": anio_minimo,
        "maximo": anio_maximo,
        "mensaje_formateado": f"Periodo analizado: {anio_minimo} - {anio_maximo}"
    }

#--------------------------------------------------------------------------------------------

def calcular_promedio_publicaciones(df):
    """
    Calcula el promedio de publicaciones por autor dividiendo 
    el total de artículos entre el número de autores únicos.
    """
    # Buscamos la columna de autores
    posibles_nombres = ['Autor', 'Autores', 'Author', 'Authors', 'AU']
    col_autor = None
    
    for col in df.columns:
        if col in posibles_nombres:
            col_autor = col
            break
            
    if col_autor is None:
        return {"error": "No se encontró la columna de Autores en el dataset."}
    
    # Quitamos las filas que no tengan autor
    df_limpio = df.dropna(subset=[col_autor])
    total_publicaciones = len(df_limpio)
    
    # Magia de Pandas: Convertimos a texto, reemplazamos los ';' por ',' y separamos cada nombre
    listas_de_autores = df_limpio[col_autor].astype(str).str.replace(';', ',').str.split(',')
    
    # Metemos a todos los autores en una sola lista gigante y les quitamos los espacios extra
    todos_los_autores = [autor.strip() for sublista in listas_de_autores for autor in sublista if autor.strip()]
    
    # Convertimos la lista en un "set" (conjunto matemático) para eliminar a los repetidos y los contamos
    autores_unicos = len(set(todos_los_autores))
    
    # Evitamos la división por cero por si el archivo viniera vacío
    if autores_unicos == 0:
        return {"error": "No hay autores válidos para calcular el promedio."}
        
    # Calculamos el promedio y lo redondeamos a 2 decimales
    promedio = total_publicaciones / autores_unicos
    
    return {
        "total_publicaciones": total_publicaciones,
        "autores_unicos": autores_unicos,
        "promedio_calculado": round(promedio, 2),
        "mensaje_formateado": f"Productividad: {round(promedio, 2)} publicaciones por autor"
    }

#--------------------------------------------------------------------------------------------

def obtener_top_10_autores(df):
    """
    Desempaqueta las listas de autores, cuenta su frecuencia y devuelve los 10 principales.
    """
    # Buscamos la columna de autores igual que en la función anterior
    posibles_nombres = ['Autor', 'Autores', 'Author', 'Authors', 'AU']
    col_autor = None
    
    for col in df.columns:
        if col in posibles_nombres:
            col_autor = col
            break
            
    if col_autor is None:
        return {"error": "No se encontró la columna de Autores."}
        
    df_limpio = df.dropna(subset=[col_autor])
    
    # 1. Separamos los autores por comas (o punto y coma) convirtiéndolos en listas.
    autores_en_listas = df_limpio[col_autor].astype(str).str.replace(';', ',').str.split(',')
    
    # 2. explode() es la magia: toma la lista de cada celda y crea una fila nueva para cada autor individual.
    autores_individuales = autores_en_listas.explode()
    
    # 3. Limpiamos los espacios en blanco accidentales (ej. " Juan " -> "Juan")
    autores_individuales = autores_individuales.str.strip()
    
    # 4. Filtramos para eliminar posibles espacios vacíos en caso de que hubiera comas dobles (,,)
    autores_individuales = autores_individuales[autores_individuales != ""]
    
    # 5. value_counts() cuenta las repeticiones de cada nombre y los ordena automáticamente. head(10) toma los primeros 10.
    top_10_serie = autores_individuales.value_counts().head(10)
    
    # Convertimos el resultado a una lista de diccionarios (muy fácil de leer para el HTML/Frontend luego)
    # items() nos da pares (nombre_autor, cantidad_publicaciones)
    resultado = [{"autor": autor, "cantidad": int(cantidad)} for autor, cantidad in top_10_serie.items()]
    
    return resultado


#--------------------------------------------------------------------------------------------

def obtener_articulo_sin_citas(df):
 
    col_citas = next((c for c in df.columns if 'cite' in c.lower()), None)
    if col_citas:
        serie = pd.to_numeric(df[col_citas], errors='coerce')
        return int((serie == 0).sum())   # NaN no cuenta como 0
    return 0

def obtener_top_citas_anuales(df, top=10):
    """Calcula el promedio de citas anuales"""
    import datetime
    anio_actual = datetime.datetime.now().year
    
    df = df.copy()
    col_citas = next((c for c in df.columns if 'times cited, wos' in c.lower()), None)
    col_anios = next((c for c in df.columns if 'year' in c.lower() or 'año' in c.lower()), None)

    if col_citas and col_anios:
        df[col_citas] = pd.to_numeric(df[col_citas], errors = 'coerce').fillna(0)
        df[col_anios] = pd.to_numeric(df[col_anios], errors = 'coerce')

        df['antiguedad'] = anio_actual - df[col_anios] + 1
        df['promedio_citas'] = df[col_citas] / df['antiguedad']

        top_df = df.sort_values(by = 'promedio_citas', ascending = False).head(top)
        return top_df[['Title', 'promedio_citas']].to_dict(orient = 'records')
    return []

def calcular_tasa_crecimiento(df):
    col_anio = next((c for c in df.columns if 'year' in c.lower() or 'año' in c.lower()), None)
    if not col_anio:
        return []
    conteo_anual = df[col_anio].value_counts().sort_index()
    tasa = conteo_anual.pct_change()*100

    resultado = []
    for anio, valor in tasa.items():
        resultado.append({
            "año": int(anio),
            "crecimiento": round(valor, 2) if pd.notnull(valor) else 0 
        })
    return resultado

def distribucion_idiomas(df):
    col_idioma = next((c for c in df.columns if 'lang' in c.lower() or 'idioma' in c.lower()), None)
    if not col_idioma:
        return {}
    distribucion = df[col_idioma].value_counts().to_dict()
    return distribucion
#--------------------------------------------------------------------------------------------
##Exportación de Docs

def excel_descargar(df):
    """
    Convierte un Dataframe en un archivo Excel en memoria (buffer)
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine = 'openpyxl') as writer:
        df.to_excel(writer, index = False, sheet_name = 'Resultados_Bibliometricos')
    output.seek(0)
    return output

def word_descargar(df, titulo = "Reporte de Análisis"):
    """Crea un documento de Word con una tabla basada en el Dataframe"""

    doc = Document()
    doc.add_heading(titulo, 0)
    df_preview = df.head(50)
    table = doc.add_table(rows = 1, cols = len(df_preview.columns))
    table.style = 'Table Grid'

    hdr_cells = table.rows[0].cells
    for i, column in enumerate(df_preview.columns):
        hdr_cells[i].text = str(column)
    
    for _, row in df_preview.iterrows():
        row_cells = table.add_row().cells
        for i, value in enumerate(row):
            row_cells[i].text = str(value)

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output
#--------------------------------------------------------------------------------------------
def distribucion_documentos(df):
    col_tipo = next(
        (c for c in df.columns if 'document type' in c.lower() or 'type' in c.lower()),
        None
    )                                                   
    if col_tipo:
        return df[col_tipo].value_counts().to_dict()
    return {"error": "Columna no encontrada"}

def calcular_h_index(df):
    col_citas = next((c for c in df.columns if 'cite' in c.lower()), None)  
    if col_citas is None:
        return 0
    citas = df[col_citas].fillna(0).astype(int).sort_values(ascending=False).tolist()
    h = 0
    for i, n_citas in enumerate(citas):
        if n_citas >= i + 1:
            h = i + 1
        else:
            break
    return h

def identificar_tendencias(df):
    try:
        col_citas = next((c for c in df.columns if 'cite' in c.lower()), None)   
        col_anio  = next((c for c in df.columns if 'year' in c.lower()), None)   

        if col_citas is None or col_anio is None:
            return []

        df = df.copy()
        anio_actual = datetime.datetime.now().year                              

        df['Edad'] = (anio_actual - pd.to_numeric(df[col_anio], errors='coerce')).clip(lower=1)
        df['Crecimiento'] = pd.to_numeric(df[col_citas], errors='coerce').fillna(0) / df['Edad']

        cols = [c for c in ['Title', 'Authors', 'Crecimiento'] if c in df.columns]
        top = df.sort_values(by='Crecimiento', ascending=False).head(5)
        return top[cols].to_dict(orient='records')
    except Exception as e:
        return {"error": str(e)}
    
                              

def generar_grafo_palabras(df):
    col_kw = next(
        (c for c in df.columns if 'keyword' in c.lower()),
        None
    )                                                   #  detecta dinámicamente 
    if col_kw is None:
        return {"nodes": [], "edges": []}

    G = nx.Graph()
    keywords_list = df[col_kw].dropna().str.split(';')

    for tags in keywords_list:
        tags = [t.strip().lower() for t in tags if t.strip()]
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                if G.has_edge(tags[i], tags[j]):
                    G[tags[i]][tags[j]]['weight'] += 1
                else:
                    G.add_edge(tags[i], tags[j], weight=1)

    nodes = [{"id": node, "size": G.degree(node)} for node in G.nodes()]      
    edges = [{"source": u, "target": v, "value": d['weight']} for u, v, d in G.edges(data=True)]
    return {"nodes": nodes, "edges": edges}