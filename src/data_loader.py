import pandas as pd
import os

def leer_archivo_datos(ruta_archivo):
    """
    Lee un archivo CSV o Excel y devuelve un DataFrame de Pandas.
    """
    extension = os.path.splitext(ruta_archivo)[1].lower()
    try:
        if extension == '.csv':
            df = pd.read_csv(ruta_archivo)
        elif extension in ['.xls', '.xlsx']:
            df = pd.read_excel(ruta_archivo, engine='openpyxl')
        else:
            return None
        return df
    except Exception as e:
        print(f"Error interno: {e}")
        return None