# Cálculos (Top 10, tasas de crecimiento)

import pandas as pd

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