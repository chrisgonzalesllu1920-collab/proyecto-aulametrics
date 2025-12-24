import streamlit as st
import analysis_core
import plotly.express as px
import xlsxwriter
import pptx_generator


def evaluacion_page(asistente):
    """
    Controlador principal del Sistema de Evaluación.
    Maneja la carga de archivos y la visualización de resultados.
    """
    # Verificamos si hay datos cargados en el estado de la sesión
    if not st.session_state.get('df_cargado', False):
        st.header("📊 Sistema de Evaluación")
        st.info("Para comenzar, sube tu registro de notas (Excel).")
        
        # IMPORTANTE: Aquí llamamos a la función de carga.
        # Como configurar_uploader probablemente esté en app.py o sea una función auxiliar,
        # asegúrate de que sea accesible o impórtala si la mueves a este módulo.
        from app import configurar_uploader 
        configurar_uploader()
        
    else:
        # B) Si YA hay datos, mostramos el panel con pestañas internas
        tab_global, tab_individual = st.tabs(["🌎 Vista Global", "👤 Vista por Estudiante"])
        
        with tab_global:
            st.subheader("Panorama General del Aula")
            # Obtenemos los datos necesarios desde el session_state
            info_areas = st.session_state.get('info_areas')
            
            # Llamamos a la función de análisis (debe estar disponible en el scope o importada)
            from app import mostrar_analisis_general
            mostrar_analisis_general(info_areas)
            
        with tab_individual:
            st.subheader("Libreta Individual")
            # Obtenemos los datos necesarios
            df = st.session_state.get('df')
            df_config = st.session_state.get('df_config')
            info_areas = st.session_state.get('info_areas')
            
            # Llamamos a la función de análisis individual
            from app import mostrar_analisis_por_estudiante
            mostrar_analisis_por_estudiante(df, df_config, info_areas)


