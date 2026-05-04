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
    posibles_nombres = ['Año', 'Year', 'PY', 'Publication Year', 'año', 'year']
    
    columna_anio = None

    for col in df.columns:
        if col in posibles_nombres:
            columna_anio = col
            break
            
    # Si el archivo no tiene columna de año, devolvemos un error controlado
    if columna_anio is None:
        return {"error": "No se encontró la columna de Año en el dataset."}
    
    # Eliminamos las filas que tengan esa celda vacía
    df_limpio = df.dropna(subset=[columna_anio])
    
    anio_minimo = int(df_limpio[columna_anio].min())
    anio_maximo = int(df_limpio[columna_anio].max())
    
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
    
    # reemplazamos los ; por , y separamos cada nombre
    listas_de_autores = df_limpio[col_autor].astype(str).str.replace(';', ',').str.split(',')
    
    # Metemos a todos los autores y les quitamos los espacios extra
    todos_los_autores = [autor.strip() for sublista in listas_de_autores for autor in sublista if autor.strip()]
    
    #convertimos la lista en un set para eliminar a los repetidos y los contamos
    autores_unicos = len(set(todos_los_autores))

    if autores_unicos == 0:
        return {"error": "No hay autores válidos para calcular el promedio."}
        
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
    df = df.copy()
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
    
    # Separamos los autores por comas y los pasamos a listas.
    autores_en_listas = df_limpio[col_autor].astype(str).str.replace(';', ',').str.split(',')
    
    # Toma la lista de cada celda y crea una fila nueva para cada autor
    autores_individuales = autores_en_listas.explode()
    
    # Limpiamos los espacios en blanco
    autores_individuales = autores_individuales.str.strip()
    
    # Filtramos para eliminar espacios vacíos en caso de que haya 2 comas
    autores_individuales = autores_individuales[autores_individuales != ""]
    
    # cuenta las repeticiones de cada nombre y los ordena y toma los primeros 10
    top_10_serie = autores_individuales.value_counts().head(10)
    
    # Convertimos el resultado a una lista de diccionarios
    resultado = [{"autor": autor, "cantidad": int(cantidad)} for autor, cantidad in top_10_serie.items()]
    
    return resultado

#--------------------------------------------------------------------------------------------

def obtener_top_10_trabajos(df):
    """
    Ordena los trabajos por número de citas y da el top 10
    """
    # Buscamos citas y títulos
    posibles_citas = ['Citas', 'TC', 'Times Cited', 'Citations']
    posibles_titulos = ['Título', 'Title', 'TI', 'Article Title']
    
    col_citas = None
    col_titulo = None
    
    for col in df.columns:
        if col in posibles_citas:
            col_citas = col
        if col in posibles_titulos:
            col_titulo = col
            
    if not col_citas or not col_titulo:
        return [] #Vacío si el archivo no tiene estas columnas
        
    # forzamos conversion de citas a numeros
    df[col_citas] = pd.to_numeric(df[col_citas], errors='coerce').fillna(0)
    
    # Ordenamos de mayor a menor y tomamos top 10
    top_10 = df.sort_values(by=col_citas, ascending=False).head(10)
    
    resultados = []
    for indice, fila in top_10.iterrows():
        resultados.append({
            "titulo": fila[col_titulo],
            "citas": int(fila[col_citas])
        })
        
    return resultados

#--------------------------------------------------------------------------------------------

def contabilizar_coautorias(df):
    """
    Cuenta cuántas publicaciones tienen más de un autor
    """

    posibles_nombres = ['Autor', 'Autores', 'Author', 'Authors', 'AU']
    col_autor = None
    
    for col in df.columns:
        if col in posibles_nombres:
            col_autor = col
            break
            
    if col_autor is None:
        return {"error": "No se encontró la columna de Autores."}
        
    df_limpio = df.dropna(subset=[col_autor])
    total_publicaciones = len(df_limpio)
    
    # Separamos el texto de los autores en arreglos
    listas_de_autores = df_limpio[col_autor].astype(str).str.replace(';', ',').str.split(',')
    
    # Cuenta cuántas listas tienen más de 1 autor válido, cada lista y devuelve true si hay más de 1 autor/elemento
    es_coautorado = listas_de_autores.apply(lambda autores: len([a for a in autores if a.strip()]) > 1)
    
    total_coautoradas = int(es_coautorado.sum())
    porcentaje = 0
    if total_publicaciones > 0:
        porcentaje = (total_coautoradas / total_publicaciones) * 100
        
    return {
        "total_coautoradas": total_coautoradas,
        "porcentaje_coautoria": round(porcentaje, 2),
        "mensaje_formateado": f"{total_coautoradas} publicaciones en colaboración ({round(porcentaje, 2)}%)"
    }

