import pandas as pd
import os
import xlrd

def leer_archivo_datos(filepath):
    import pandas as pd
    import os

    try:
        ext = os.path.splitext(filepath)[1].lower()

        df = None

        # ------------------- XLS -------------------
        if ext == '.xls':
            try:
                # Intento normal (pandas decide)
                return pd.read_excel(filepath)
            
            except Exception as e:
                print(" Fallo lectura estándar:", e)

                # Intento con xlrd explícito 
                try:
                    return pd.read_excel(filepath, engine="xlrd")
                except Exception as e2:
                    print(" Fallo con xlrd:", e2)

                    # Último intento: HTML disfrazado 
                    try:
                        print(" Intentando como HTML disfrazado...")
                        tablas = pd.read_html(filepath)
                        if tablas:
                            return tablas[0]
                    except Exception as e3:
                        print(" Tampoco es HTML:", e3)

                    raise ValueError("No se pudo leer el archivo .xls en ningún formato")

        # ------------------- XLSX  -------------------
        elif ext == '.xlsx':
            try:
                df = pd.read_excel(filepath, engine='openpyxl')
            except Exception as e:
                print(" Error leyendo .xlsx:", e)
                raise ValueError("El archivo .xlsx no se pudo leer")

        # ------------------- CSV -------------------
        elif ext == '.csv':
            try:
                df = pd.read_csv(
                    filepath,
                    encoding='utf-8-sig',   # ← utf-8-sig elimina el BOM automáticamente
                    sep=None,
                    engine='python',
                    on_bad_lines='skip'
                )
            except Exception as e:
                print(" Error leyendo CSV:", e)
                raise ValueError("El archivo CSV no se pudo leer")

        else:
            raise ValueError(f"Formato no soportado: {ext}")

        # ------------------- LIMPIEZA CLAVE  -------------------
        if df is not None:
            # Quitar espacios invisibles en nombres de columnas
            df.columns = df.columns.str.strip()

            # Eliminar columnas completamente vacías
            df = df.dropna(axis=1, how='all')

            # Eliminar filas completamente vacías
            df = df.dropna(how='all')

            print("✅ Columnas detectadas:", df.columns.tolist())
            print(df.head(2))

            return df

        return None

    except Exception as e:
        print(" ERROR LEYENDO ARCHIVO:", e)
        return None