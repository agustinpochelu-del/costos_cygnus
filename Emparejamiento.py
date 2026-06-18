import streamlit as st
import pandas as pd
from thefuzz import process

st.title("Emparejamiento de Stock 📦")
st.write("Procesando y cruzando los datos. Dame unos segundos...")

# 1. Cargar los archivos 
# (Asumimos que están en la misma carpeta que el script en tu repositorio)
df_costos = pd.read_csv('Costos.csv')
df_detalle = pd.read_csv('Hoja1.csv')

# 2. Diccionario de equivalencias para normalizar las medidas
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

# 3. Crear una columna de búsqueda unificada en ambas tablas
df_costos['Texto_Busqueda'] = df_costos['Nombre del Producto'].astype(str) + " " + df_costos['Nombre de Variante'].astype(str)
df_detalle['Texto_Busqueda'] = df_detalle['nombre en la web'].astype(str) + " " + df_detalle['Medida_Norm'].astype(str) + " " + df_detalle['Detalle'].astype(str)

# 4. Función de coincidencia difusa (Fuzzy Matching)
# Usamos @st.cache_data para que la web no recalcule todo si apretás un botón por error
@st.cache_data 
def buscar_mejor_coincidencia(texto, lista_opciones):
    match, score, indice = process.extractOne(texto, lista_opciones)
    if score >= 75:  # Umbral de similitud al 75%
        return match
    return None

opciones_tiendanube = df_costos['Texto_Busqueda'].dropna().tolist()

# 5. Ejecutar el cruce masivo
df_detalle['Match_Tiendanube'] = df_detalle['Texto_Busqueda'].apply(
    lambda x: buscar_mejor_coincidencia(x, opciones_tiendanube)
)

# 6. Unir ambas tablas en base al mejor match encontrado
df_final = pd.merge(df_detalle, df_costos, left_on='Match_Tiendanube', right_on='Texto_Busqueda', how='left')

# 7. Limpiar columnas de ayuda
df_final = df_final.drop(columns=['Texto_Busqueda_x', 'Texto_Busqueda_y', 'Medida_Norm', 'Match_Tiendanube'])
nombre_archivo_salida = 'Cruce_Stock_Final.csv'

# Exportamos el archivo internamente en el servidor
df_final.to_csv(nombre_archivo_salida, index=False, encoding='utf-8-sig')

st.success("¡Listo! El cruce se generó correctamente.")

# 8. Botón de descarga en la interfaz web
with open(nombre_archivo_salida, "rb") as file:
    st.download_button(
            label="📥 Descargar Excel Cruzado",
            data=file,
            file_name="Cruce_Stock_Final.csv",
            mime="text/csv"
          )
