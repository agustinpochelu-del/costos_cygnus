import streamlit as st
import pandas as pd
from thefuzz import process
import io

st.title("Emparejamiento de Stock 📦")
st.write("Arrastrá y soltá tus planillas de Excel para hacer el cruce de datos.")

# 1. Ajustamos para que acepte archivos Excel (.xlsx o .xls)
archivo_costos = st.file_uploader("Subí la planilla de Tiendanube (Costos)", type=['xlsx', 'xls'])
archivo_detalle = st.file_uploader("Subí la planilla de Detalle (Hoja1)", type=['xlsx', 'xls'])

if archivo_costos is not None and archivo_detalle is not None:
    st.info("Procesando y cruzando los datos. Dame unos segundos...")

    # 2. Leemos los archivos con read_excel en vez de read_csv
    df_costos = pd.read_excel(archivo_costos)
    df_detalle = pd.read_excel(archivo_detalle)

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
    df_costos['Texto_Busqueda'] = df_costos['Nombre del Producto'].astype(str) + " " + df_costos['Nombre de Variante'].astype(str)
    df_detalle['Texto_Busqueda'] = df_detalle['nombre en la web'].astype(str) + " " + df_detalle['Medida_Norm'].astype(str) + " " + df_detalle['Detalle'].astype(str)

    # 5. Función de coincidencia difusa (Fuzzy Matching)
    @st.cache_data 
    def buscar_mejor_coincidencia(texto, lista_opciones):
        match, score, indice = process.extractOne(texto, lista_opciones)
        if score >= 75:  # Umbral de similitud al 75%
            return match
        return None

    opciones_tiendanube = df_costos['Texto_Busqueda'].dropna().tolist()

    # 6. Ejecutar el cruce masivo
    df_detalle['Match_Tiendanube'] = df_detalle['Texto_Busqueda'].apply(
        lambda x: buscar_mejor_coincidencia(x, opciones_tiendanube)
    )

    # 7. Unir ambas tablas en base al mejor match encontrado
    df_final = pd.merge(df_detalle, df_costos, left_on='Match_Tiendanube', right_on='Texto_Busqueda', how='left')

    # 8. Limpiar columnas de ayuda
    df_final = df_final.drop(columns=['Texto_Busqueda_x', 'Texto_Busqueda_y', 'Medida_Norm', 'Match_Tiendanube'])

    # 9. Preparar el Excel para descargar usando un buffer de memoria
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Stock_Cruzado')
    
    excel_salida = buffer.getvalue()

    st.success("¡Listo! El cruce se generó correctamente.")

    # 10. Botón de descarga en formato Excel
    st.download_button(
        label="📥 Descargar Excel Cruzado",
        data=excel_salida,
        file_name="Cruce_Stock_Final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