#--------------------------------------------------------------------------------------------

def obtener_articulos_por_universidad(df, nombre_universidad):
    """
    Filtra el dataset para devolver solo los artículos que pertenezcan a una universidad específica.
    """
    # buscamos la columna de afiliación y la de título
    posibles_afiliaciones = ['Afiliación', 'Affiliation', 'C1', 'Institución', 'Institution']
    posibles_titulos = ['Título', 'Title', 'TI', 'Article Title']
    
    col_afil = None
    col_titulo = None
    
    for col in df.columns:
        if col in posibles_afiliaciones:
            col_afil = col
        if col in posibles_titulos:
            col_titulo = col
            
    if not col_afil or not col_titulo:
        return [] # vacío si faltan columnas
        
    # Quitamos filas sin institución
    df_limpio = df.dropna(subset=[col_afil])
    
    # Aplicamos el filtro para ignorar mayúsculas y minúsculas
    filtro = df_limpio[col_afil].str.contains(nombre_universidad, case=False, na=False)
    df_filtrado = df_limpio[filtro]
    
    resultados = []
    for _, fila in df_filtrado.iterrows():
        resultados.append({
            "titulo": fila[col_titulo],
            "afiliacion": fila[col_afil]
        })
        
    return resultados

#--------------------------------------------------------------------------------------------

def calcular_promedio_citas(df):
    """
    Calcula el promedio de citas por artículo sumando todas las citas 
    y dividiéndolas entre el total de publicaciones.
    """
    posibles_citas = ['Citas', 'TC', 'Times Cited', 'Citations']
    col_citas = None
    
    for col in df.columns:
        if col in posibles_citas:
            col_citas = col
            break
            
    if col_citas is None:
        return {"error": "No se encontró la columna de Citas en el dataset."}
        
    # Forzamos la conversión a números
    citas_numericas = pd.to_numeric(df[col_citas], errors='coerce').fillna(0)
    
    # Sumatoria
    total_citas = int(citas_numericas.sum())
    total_articulos = len(df)

    if total_articulos == 0:
        return {"error": "El dataset está vacío."}
        
    promedio = total_citas / total_articulos
    
    return {
        "total_citas": total_citas,
        "promedio_citas": round(promedio, 2),
        "mensaje_formateado": f"Impacto promedio: {round(promedio, 2)} citas por artículo"
    }

#--------------------------------------------------------------------------------------------

def obtener_lista_paises(df):
    """
    Extrae, limpia y cuenta todos los países únicos que participan en los papers
    """
    posibles_nombres = ['País', 'Países', 'Country', 'Countries', 'CU']
    col_pais = None
    
    for col in df.columns:
        if col in posibles_nombres:
            col_pais = col
            break
            
    if col_pais is None:
        return [] # retornamos si no hay nada
        
    df_limpio = df.dropna(subset=[col_pais])
    
    # Separamos los países por si vienen varios en una celda "USA; Mexico; Spain"
    paises_en_listas = df_limpio[col_pais].astype(str).str.replace(';', ',').str.split(',')
    
    # desempaquetamos para que cada país tenga su propia fila
    paises_individuales = paises_en_listas.explode()
    
    # Limpiamos espacios 
    paises_individuales = paises_individuales.str.strip()
    
    # Para eliminar celdas vacías
    paises_individuales = paises_individuales[paises_individuales != ""]
    
    # cuenta cuántas veces se repite cada país y los ordena de mayor a menor
    conteo_paises = paises_individuales.value_counts()
    
    # Convertimos la serie a una lista de diccionarios para enviarla a HTML
    resultados = [{"pais": pais, "cantidad": int(cantidad)} for pais, cantidad in conteo_paises.items()]
    
    return resultados

#--------------------------------------------------------------------------------------------

