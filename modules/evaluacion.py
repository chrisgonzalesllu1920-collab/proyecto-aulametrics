import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import xlsxwriter
import pptx_generator
import pedagogical_assistant

def evaluacion_page(asistente):
    """
    Controlador principal del Sistema de Evaluación.
    Maneja la carga de archivos y la visualización de resultados.
    """
    # Verificamos si hay datos cargados en el estado de la sesión
    if not st.session_state.get('df_cargado', False):
        st.header("📊 Sistema de Evaluación")
        st.info("Para comenzar, sube tu registro de notas (Excel).")
        
        # Llamamos a la función de carga localmente
        configurar_uploader()
        
    else:
        # Si YA hay datos, mostramos el panel con pestañas internas
        tab_global, tab_individual = st.tabs(["🌎 Vista Global", "👤 Vista por Estudiante"])
        
        with tab_global:
            st.subheader("Panorama General del Aula")
            info_areas = st.session_state.get('info_areas')
            # Función local
            mostrar_analisis_general(info_areas)
            
        with tab_individual:
            # Función local
            mostrar_analisis_por_estudiante()

# =========================================================================
# === FUNCIONES DE CARGA Y LOGICA DE NEGOCIO (ANTES EN APP.PY) ===
# =========================================================================

def configurar_uploader():
    """Maneja la carga y el procesamiento inicial del archivo Excel."""
    archivo_cargado = st.file_uploader("Elige tu archivo Excel", type=['xlsx', 'xls'])
    
    if archivo_cargado is not None:
        with st.spinner('Procesando datos...'):
            try:
                # Procesar el archivo usando el core de análisis
                resultado = analysis_core.procesar_archivo_evaluacion(archivo_cargado)
                
                if resultado:
                    # Guardamos todo en session_state para persistencia
                    st.session_state.df = resultado['df_notas']
                    st.session_state.df_config = resultado['df_config']
                    st.session_state.info_areas = resultado['info_areas']
                    st.session_state.all_dataframes = resultado['all_dataframes']
                    st.session_state.df_cargado = True
                    st.rerun()
            except Exception as e:
                st.error(f"Error al procesar el archivo: {str(e)}")

def mostrar_analisis_general(info_areas):
    """Muestra el resumen estadístico de todas las áreas cargadas."""
    if not info_areas:
        st.warning("No hay datos de áreas para mostrar.")
        return

    for area, datos in info_areas.items():
        with st.container(border=True):
            st.markdown(f"### 📚 Área: {area}")
            
            # Métricas rápidas
            c1, c2, c3, c4 = st.columns(4)
            resumen = datos['resumen_frecuencias']
            
            c1.metric("Logro Destacado (AD)", resumen.get('AD', 0))
            c2.metric("Logro Esperado (A)", resumen.get('A', 0))
            c3.metric("En Proceso (B)", resumen.get('B', 0))
            c4.metric("En Inicio (C)", resumen.get('C', 0))

            # --- NUEVA SECCIÓN: DISEÑO DE TABLA DE FRECUENCIAS ---
            st.markdown("#### 📋 Detalle de Frecuencias por Competencia")
            
            df_frec = datos['df_frecuencias']

            # Función para aplicar colores a las celdas según el encabezado
            def resaltar_niveles(val):
                return 'background-color: #f8f9fa; color: #333; border: 1px solid #dee2e6;'

            # Aplicar estilos específicos por columnas de logros
            styled_df = df_frec.style.set_properties(**{
                'background-color': 'white',
                'color': 'black',
                'border-color': '#e6e6e6'
            })

            # Resaltar columnas según nivel de logro (AD, A, B, C)
            for col in df_frec.columns:
                col_upper = str(col).upper()
                if 'AD' in col_upper:
                    styled_df = styled_df.set_properties(subset=[col], **{'background-color': '#d1e7dd', 'color': '#0f5132', 'font-weight': 'bold'})
                elif 'A' in col_upper:
                    styled_df = styled_df.set_properties(subset=[col], **{'background-color': '#d1e7dd', 'color': '#0f5132'})
                elif 'B' in col_upper:
                    styled_df = styled_df.set_properties(subset=[col], **{'background-color': '#fff3cd', 'color': '#664d03'})
                elif 'C' in col_upper:
                    styled_df = styled_df.set_properties(subset=[col], **{'background-color': '#f8d7da', 'color': '#842029'})

            st.dataframe(styled_df, use_container_width=True)
            # -----------------------------------------------------
            
            # Botones de descarga para esta área específica
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                excel_data = convert_df_to_excel(datos['df_frecuencias'], area, datos['general_info'])
                st.download_button(
                    label=f"📥 Descargar Excel - {area}",
                    data=excel_data,
                    file_name=f"Analisis_{area}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"btn_xl_{area}"
                )
            
            with col_btn2:
                # Generar PPTX (usando el generador importado)
                ppt_buffer = pptx_generator.generate_area_report(area, datos)
                st.download_button(
                    label=f"📊 Descargar PPTX - {area}",
                    data=ppt_buffer,
                    file_name=f"Reporte_{area}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    key=f"btn_ppt_{area}"
                )

