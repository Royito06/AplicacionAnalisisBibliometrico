import pandas as pd

def lista_paises(df):
    """Extrae y cuenta la frecuencia de países en las afiliaciones."""
    if df is None: return []
    col_pais = next((c for c in df.columns if any(x in c.lower() for x in ['country', 'cu', 'país'])), None)
    
    if col_pais:
        serie = df[col_pais].dropna().astype(str).str.split(';|,').explode().str.strip()
    else:
        col_afil = next((c for c in df.columns if 'affilia' in c.lower()), None)
        serie = df[col_afil].dropna().astype(str).str.split(',').apply(lambda x: x[-1].strip() if x else "") if col_afil else pd.Series([])
    
    conteo = serie[serie != ""].value_counts()
    return [{"pais": p.title(), "cantidad": int(v)} for p, v in conteo.items()]

def top_citados(df):
    """Obtiene los 10 artículos con más citas para el reporte Word."""
    if df is None: return []
    c_citas = next((c for c in df.columns if any(x in c.lower() for x in ['cite', 'tc', 'citas'])), None)
    c_titulo = next((c for c in df.columns if any(x in c.lower() for x in ['title', 'ti', 'título'])), None)
    
    if not c_citas or not c_titulo: return []
    
    df_temp = df.copy()
    df_temp[c_citas] = pd.to_numeric(df_temp[c_citas], errors='coerce').fillna(0)
    top = df_temp.sort_values(by=c_citas, ascending=False).head(10)
    return [{"titulo": str(r[c_titulo]), "citas": int(r[c_citas])} for _, r in top.iterrows()]