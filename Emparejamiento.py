import streamlit as st
import pandas as pd
from thefuzz import process

st.title("Emparejamiento de Stock 📦")
st.write("Arrastrá y soltá tus planillas para hacer el cruce de datos.")

# 1. Creamos las "cajas" en la web para que subas los archivos en el momento
archivo_costos = st.file_uploader("Subí la planilla de Tiendanube (Costos)", type=['csv'])
archivo_detalle = st.file_uploader("Subí la planilla de Detalle (Hoja1)", type=['csv'])

# El código solo avanza si subiste ambos archivos
if archivo_costos is not None and archivo_detalle is not None:
    st.info("Procesando y cruzando los datos. Dame unos segundos...")

    # Leemos los archivos que acabás de subir
    df_costos = pd.read_csv(archivo_costos)
    df_detalle = pd.read_csv(archivo_detalle)

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

    # Exportamos el archivo a formato CSV en la memoria
    csv_salida = df_final.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

    st.success("¡Listo! El cruce se generó correctamente.")

    # 8. Botón de descarga en la interfaz web
    st.download_button(
        label="📥 Descargar Excel Cruzado",
        data=csv_salida,
        file_name="Cruce_Stock_Final.csv",
        mime="text/csv"
    )
