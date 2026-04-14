import re 
import unicodedata

def normalizar_autor(no_definido):
    if not no_definido or not isinstance(no_definido, str):
        return ""
    # Quitar acentos
    nombre = unicodedata.normalize('NFKD', no_definido)
    nombre = "".join([c for c in nombre if not unicodedata.combining(c)])
    
    nombre = nombre.lower()
    nombre = re.sub(r'[^a-z\s,]', '', nombre)

    # Lógica de la coma (Apellido, Nombre -> Nombre Apellido)
    if ',' in nombre:
        partes = nombre.split(',')
        if len(partes) >= 2:
            nombre = f"{partes[1].strip()} {partes[0].strip()}"
    
    nombre = " ".join(nombre.split())
    return nombre.title()

# ESTO ES LO QUE HACE QUE SALGA EN LA TERMINAL
autores = [
    "Gálvez Mendoza Alberto",
    "Papá",
    "Gálvez Mendoza, Alberto",
    "alberto galvez mendoza",
    "Mendoza, A. G."
]

print("\n--- INICIANDO NORMALIZACIÓN ---")
print(f"{'Original':<30} | {'Normalizado':<30}")
print("-" * 65)

for autor in autores:
    resultado = normalizar_autor(autor)
    print(f"{autor:<30} | {resultado:<30}")