# =========================================================================
# === FUNCIÓN (TAB 2: ANÁLISIS POR ESTUDIANTE) - v5.0 FINAL CON WORD ===
# =========================================================================
def mostrar_analisis_por_estudiante(df_first, df_config, info_areas):
    """
    Muestra el perfil INTEGRAL y permite descargar INFORME WORD.
    """
    st.markdown("---")
    st.header("🧑‍🎓 Perfil Integral del Estudiante")
    
    if 'all_dataframes' not in st.session_state or not st.session_state.all_dataframes:
        st.warning("⚠️ No se han cargado datos. Sube un archivo en la Pestaña 1.")
        return

    all_dfs = st.session_state.all_dataframes
    
    # 1. DETECCIÓN DE COLUMNA
    posibles_nombres = [
        "Estudiante", "ESTUDIANTE", "APELLIDOS Y NOMBRES", "Apellidos y Nombres", 
        "ALUMNO", "Alumno", "Nombres y Apellidos", "Nombre Completo", 
        "Nombres", "NOMBRES"
    ]
    
    first_sheet_name = next(iter(all_dfs))
    df_base = all_dfs[first_sheet_name]
    
    col_nombre = None
    for col in df_base.columns:
        if str(col).strip() in posibles_nombres:
            col_nombre = col
            break
    
    if not col_nombre:
        st.error(f"❌ No encontramos la columna de nombres en la hoja '{first_sheet_name}'.")
        return

    # 2. SELECTOR
    lista_estudiantes = df_base[col_nombre].dropna().unique()
    estudiante_sel = st.selectbox("🔍 Busca al estudiante:", options=lista_estudiantes, index=None, placeholder="Escribe nombre...")

    if estudiante_sel:
        st.divider()
        st.subheader(f"📊 Reporte Global: {estudiante_sel}")
        
        # --- 3. BARRIDO CON MEMORIA DE ÁREAS ---
        total_conteo = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        desglose_areas = {'AD': [], 'A': [], 'B': [], 'C': []}
        areas_analizadas = 0
        
        # Barra de progreso
        my_bar = st.progress(0, text="Analizando áreas...")
        total_sheets = len(all_dfs)
        
        for i, (area_name, df_area) in enumerate(all_dfs.items()):
            my_bar.progress((i + 1) / total_sheets, text=f"Revisando: {area_name}")
            
            c_name_local = None
            for c in df_area.columns:
                if str(c).strip() in posibles_nombres:
                    c_name_local = c
                    break
            
            if c_name_local:
                fila = df_area[df_area[c_name_local] == estudiante_sel]
                if not fila.empty:
                    areas_analizadas += 1
                    vals = [str(v).upper().strip() for v in fila.iloc[0].values]
                    
                    c_ad = vals.count('AD')
                    c_a = vals.count('A')
                    c_b = vals.count('B')
                    c_c = vals.count('C')
                    
                    total_conteo['AD'] += c_ad
                    total_conteo['A'] += c_a
                    total_conteo['B'] += c_b
                    total_conteo['C'] += c_c
                    
                    if c_ad > 0: desglose_areas['AD'].append(f"{area_name} ({c_ad})")
                    if c_a > 0: desglose_areas['A'].append(f"{area_name} ({c_a})")
                    if c_b > 0: desglose_areas['B'].append(f"{area_name} ({c_b})")
                    if c_c > 0: desglose_areas['C'].append(f"{area_name} ({c_c})")

        my_bar.empty()
        
        # --- 4. MOSTRAR RESULTADOS CON DETALLE ---
        suma_total = sum(total_conteo.values())
        
        col_izq, col_der = st.columns([1, 1.5])
        
        with col_izq:
            st.markdown("#### 📈 Detalle por Nivel")
            st.caption(f"Se analizaron {areas_analizadas} áreas en total.")
            
            # AD
            if total_conteo['AD'] > 0:
                with st.expander(f"🏆 Logro Destacado (AD): {total_conteo['AD']}", expanded=False):
                    for area in desglose_areas['AD']: st.markdown(f"- {area}")
            else:
                st.markdown(f"🏆 **AD:** 0")

            # A
            if total_conteo['A'] > 0:
                with st.expander(f"✅ Logro Esperado (A): {total_conteo['A']}", expanded=False):
                    for area in desglose_areas['A']: st.markdown(f"- {area}")
            else:
                st.markdown(f"✅ **A:** 0")

            # B
            if total_conteo['B'] > 0:
                with st.expander(f"⚠️ En Proceso (B): {total_conteo['B']}", expanded=True):
                    st.markdown("**:orange[Áreas a reforzar:]**")
                    for area in desglose_areas['B']: st.markdown(f"- {area}")
            else:
                st.markdown(f"⚠️ **B:** 0")

            # C
            if total_conteo['C'] > 0:
                with st.expander(f"🛑 En Inicio (C): {total_conteo['C']}", expanded=True):
                    st.markdown("**:red[Requiere atención urgente en:]**")
                    for area in desglose_areas['C']: st.markdown(f"- {area}")
            else:
                st.markdown(f"🛑 **C:** 0")

        with col_der:
            if suma_total > 0:
                df_chart = pd.DataFrame({'Nivel': list(total_conteo.keys()), 'Cantidad': list(total_conteo.values())})
                df_chart = df_chart[df_chart['Cantidad'] > 0]
                fig = px.pie(
                    df_chart, values='Cantidad', names='Nivel', 
                    title=f"Mapa de Calor Académico",
                    color='Nivel',
                    color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'},
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin registros de notas.")

        # --- 5. BOTÓN DE DESCARGA DE INFORME (NUEVO) ---
        st.write("---")
        st.write("#### 📥 Opciones de Exportación")
        
        if suma_total > 0:
            # Llamamos a la función que creamos en pedagogical_assistant.py
            # Asumimos que lo tienes importado como 'pedagogical_assistant'
            import pedagogical_assistant # Importación local por seguridad
            
            with st.spinner("Generando informe en Word..."):
                doc_buffer = pedagogical_assistant.generar_reporte_estudiante(
                    estudiante_sel, 
                    total_conteo, 
                    desglose_areas
                )
            
# 1. INSERTAMOS EL ESTILO AZUL (CSS)
            st.markdown("""
                <style>
                div.stDownloadButton > button:first-child {
                    background-color: #0056b3; /* Azul Profesional */
                    color: white;
                    border-radius: 8px;
                    border: 1px solid #004494;
                }
                div.stDownloadButton > button:first-child:hover {
                    background-color: #004494; /* Azul más oscuro al pasar el mouse */
                    color: white;
                    border-color: #002a5c;
                }
                </style>
            """, unsafe_allow_html=True)

            # 2. EL BOTÓN (Sin type="primary")
            st.download_button(
                label="📄 Descargar Informe de Progreso (Word)",
                data=doc_buffer,
                file_name=f"Informe_Progreso_{estudiante_sel}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
                # Nota: He borrado la línea 'type="primary"' para que el azul funcione
            )

# --- FUNCIÓN (Conversión a Excel) - MEJORADA (Colores y Anchos) ---
@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    """
    Convierte DataFrame a formato Excel (xlsx) con formato profesional:
    - Columna de Competencias ancha.
    - Encabezados de colores (AD=Verde, B=Naranja, C=Rojo).
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 1. Escribir las hojas
        workbook = writer.book
        
        # --- Hoja Generalidades ---
        info_sheet = workbook.add_worksheet("Generalidades")
        bold_fmt = workbook.add_format({'bold': True})
        info_sheet.write('A1', 'Área:', bold_fmt)
        info_sheet.write('B1', area_name)
        info_sheet.write('A2', 'Nivel:', bold_fmt)
        info_sheet.write('B2', general_info.get('nivel', 'N/A'))
        info_sheet.write('A3', 'Grado:', bold_fmt)
        info_sheet.write('B3', general_info.get('grado', 'N/A'))
        
        # --- Hoja Frecuencias (Aquí está la magia) ---
        df.to_excel(writer, sheet_name='Frecuencias', startrow=0, startcol=0, index=True)
        worksheet = writer.sheets['Frecuencias']

        # 2. Definir Formatos de Colores (Estilo Pastel Profesional)
        # AD y A (Verdes)
        fmt_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # B (Naranja/Amarillo)
        fmt_orange = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # C (Rojo)
        fmt_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # Cabecera Genérica (Gris)
        fmt_header = workbook.add_format({'bg_color': '#D3D3D3', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # Texto normal (Alineado a la izquierda para competencias)
        fmt_text = workbook.add_format({'text_wrap': True, 'valign': 'vcenter'})

        # 3. Ajustar Ancho de Columnas
        # Columna A (Índice/Competencia): Muy ancha (60) para que entre todo el texto
        worksheet.set_column('A:A', 60, fmt_text)

        # 👇 CAMBIO FINAL: Ancho 9 (Equilibrio perfecto) 👇
        # Aplica a todas las columnas de datos (AD, A, B, C, Porcentajes...)
        worksheet.set_column('B:Z', 9)

        # 4. Pintar los Encabezados con Lógica
        # (Sobrescribimos la fila 0 con los colores correctos)
        
        # Primero pintamos la celda A1 (El título "Competencia")
        worksheet.write(0, 0, "Competencia", fmt_header)

        # Ahora recorremos las columnas de datos (AD, % AD, etc.)
        # df.columns son los nombres. enumerate nos da (0, 'AD'), (1, '% AD')...
        for col_num, value in enumerate(df.columns.values):
            val_str = str(value).upper() # Convertimos a mayúsculas para comparar
            
            # Elegimos el color según la letra
            if "AD" in val_str or ("A" in val_str and "% A" in val_str) or "A (EST.)" in val_str:
                cell_format = fmt_green
            elif "B" in val_str:
                cell_format = fmt_orange
            elif "C" in val_str:
                cell_format = fmt_red
            else:
                cell_format = fmt_header # Por defecto (ej: Total)

            # Escribimos en la fila 0, columna (col_num + 1 porque la A es el índice)
            worksheet.write(0, col_num + 1, value, cell_format)

    return output.getvalue()

# --- FUNCIÓN AUXILIAR: BARRA LATERAL DE NAVEGACIÓN (V3 - CON LOGOUT) ---
def mostrar_sidebar():
    """
    Muestra el menú lateral. Detecta el contexto para mostrar herramientas.
    """
    with st.sidebar:
        # 1. BOTÓN VOLVER (Siempre visible si no estamos en Inicio)
        if st.session_state.get('pagina_actual') != 'Inicio':
            st.divider()
            if st.button("🏠 Volver al Menú Principal", use_container_width=True):
                navegar_a("Inicio")
                st.rerun()

        # 2. BOTÓN DE CARGA DE ARCHIVO (Solo visible en Evaluación)
        if st.session_state.get('pagina_actual') == 'Sistema de Evaluación':
            st.divider()
            if st.button("📂 Subir Nuevo Archivo", use_container_width=True):
                # Limpieza total de datos para permitir nueva carga
                st.session_state.df_cargado = False
                st.session_state.info_areas = None
                st.session_state.all_dataframes = None
                st.session_state.df = None
                # Truco para limpiar el widget de carga
                if 'file_uploader' in st.session_state:
                    del st.session_state['file_uploader']
                st.rerun()

        # 3. BOTÓN CERRAR SESIÓN (NUEVO)
        st.write("") # Espacio vertical
        st.write("") 
        
        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            st.session_state.clear() # Borra toda la memoria
            st.rerun() # Reinicia la app (te llevará al Login)

        # 4. PIE DE PÁGINA
        st.divider()
        
        # [AÑADIENDO LA FECHA DE LANZAMIENTO AQUÍ]
        # Usamos st.info para destacarlo, o st.markdown para un estilo fuerte.
        st.markdown(
            "🚀 **Lanzamiento oficial de Aulametrics:** 01/03/2026", 
            help="Fecha de lanzamiento oficial de la nueva versión de AulaMetrics."
        )
        # También podrías usar: st.text("Fecha de lanzamiento de Aulametrics 01/03/2026")
        
        if st.session_state.get('pagina_actual') == 'Inicio':
            st.info("👋 Selecciona una herramienta del panel.")
        else:
            st.caption(f"📍 Sección: {st.session_state.get('pagina_actual')}")
        
        st.caption("🏫 AulaMetrics v2.0 Beta")
