import pandas as pd
import os
import xlrd
"""
def leer_archivo_datos(ruta_archivo):
    
    #Lee un archivo CSV o Excel y devuelve un DataFrame de Pandas.
    
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
        return {"error": "Error interno: {e}"}
    """
    
def leer_archivo_datos(filepath):
    
    try:
        ext = filepath.lower().split('.')[-1]

        if ext == 'xls':
            try:
                df = pd.read_excel(filepath, engine='xlrd')
            except Exception as e:
                print("Fallo como Excel:", e)
                print("Intentando como archivo flexible...")
                df = pd.read_csv(
                    filepath,
                    sep=None,
                    engine='python',
                    encoding='latin1',
                    on_bad_lines='skip',
                    quotechar='"'
                )
        
        elif ext == 'xlsx':
            df = pd.read_excel(filepath, engine='openpyxl')
        
        elif ext == 'csv':
            df = pd.read_csv(filepath, encoding='latin1', on_bad_lines='skip')
        
        else:
            raise ValueError("Formato no soportado")

        if df is None or df.empty:
            print("DataFrame vacío o inválido")
            return None

        # Limpieza básica
        df.columns = [col.strip() for col in df.columns]

        print("Columnas detectadas:", df.columns.tolist())
        print(df.head(2))

        return df
    
    except Exception as e:
        print("ERROR LEYENDO ARCHIVO:", e)
        return None