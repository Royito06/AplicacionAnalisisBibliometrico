# Normalización de autores
import re
import unicodedata
import pandas as pd

def normalizar_nombre(texto):
    """Lógica para limpiar un solo nombre de autor."""
    if not texto or not isinstance(texto, str):
        return ""
    
    nombre = unicodedata.normalize('NFKD', texto)
    nombre = "".join([c for c in nombre if not unicodedata.combining(c)])
    
    nombre = nombre.lower()
    nombre = re.sub(r'[^a-z\s,;]', '', nombre)  # esto agrega ; a los caracteres permitidos

    if ',' in nombre:
        partes = nombre.split(',')
        if len(partes) >= 2:
            nombre = f"{partes[1].strip()} {partes[0].strip()}"
    
    nombre = " ".join(nombre.split())
    return nombre.title()

def limpiar_dataset(df):
    """Recorre el DataFrame y normaliza la columna de autores."""
    df = df.copy()
    
    df.columns = [
        col.encode('utf-8').decode('utf-8-sig').strip().strip('"')
        for col in df.columns
    ]
    posibles_nombres = ['Autor', 'Autores', 'Author', 'Authors', 'AU']
    col_autor = next((c for c in df.columns if c in posibles_nombres), None)
    if col_autor:
        df[col_autor] = df[col_autor].apply(
            lambda x: "; ".join([normalizar_nombre(a) for a in str(x).split(';') if a.strip()])
            if pd.notna(x) else ""
        )
    return df