def obtener_detalle_articulo(df, titulo_buscado):
    """
    Busca un artículo por su título exacto y devuelve todos sus metadatos en formato de diccionario.
    """
    posibles_titulos = ['Título', 'Title', 'TI', 'Article Title']
    col_titulo = None
    
    for col in df.columns:
        if col in posibles_titulos:
            col_titulo = col
            break
            
    if not col_titulo:
        return {"error": "No se encontró la columna de Títulos."}
        
    # Filtramos el dataframe buscando la fila donde el título coincida exactamente y
    # Usamos .astype(str) y .str.strip() por si hay espacios invisibles
    filtro = df[df[col_titulo].astype(str).str.strip() == titulo_buscado.strip()]
    
    if filtro.empty:
        return {"error": "No se encontró ningún artículo con ese título."}
        
    # extraemos la primera fila que coincida (iloc[0]) y la convertimos a un diccionario
    articulo_dict = filtro.iloc[0].to_dict()
    
    # Limpiamos los valores NaN para q  no se vea feo
    for clave, valor in articulo_dict.items():
        if pd.isna(valor):
            articulo_dict[clave] = "No disponible"
            
    return articulo_dict

#--------------------------------------------------------------------------------------------

def calcular_proporcion_citadas(df):
    """
    Calcula el porcentaje de publicaciones que tienen al menos 1 cita.
    (Proporción de Publicaciones Citadas - PCP)
    """
    posibles_citas = ['Citas', 'TC', 'Times Cited', 'Citations']
    col_citas = None
    
    for col in df.columns:
        if col in posibles_citas:
            col_citas = col
            break
            
    if col_citas is None:
        return {"error": "No se encontró la columna de Citas en el dataset."}
        
    # Forzamos la conversión a números y los valores corruptos/vacíos los volvemos 0
    citas_numericas = pd.to_numeric(df[col_citas], errors='coerce').fillna(0)
    
    total_articulos = len(df)
    if total_articulos == 0:
        return {"error": "El dataset está vacío."}
        
    # Magia de Pandas: (citas_numericas > 0) crea una lista de True/False.
    # Al sumarla, cuenta todos los 'True' (artículos con 1 o más citas).
    articulos_citados = int((citas_numericas > 0).sum())
    
    # Calculamos el porcentaje
    proporcion = (articulos_citados / total_articulos) * 100
    
    return {
        "total_articulos": total_articulos,
        "articulos_citados": articulos_citados,
        "proporcion_pcp": round(proporcion, 2),
        "mensaje_formateado": f"{articulos_citados} de {total_articulos} artículos han sido citados ({round(proporcion, 2)}%)"
    }

#--------------------------------------------------------------------------------------------



#--------------------------------------------------------------------------------------------



#--------------------------------------------------------------------------------------------



#--------------------------------------------------------------------------------------------



#--------------------------------------------------------------------------------------------


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
    col_citas = next((c for c in df.columns if 'cite' in c.lower()), None)
    col_anios = next((c for c in df.columns if 'year' in c.lower() or 'año' in c.lower()), None)
    
    # Búsqueda dinámica del título
    col_titulo = next((c for c in df.columns if c.lower() in ['título', 'title', 'ti', 'article title']), 'Title')

    if col_citas and col_anios:
        df[col_citas] = pd.to_numeric(df[col_citas], errors = 'coerce').fillna(0)
        df[col_anios] = pd.to_numeric(df[col_anios], errors = 'coerce')

        df['antiguedad'] = (anio_actual - df[col_anios] + 1).clip(lower=1)
        df['promedio_citas'] = df[col_citas] / df['antiguedad']

        top_df = df.sort_values(by = 'promedio_citas', ascending = False).head(top)
        return top_df[[col_titulo, 'promedio_citas']].to_dict(orient = 'records')
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

        col_titulo = next((c for c in df.columns if c.lower() in ['título', 'title', 'ti', 'article title']), 'Title')

        df['Edad'] = (anio_actual - pd.to_numeric(df[col_anio], errors='coerce')).clip(lower=1)
        df['Crecimiento'] = pd.to_numeric(df[col_citas], errors='coerce').fillna(0) / df['Edad']

        cols = [c for c in [col_titulo, 'Authors', 'Crecimiento'] if c in df.columns]
        top = df.sort_values(by='Crecimiento', ascending=False).head(5)
        return top[cols].to_dict(orient='records')
    except Exception as e:
        print(f"Error en identificar_tendencias: {e}")
        return []
    
                              

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