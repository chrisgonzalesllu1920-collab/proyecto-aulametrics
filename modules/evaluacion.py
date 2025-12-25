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
        st.markdown("""
            <div style='text-align: center; padding: 20px;'>
                <h1 style='color: #1E3A8A;'>📊 Sistema de Evaluación</h1>
                <p style='font-size: 1.2rem; color: #64748b;'>Sube tu registro de notas para comenzar el análisis pedagógico.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Llamamos a la función de carga localmente
        configurar_uploader()
        
    else:
        # Si YA hay datos, mostramos el panel con pestañas internas
        tab_global, tab_individual = st.tabs(["🌎 Vista Global del Aula", "👤 Perfil por Estudiante"])
        
        with tab_global:
            st.markdown("### 📊 Panorama General del Aula")
            info_areas = st.session_state.get('info_areas')
            # Función local
            mostrar_analisis_general(info_areas)
            
        with tab_individual:
            # Función local
            # Nota: Recuperamos los datos de session_state para pasarlos si la firma lo requiere
            df = st.session_state.get('df')
            df_config = st.session_state.get('df_config')
            info_areas = st.session_state.get('info_areas')
            mostrar_analisis_por_estudiante(df, df_config, info_areas)

# =========================================================================
# === FUNCIONES DE CARGA Y LOGICA DE NEGOCIO ===
# =========================================================================

def configurar_uploader():
    """Maneja la carga y el procesamiento inicial del archivo Excel."""
    with st.container(border=True):
        archivo_cargado = st.file_uploader("Selecciona el Registro Auxiliar (Formato Excel)", type=['xlsx', 'xls'])
        
        if archivo_cargado is not None:
            with st.spinner('🛠️ Analizando estructura del registro...'):
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
                        st.success("✅ ¡Archivo procesado con éxito!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al procesar el archivo: {str(e)}")

def mostrar_analisis_general(info_areas):
    """Muestra el resumen estadístico con diseño de tabla HTML forzado."""
    if not info_areas:
        st.warning("⚠️ No hay datos de áreas para mostrar.")
        return

    # Estilos CSS para la tabla (Mejorados visualmente)
    st.markdown("""
        <style>
            .tabla-frecuencias { 
                width: 100%; 
                border-collapse: collapse; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 15px 0;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .tabla-frecuencias th, .tabla-frecuencias td { 
                border: 1px solid #e2e8f0; 
                padding: 12px; 
                text-align: center; 
            }
            .tabla-frecuencias th { 
                background-color: #f8fafc; 
                font-weight: bold; 
                color: #1e293b;
            }
            .nivel-ad { background-color: #dcfce7 !important; color: #166534 !important; font-weight: bold; }
            .nivel-a { background-color: #f0fdf4 !important; color: #166534 !important; }
            .nivel-b { background-color: #fef9c3 !important; color: #854d0e !important; }
            .nivel-c { background-color: #fee2e2 !important; color: #991b1b !important; }
            .col-comp { text-align: left !important; background-color: #ffffff; min-width: 280px; font-weight: 500; }
        </style>
    """, unsafe_allow_html=True)

    for area, datos in info_areas.items():
        with st.container(border=True):
            st.markdown(f"#### 📚 Área: {area}")
            
            # Métricas con diseño nativo de Streamlit
            c1, c2, c3, c4 = st.columns(4)
            resumen = datos['resumen_frecuencias']
            c1.metric("Logro (AD)", resumen.get('AD', 0))
            c2.metric("Logro (A)", resumen.get('A', 0))
            c3.metric("En Proceso (B)", resumen.get('B', 0))
            c4.metric("En Inicio (C)", resumen.get('C', 0))

            st.markdown("---")
            st.markdown("##### 📋 Distribución de Niveles por Competencia")
            
            df = datos['df_frecuencias']
            
            # Construcción manual de la tabla HTML
            html_table = '<table class="tabla-frecuencias"><thead><tr>'
            for col in df.columns:
                html_table += f'<th>{col}</th>'
            html_table += '</tr></thead><tbody>'

            for _, row in df.iterrows():
                html_table += '<tr>'
                for i, col in enumerate(df.columns):
                    val = row[col]
                    clase = ""
                    col_name = str(col).upper()
                    
                    if i == 0: clase = "col-comp"
                    elif 'AD' in col_name: clase = "nivel-ad"
                    elif 'A' in col_name: clase = "nivel-a"
                    elif 'B' in col_name: clase = "nivel-b"
                    elif 'C' in col_name: clase = "nivel-c"
                    
                    html_table += f'<td class="{clase}">{val}</td>'
                html_table += '</tr>'
            
            html_table += '</tbody></table>'
            st.markdown(html_table, unsafe_allow_html=True)
            
            # Botones de descarga - Mantenemos exactamente la lógica de exportación solicitada
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                # Se pasan exactamente los parámetros que el ExcelWriter requiere
                excel_data = convert_df_to_excel(df, area, datos['general_info'])
                st.download_button(
                    label=f"📥 Descargar Excel {area}", 
                    data=excel_data, 
                    file_name=f"Analisis_{area}.xlsx", 
                    key=f"xl_{area}",
                    use_container_width=True
                )
            with col_btn2:
                ppt_buffer = pptx_generator.generate_area_report(area, datos)
                st.download_button(
                    label=f"📊 Descargar PPTX {area}", 
                    data=ppt_buffer, 
                    file_name=f"Reporte_{area}.pptx", 
                    key=f"ppt_{area}",
                    use_container_width=True
                )

# =========================================================================
# === ANALISIS POR ESTUDIANTE ===
# =========================================================================
def mostrar_analisis_por_estudiante(df, df_config, info_areas):
    """Muestra el perfil integral del estudiante."""
    st.markdown("### 🧑‍🎓 Perfil Integral del Estudiante")
    
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
    estudiante_sel = st.selectbox("🔍 Selecciona un estudiante para ver su progreso:", options=lista_estudiantes, index=None, placeholder="Escribe el nombre del alumno...")

    if estudiante_sel:
        st.markdown(f"#### 📈 Reporte Consolidado: {estudiante_sel}")
        
        # --- 3. BARRIDO DE DATOS ---
        total_conteo = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        desglose_areas = {'AD': [], 'A': [], 'B': [], 'C': []}
        areas_analizadas = 0
        
        my_bar = st.progress(0, text="Analizando áreas...")
        total_sheets = len(all_dfs)
        
        for i, (area_name, df_area) in enumerate(all_dfs.items()):
            my_bar.progress((i + 1) / total_sheets, text=f"Procesando {area_name}")
            
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
        
        # --- 4. VISUALIZACIÓN ---
        suma_total = sum(total_conteo.values())
        col_izq, col_der = st.columns([1, 1.5])
        
        with col_izq:
            st.markdown(f"**Competencias evaluadas:** {suma_total}")
            niveles = [
                ('AD', '🏆 Logro Destacado', '#166534', False),
                ('A', '✅ Logro Esperado', '#15803d', False),
                ('B', '⚠️ En Proceso', '#a16207', True),
                ('C', '🛑 En Inicio', '#b91c1c', True)
            ]

            for cod, label, color, expand in niveles:
                cant = total_conteo[cod]
                if cant > 0:
                    with st.expander(f"{label}: {cant}", expanded=expand):
                        if cod in ['B', 'C']:
                            st.markdown(f"<span style='color:{color}; font-weight:bold;'>Necesita reforzamiento en:</span>", unsafe_allow_html=True)
                        for area in desglose_areas[cod]:
                            st.markdown(f"• {area}")
                else:
                    st.caption(f"{label}: 0")

        with col_der:
            if suma_total > 0:
                df_chart = pd.DataFrame({'Nivel': list(total_conteo.keys()), 'Cantidad': list(total_conteo.values())})
                df_chart = df_chart[df_chart['Cantidad'] > 0]
                fig = px.pie(
                    df_chart, values='Cantidad', names='Nivel', 
                    title="Distribución de Calificaciones",
                    color='Nivel',
                    color_discrete_map={'AD': '#166534', 'A': '#22c55e', 'B': '#eab308', 'C': '#ef4444'},
                    hole=0.5
                )
                fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
        
        # --- 5. EXPORTACIÓN WORD ---
        if suma_total > 0:
            with st.container(border=True):
                st.markdown("##### 📄 Informe Psicopedagógico")
                st.info("Genera un documento Word con el análisis de desempeño y recomendaciones para este estudiante.")
                
                if st.button("🛠️ Preparar Informe", use_container_width=True):
                    with st.spinner("Redactando informe..."):
                        doc_buffer = pedagogical_assistant.generar_reporte_estudiante(
                            estudiante_sel, total_conteo, desglose_areas
                        )
                        st.download_button(
                            label="📥 Descargar Informe (Word)",
                            data=doc_buffer,
                            file_name=f"Informe_{estudiante_sel.replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )

# =========================================================================
# === EXPORTACION EXCEL ===
# =========================================================================
@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    """Convierte DataFrame a Excel con formato profesional. Respeta la firma original."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Hoja Generalidades
        info_sheet = workbook.add_worksheet("Generalidades")
        bold_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_name': 'Arial'})
        info_sheet.write('A1', 'Área:', bold_fmt)
        info_sheet.write('B1', area_name)
        info_sheet.write('A2', 'Nivel:', bold_fmt)
        info_sheet.write('B2', general_info.get('nivel', 'N/A'))
        info_sheet.write('A3', 'Grado:', bold_fmt)
        info_sheet.write('B3', general_info.get('grado', 'N/A'))
        
        # Hoja de Frecuencias
        df.to_excel(writer, sheet_name='Frecuencias', index=True)
        worksheet = writer.sheets['Frecuencias']

        # Formatos profesionales
        fmt_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_orange = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_header = workbook.add_format({'bg_color': '#D3D3D3', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_text = workbook.add_format({'text_wrap': True, 'valign': 'vcenter'})

        # Ajuste de columnas
        worksheet.set_column('A:A', 60, fmt_text)
        worksheet.set_column('B:Z', 12)

        # Encabezados con colores condicionales
        worksheet.write(0, 0, "Competencia", fmt_header)
        for col_num, value in enumerate(df.columns.values):
            val_str = str(value).upper()
            cell_format = fmt_header
            if any(x in val_str for x in ["AD", "A (EST.)", "% A"]):
                cell_format = fmt_green
            elif "B" in val_str:
                cell_format = fmt_orange
            elif "C" in val_str:
                cell_format = fmt_red
            
            worksheet.write(0, col_num + 1, value, cell_format)

    return output.getvalue()
