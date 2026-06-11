# 1. Instalamos la librería necesaria para buscar coincidencias (solo para Colab)
!pip install thefuzz[speedup]

import pandas as pd
from thefuzz import process
from google.colab import files

print("Arrancando el proceso...")

# 2. Cargar los archivos (tienen que estar subidos a la carpeta de la izquierda)
df_costos = pd.read_csv('Costos.csv')
df_detalle = pd.read_csv('Hoja1.csv')

# 3. Diccionario de equivalencias para normalizar las medidas
reemplazos_medida = {
    '1 1/2 PL': '1 y 1/2 Plaza',
    '1.5': '1 y 1/2 Plaza',
    '2.5': '2 y 1/2 Plaza',
    'Queen': 'QUEEN SIZE',
    'King': 'KING SIZE',
    'twin': '1 y 1/2 Plaza'
}

# Normalizamos la columna de medida en el detalle
df_detalle['Medida_Norm'] = df_detalle['Medida'].replace(reemplazos_medida)

# 4. Crear una columna de búsqueda unificada en ambas tablas
# Tiendanube: Producto + Variante
df_costos['Texto_Busqueda'] = df_costos['Nombre del Producto'].astype(str) + " " + df_costos['Nombre de Variante'].astype(str)

# Detalle: Nombre web + Medida normalizada + Detalle
df_detalle['Texto_Busqueda'] = df_detalle['nombre en la web'].astype(str) + " " + df_detalle['Medida_Norm'].astype(str) + " " + df_detalle['Detalle'].astype(str)

# 5. Función de coincidencia difusa (Fuzzy Matching)
def buscar_mejor_coincidencia(texto, lista_opciones):
    match, score, indice = process.extractOne(texto, lista_opciones)
    if score >= 75:  # Umbral de similitud configurado al 75%
        return match
    return None

opciones_tiendanube = df_costos['Texto_Busqueda'].dropna().tolist()

# 6. Ejecutar el cruce masivo
print("Cruzando los datos (esto puede demorar unos segundos)...")
df_detalle['Match_Tiendanube'] = df_detalle['Texto_Busqueda'].apply(
    lambda x: buscar_mejor_coincidencia(x, opciones_tiendanube)
)

# 7. Unir ambas tablas en base al mejor match encontrado
df_final = pd.merge(df_detalle, df_costos, left_on='Match_Tiendanube', right_on='Texto_Busqueda', how='left')

# 8. Limpiar columnas de ayuda y exportar el resultado limpio
df_final = df_final.drop(columns=['Texto_Busqueda_x', 'Texto_Busqueda_y', 'Medida_Norm', 'Match_Tiendanube'])
nombre_archivo_salida = 'Cruce_Stock_Final.csv'
df_final.to_csv(nombre_archivo_salida, index=False, encoding='utf-8-sig')

print("¡Listo! Descargando el archivo final...")

# 9. Descargar el archivo automáticamente a tu computadora
files.download(nombre_archivo_salida)
