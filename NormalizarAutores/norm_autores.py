import re 
import unicodedata

def normalizar_autor(no_definido):
    if not no_definido or not isinstance(no_definido, str):
        return ""
    nombre = unicodedata.normalize('NFKD', no_definido)
    nombre = "".join([c for c in nombre if not unicodedata.combining(c)])
    
    nombre = nombre.lower()

    nombre = re.sub(r'[^a-z\s,]', '', nombre)

    if ',' in nombre:
        partes = nombres.split(',')
        nombre = f"{partes[1].strip()} {partes[0].strip()}"
    nombre = " ".join(nombre.split())
    return nombre.title()

#Ejemplo práctico 
autores=[
    "Gálvez Mendoza Alberto",
    "Papá"
]

print(f"{'Original':<30} | {'Normalizando':<30}")
print("-" * 65)

for autor in autores:
    resultado = normalizar_autor(autor)
    print(f"{autor:<30} | {resultado:<30}")