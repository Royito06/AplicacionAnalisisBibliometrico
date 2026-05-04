import re
import unicodedata
import pandas as pd

def normalizar_autor(texto):
    """Limpia y estandariza nombres de autores."""
    if not texto or not isinstance(texto, str): 
        return ""
    nombre = unicodedata.normalize('NFKD', texto)
    nombre = "".join([c for c in nombre if not unicodedata.combining(c)])
    nombre = nombre.lower()
    nombre = re.sub(r'[^a-z\s,;]', '', nombre)
    
    if ',' in nombre and ';' not in nombre:
        partes = nombre.split(',')
        if len(partes) >= 2:
            nombre = f"{partes[1].strip()} {partes[0].strip()}"
    
    return " ".join(nombre.split()).title()

def limpiar_dataset(df):
    """Aplica la limpieza a la columna de autores detectada."""
    df = df.copy()
    posibles = ['autor', 'autores', 'author', 'authors', 'au']
    col_autor = next((c for c in df.columns if any(p in c.lower() for p in posibles)), None)
    
    if col_autor:
        df[col_autor] = df[col_autor].apply(
            lambda x: "; ".join([normalizar_autor(a) for a in str(x).split(';') if a.strip()]) 
            if pd.notna(x) else ""
        )
    return df