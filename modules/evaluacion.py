import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter
import pptx_generator
import pedagogical_assistant

def evaluacion_page(asistente):
    """
    Controlador principal del Sistema de Evaluación.
    Maneja la carga de archivos y la visualización de resultados con diseño Premium.
    """
    if not st.session_state.get('df_cargado', False):
        st.markdown("""
            <div style='text-align: center; padding: 40px 20px;'>
                <h1 style='color: #1e3a8a; font-size: 2.8rem; font-weight: 800; margin-bottom: 10px;'>📊 Sistema de Evaluación</h1>
                <p style='font-size: 1.3rem; color: #64748b; max-width: 700px; margin: 0 auto;'>
                    Análisis pedagógico inteligente: transforma tus registros de notas en decisiones estratégicas.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        configurar_uploader()
        
    else:
        # Pestañas con estilo mejorado
        tab_global, tab_individual = st.tabs(["🌎 Vista Global del Aula", "👤 Perfil por Estudiante"])
        
        with tab_global:
            st.markdown("<h3 style='color: #1e293b; padding-top: 10px;'>📊 Panorama General del Aula</h3>", unsafe_allow_html=True)
            info_areas = st.session_state.get('info_areas')
            mostrar_analisis_general(info_areas)
            
        with tab_individual:
            df = st.session_state.get('df')
            df_config = st.session_state.get('df_config')
            info_areas = st.session_state.get('info_areas')
            mostrar_analisis_por_estudiante(df, df_config, info_areas)

# =========================================================================
# === FUNCIONES DE CARGA Y LOGICA DE NEGOCIO ===
# =========================================================================

def configurar_uploader():
    """Maneja la carga y el procesamiento inicial del archivo Excel."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<p style='text-align:center; font-weight:600;'>Subir Registro Auxiliar</p>", unsafe_allow_html=True)
            archivo_cargado = st.file_uploader("", type=['xlsx', 'xls'])
            
            if archivo_cargado is not None:
                with st.spinner('🛠️ Analizando estructura del registro...'):
                    try:
                        resultado = analysis_core.procesar_archivo_evaluacion(archivo_cargado)
                        
                        if resultado:
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
    """Muestra el resumen estadístico con diseño WOW."""
    if not info_areas:
        st.warning("⚠️ No hay datos de áreas para mostrar.")
        return

    # --- CSS PREMIUM PARA TABLAS ---
    st.markdown("""
        <style>
            .container-tabla {
                background: white;
                border-radius: 15px;
                padding: 2px;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                margin: 20px 0;
            }
            .tabla-frecuencias { 
                width: 100%; 
                border-collapse: separate; 
                border-spacing: 0;
                font-family: 'Inter', sans-serif; 
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid #e2e8f0;
            }
            .tabla-frecuencias th { 
                background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); 
                padding: 16px; 
                font-weight: 700; 
                color: #475569;
                text-transform: uppercase;
                font-size: 0.8rem;
                letter-spacing: 0.05em;
                border-bottom: 2px solid #e2e8f0;
                text-align: center;
            }
            .tabla-frecuencias td { 
                padding: 14px; 
                text-align: center; 
                border-bottom: 1px solid #f1f5f9;
                color: #1e293b;
                font-size: 0.95rem;
            }
            .nivel-ad { background-color: #ecfdf5 !important; color: #065f46 !important; font-weight: bold; border: 1px solid #bef264 !important; }
            .nivel-a { background-color: #f0fdf4 !important; color: #166534 !important; }
            .nivel-b { background-color: #fffbeb !important; color: #92400e !important; }
            .nivel-c { background-color: #fef2f2 !important; color: #991b1b !important; }
            .col-comp { text-align: left !important; background-color: #ffffff; min-width: 320px; font-weight: 600; color: #0f172a; }
            
            /* Efecto Hover */
            .tabla-frecuencias tr:hover td { background-color: #f8fafc; transition: 0.2s; }
        </style>
    """, unsafe_allow_html=True)

    for area, datos in info_areas.items():
        with st.container(border=True):
            st.markdown(f"<h3 style='color:#1e3a8a; border-left: 5px solid #1e3a8a; padding-left:15px;'>📚 Área: {area}</h3>", unsafe_allow_html=True)
            
            # Métricas en Cards Modernas
            resumen = datos['resumen_frecuencias']
            m_ad, m_a, m_b, m_c = st.columns(4)
            
            metrics = [
                (m_ad, "Logro (AD)", resumen.get('AD', 0), "#dcfce7", "#166534"),
                (m_a, "Logro (A)", resumen.get('A', 0), "#f0fdf4", "#166534"),
                (m_b, "Proceso (B)", resumen.get('B', 0), "#fef9c3", "#854d0e"),
                (m_c, "Inicio (C)", resumen.get('C', 0), "#fee2e2", "#991b1b")
            ]
            
            for col, label, val, bg, txt in metrics:
                col.markdown(f"""
                    <div style='background:{bg}; padding:15px; border-radius:12px; text-align:center; border: 1px solid rgba(0,0,0,0.05);'>
                        <p style='margin:0; font-size:0.8rem; font-weight:bold; color:{txt};'>{label}</p>
                        <p style='margin:0; font-size:1.8rem; font-weight:800; color:{txt};'>{val}</p>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- GRÁFICO DE BARRAS WOW ---
            df_frec = datos['df_frecuencias']
            
            fig_bar = px.bar(
                df_frec, 
                x=df_frec.index, 
                y=[c for c in df_frec.columns if c in ['AD', 'A', 'B', 'C']],
                title=f"Distribución de Niveles - {area}",
                color_discrete_map={'AD': '#059669', 'A': '#10b981', 'B': '#f59e0b', 'C': '#ef4444'},
                barmode='group',
                text_auto=True
            )
            
            fig_bar.update_layout(
                plot_bgcolor='white',
                font_family="Inter",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=60, b=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("##### 📋 Tabla Detallada de Competencias")
            
            # Construcción de Tabla HTML Premium
            html_table = '<div class="container-tabla"><table class="tabla-frecuencias"><thead><tr>'
            for col in df_frec.columns:
                html_table += f'<th>{col}</th>'
            html_table += '</tr></thead><tbody>'

            for _, row in df_frec.iterrows():
                html_table += '<tr>'
                for i, col in enumerate(df_frec.columns):
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
            
            html_table += '</tbody></table></div>'
            st.markdown(html_table, unsafe_allow_html=True)
            
            # Exportación
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                excel_data = convert_df_to_excel(df_frec, area, datos['general_info'])
                st.download_button(label=f"📥 Descargar Excel {area}", data=excel_data, file_name=f"Analisis_{area}.xlsx", key=f"xl_{area}", use_container_width=True)
            with col_btn2:
                ppt_buffer = pptx_generator.generate_area_report(area, datos)
                st.download_button(label=f"📊 Descargar PPTX {area}", data=ppt_buffer, file_name=f"Reporte_{area}.pptx", key=f"ppt_{area}", use_container_width=True)

# =========================================================================
# === ANALISIS POR ESTUDIANTE ===
# =========================================================================
def mostrar_analisis_por_estudiante(df, df_config, info_areas):
    """Muestra el perfil integral del estudiante con Gráfico de Anillos Optimizado."""
    st.markdown("### 🧑‍🎓 Perfil Integral del Estudiante")
    
    if 'all_dataframes' not in st.session_state or not st.session_state.all_dataframes:
        st.warning("⚠️ No se han cargado datos.")
        return

    all_dfs = st.session_state.all_dataframes
    
    # 1. DETECCIÓN DE COLUMNA DE NOMBRES
    posibles_nombres = ["Estudiante", "ESTUDIANTE", "APELLIDOS Y NOMBRES", "Apellidos y Nombres", "ALUMNO", "Alumno", "Nombres y Apellidos", "Nombre Completo", "Nombres", "NOMBRES"]
    
    first_sheet_name = next(iter(all_dfs))
    df_base = all_dfs[first_sheet_name]
    
    col_nombre = None
    for col in df_base.columns:
        if str(col).strip() in posibles_nombres:
            col_nombre = col
            break
    
    if not col_nombre:
        st.error(f"❌ No encontramos la columna de nombres en '{first_sheet_name}'.")
        return

    # 2. SELECTOR
    lista_estudiantes = sorted(df_base[col_nombre].dropna().unique())
    estudiante_sel = st.selectbox("🔍 Selecciona un estudiante:", options=lista_estudiantes, index=None, placeholder="Escribe el nombre...")

    if estudiante_sel:
        st.markdown(f"#### 📈 Reporte Consolidado: {estudiante_sel}")
        
        total_conteo = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        desglose_areas = {'AD': [], 'A': [], 'B': [], 'C': []}
        
        # 3. Barrido de datos (Optimizado)
        for area_name, df_area in all_dfs.items():
            c_name_local = next((c for c in df_area.columns if str(c).strip() in posibles_nombres), None)
            
            if c_name_local:
                fila = df_area[df_area[c_name_local] == estudiante_sel]
                if not fila.empty:
                    vals = [str(v).upper().strip() for v in fila.iloc[0].values]
                    for niv in ['AD', 'A', 'B', 'C']:
                        count = vals.count(niv)
                        total_conteo[niv] += count
                        if count > 0: desglose_areas[niv].append(f"{area_name} ({count})")

        # 4. VISUALIZACIÓN
        suma_total = sum(total_conteo.values())
        col_izq, col_der = st.columns([1, 1.2])
        
        with col_izq:
            st.markdown(f"**Competencias evaluadas:** <span style='font-size:1.5rem; font-weight:800;'>{suma_total}</span>", unsafe_allow_html=True)
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
                            st.markdown(f"<span style='color:{color}; font-weight:bold;'>Reforzar en:</span>", unsafe_allow_html=True)
                        for area in desglose_areas[cod]:
                            st.markdown(f"• {area}")
                else:
                    st.caption(f"{label}: 0")

        with col_der:
            if suma_total > 0:
                # GRÁFICO DE ANILLOS WOW - ETIQUETAS GRANDES
                fig = go.Figure(data=[go.Pie(
                    labels=list(total_conteo.keys()), 
                    values=list(total_conteo.values()), 
                    hole=.6,
                    marker=dict(colors=['#059669', '#10b981', '#f59e0b', '#ef4444']),
                    textinfo='percent+label',
                    textfont_size=16, # TEXTO MUCHO MÁS GRANDE
                    insidetextorientation='horizontal'
                )])
                
                fig.update_layout(
                    annotations=[dict(text=f"CALIDAD<br>EDUCATIVA", x=0.5, y=0.5, font_size=18, showarrow=False, font_family="Inter")],
                    showlegend=False,
                    margin=dict(t=20, b=20, l=10, r=10),
                    height=450
                )
                st.plotly_chart(fig, use_container_width=True)

        # 5. EXPORTACIÓN WORD
        if suma_total > 0:
            with st.container(border=True):
                st.markdown("##### 📄 Informe Psicopedagógico")
                if st.button("🛠️ Preparar Informe Profesional", use_container_width=True):
                    with st.spinner("Redactando informe..."):
                        doc_buffer = pedagogical_assistant.generar_reporte_estudiante(estudiante_sel, total_conteo, desglose_areas)
                        st.download_button(label="📥 Descargar Informe (Word)", data=doc_buffer, file_name=f"Informe_{estudiante_sel.replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

# =========================================================================
# === EXPORTACION EXCEL ===
# =========================================================================
@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    """Exportación con formato profesional intacto."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        info_sheet = workbook.add_worksheet("Generalidades")
        bold_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_name': 'Arial'})
        info_sheet.write('A1', 'Área:', bold_fmt)
        info_sheet.write('B1', area_name)
        info_sheet.write('A2', 'Nivel:', bold_fmt)
        info_sheet.write('B2', general_info.get('nivel', 'N/A'))
        info_sheet.write('A3', 'Grado:', bold_fmt)
        info_sheet.write('B3', general_info.get('grado', 'N/A'))
        
        df.to_excel(writer, sheet_name='Frecuencias', index=True)
        worksheet = writer.sheets['Frecuencias']

        fmt_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_orange = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_header = workbook.add_format({'bg_color': '#D3D3D3', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_text = workbook.add_format({'text_wrap': True, 'valign': 'vcenter'})

        worksheet.set_column('A:A', 60, fmt_text)
        worksheet.set_column('B:Z', 12)

        worksheet.write(0, 0, "Competencia", fmt_header)
        for col_num, value in enumerate(df.columns.values):
            val_str = str(value).upper()
            cell_format = fmt_header
            if any(x in val_str for x in ["AD", "A (EST.)", "% A"]): cell_format = fmt_green
            elif "B" in val_str: cell_format = fmt_orange
            elif "C" in val_str: cell_format = fmt_red
            worksheet.write(0, col_num + 1, value, cell_format)

    return output.getvalue()