# =========================================================================
# === FUNCIÓN (TAB 2: ANÁLISIS POR ESTUDIANTE) ===
# =========================================================================
def mostrar_analisis_por_estudiante(df, df_config, info_areas):
    """
    Muestra el perfil INTEGRAL y permite descargar INFORME WORD.
    Utiliza los datos almacenados en st.session_state.
    """
    st.markdown("---")
    st.header("🧑‍🎓 Perfil Integral del Estudiante")
    
    if 'all_dataframes' not in st.session_state or not st.session_state.all_dataframes:
        st.warning("⚠️ No se han cargado datos. Sube un archivo en la pestaña de carga.")
        return

    all_dfs = st.session_state.all_dataframes
    
    # 1. DETECCIÓN DE COLUMNA DE NOMBRES
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
    lista_estudiantes = sorted(df_base[col_nombre].dropna().unique())
    estudiante_sel = st.selectbox("🔍 Busca al estudiante:", options=lista_estudiantes, index=None, placeholder="Escribe nombre...")

    if estudiante_sel:
        st.divider()
        st.subheader(f"📊 Reporte Global: {estudiante_sel}")
        
        # --- 3. BARRIDO CON MEMORIA DE ÁREAS ---
        total_conteo = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        desglose_areas = {'AD': [], 'A': [], 'B': [], 'C': []}
        areas_analizadas = 0
        
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
                    # Extraer valores y limpiar
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
            st.caption(f"Se analizaron {areas_analizadas} áreas.")
            
            niveles = [
                ('AD', '🏆 Logro Destacado', 'green', False),
                ('A', '✅ Logro Esperado', 'lightgreen', False),
                ('B', '⚠️ En Proceso', 'orange', True),
                ('C', '🛑 En Inicio', 'red', True)
            ]

            for cod, label, color, expand in niveles:
                cant = total_conteo[cod]
                if cant > 0:
                    with st.expander(f"{label}: {cant}", expanded=expand):
                        if cod in ['B', 'C']:
                            st.markdown(f"**:{color}[Reforzar en:]**")
                        for area in desglose_areas[cod]:
                            st.markdown(f"- {area}")
                else:
                    st.markdown(f"{label}: 0")

        with col_der:
            if suma_total > 0:
                df_chart = pd.DataFrame({'Nivel': list(total_conteo.keys()), 'Cantidad': list(total_conteo.values())})
                df_chart = df_chart[df_chart['Cantidad'] > 0]
                fig = px.pie(
                    df_chart, values='Cantidad', names='Nivel', 
                    title=f"Mapa de Calor: {estudiante_sel}",
                    color='Nivel',
                    color_discrete_map={'AD': '#2E7D32', 'A': '#66BB6A', 'B': '#FFA726', 'C': '#EF5350'},
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No se encontraron calificaciones registradas para este estudiante.")

        # --- 5. BOTÓN DE DESCARGA DE INFORME WORD ---
        st.write("---")
        st.write("#### 📥 Opciones de Exportación")
        
        if suma_total > 0:
            with st.spinner("Generando informe pedagógico..."):
                doc_buffer = pedagogical_assistant.generar_reporte_estudiante(
                    estudiante_sel, 
                    total_conteo, 
                    desglose_areas
                )
            
            # Estilo personalizado para el botón
            st.markdown("""
                <style>
                div.stDownloadButton > button:first-child {
                    background-color: #0056b3;
                    color: white;
                    border-radius: 8px;
                    border: 1px solid #004494;
                    font-weight: bold;
                }
                div.stDownloadButton > button:first-child:hover {
                    background-color: #004494;
                    color: white;
                }
                </style>
            """, unsafe_allow_html=True)

            st.download_button(
                label="📄 Descargar Informe de Progreso (Word)",
                data=doc_buffer,
                file_name=f"Informe_Progreso_{estudiante_sel.replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

# --- FUNCIÓN (Conversión a Excel) ---
@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    """Convierte DataFrame a Excel con formato profesional."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Hoja Generalidades
        info_sheet = workbook.add_worksheet("Generalidades")
        bold_fmt = workbook.add_format({'bold': True, 'font_size': 12})
        info_sheet.write('A1', 'Área:', bold_fmt)
        info_sheet.write('B1', area_name)
        info_sheet.write('A2', 'Nivel:', bold_fmt)
        info_sheet.write('B2', general_info.get('nivel', 'N/A'))
        info_sheet.write('A3', 'Grado:', bold_fmt)
        info_sheet.write('B3', general_info.get('grado', 'N/A'))
        
        # Hoja de Frecuencias
        df.to_excel(writer, sheet_name='Frecuencias', index=True)
        worksheet = writer.sheets['Frecuencias']

        # Formatos
        fmt_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_orange = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_header = workbook.add_format({'bg_color': '#D3D3D3', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_text = workbook.add_format({'text_wrap': True, 'valign': 'vcenter'})

        # Ajuste de columnas
        worksheet.set_column('A:A', 60, fmt_text)
        worksheet.set_column('B:Z', 10)

        # Encabezados con colores
        worksheet.write(0, 0, "Competencia", fmt_header)
        for col_num, value in enumerate(df.columns.values):
            val_str = str(value).upper()
            if any(x in val_str for x in ["AD", "A (EST.)", "% A"]):
                cell_format = fmt_green
            elif "B" in val_str:
                cell_format = fmt_orange
            elif "C" in val_str:
                cell_format = fmt_red
            else:
                cell_format = fmt_header
            worksheet.write(0, col_num + 1, value, cell_format)

    return output.getvalue()

