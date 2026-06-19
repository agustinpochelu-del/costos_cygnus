import streamlit as st
import pandas as pd
from rapidfuzz import process
import io

st.title("Emparejamiento de Stock 📦")
st.write("Arrastrá y soltá tus planillas de Excel para hacer el cruce de datos.")

# 1. Creamos los espacios para subir los archivos
archivo_costos = st.file_uploader("Subí la planilla de Tiendanube (Costos)", type=['xlsx', 'xls'])
archivo_detalle = st.file_uploader("Subí la planilla de Detalle (Hoja1)", type=['xlsx', 'xls'])

if archivo_costos is not None and archivo_detalle is not None:
    st.info("Procesando y cruzando los datos. Esto va a ser rapidísimo...")
    barra_progreso = st.progress(0)

    # 2. Leemos los archivos
    df_costos = pd.read_excel(archivo_costos)
    df_detalle = pd.read_excel(archivo_detalle)
    barra_progreso.progress(20)

    # 3. Limpiamos espacios invisibles en los títulos de las columnas
    df_costos.columns = df_costos.columns.str.strip()
    df_detalle.columns = df_detalle.columns.str.strip()

    # Chequeo de seguridad: Confirmar que existan las columnas clave
    columnas_faltantes = False
    if 'Medida' not in df_detalle.columns:
        st.error("🚨 No encontré la columna 'Medida' en la planilla de Detalle.")
        columnas_faltantes = True
    if 'Nombre del Producto' not in df_costos.columns:
        st.error("🚨 No encontré la columna 'Nombre del Producto' en Tiendanube.")
        columnas_faltantes = True

    if not columnas_faltantes:
        
        # 4. Diccionario de equivalencias para normalizar las medidas
        reemplazos_medida = {
            '1 1/2 PL': '1 y 1/2 Plaza',
            '1.5': '1 y 1/2 Plaza',
            '2.5': '2 y 1/2 Plaza',
            'Queen': 'QUEEN SIZE',
            'King': 'KING SIZE',
            'twin': '1 y 1/2 Plaza'
        }

        # Aplicamos el diccionario al detalle
        df_detalle['Medida_Norm'] = df_detalle['Medida'].replace(reemplazos_medida)
        barra_progreso.progress(40)

        # 5. Creamos la columna de búsqueda unificada en ambas tablas
        df_costos['Texto_Busqueda'] = df_costos['Nombre del Producto'].astype(str) + " " + df_costos['Nombre de Variante'].astype(str)
        df_detalle['Texto_Busqueda'] = df_detalle['nombre en la web'].astype(str) + " " + df_detalle['Medida_Norm'].astype(str) + " " + df_detalle['Detalle'].astype(str)

        # 6. SOLUCIÓN A LA MULTIPLICACIÓN: Eliminamos duplicados en la tabla de costos
        # Así evitamos el producto cartesiano al cruzar
        df_costos = df_costos.drop_duplicates(subset=['Texto_Busqueda'])

        # 7. Función de coincidencia difusa (Fuzzy Matching con rapidfuzz)
        def buscar_mejor_coincidencia(texto, lista_opciones):
            resultado = process.extractOne(texto, lista_opciones)
            if resultado:
                match = resultado[0]
                score = resultado[1]
                if score >= 75:  # Umbral de similitud
                    return match
            return None

        # Armamos la lista de opciones y ejecutamos la búsqueda masiva
        opciones_tiendanube = df_costos['Texto_Busqueda'].dropna().tolist()
        barra_progreso.progress(60)

        df_detalle['Match_Tiendanube'] = df_detalle['Texto_Busqueda'].apply(
            lambda x: buscar_mejor_coincidencia(x, opciones_tiendanube)
        )
        barra_progreso.progress(80)

        # 8. Unimos ambas tablas en base al mejor match encontrado
        df_final = pd.merge(df_detalle, df_costos, left_on='Match_Tiendanube', right_on='Texto_Busqueda', how='left')
        
        # 9. Limpiamos las columnas temporales que usamos para buscar
        df_final = df_final.drop(columns=['Texto_Busqueda_x', 'Texto_Busqueda_y', 'Medida_Norm', 'Match_Tiendanube'])

        # 10. Preparamos el Excel final para descargar
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Stock_Cruzado')
        
        excel_salida = buffer.getvalue()
        barra_progreso.progress(100)

        st.success("¡Listo! El cruce se generó perfectamente y sin filas de más.")

        # 11. Mostramos el botón de descarga en la web
        st.download_button(
            label="📥 Descargar Excel Cruzado",
            data=excel_salida,
            file_name="Cruce_Stock_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
