import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.graph_objects as go
import xlsxwriter
import pptx_generator
import pedagogical_assistant

def evaluacion_page(asistente):
    """
    Controlador principal del Sistema de Evaluación.
    Diseño optimizado para proyección y visualización de alta fidelidad.
    """
    if not st.session_state.get('df_cargado', False):
        st.markdown("""
            <div style='text-align: center; padding: 30px;'>
                <h1 style='color: #1E3A8A; font-weight: 800;'>📊 SISTEMA DE EVALUACIÓN</h1>
                <p style='font-size: 1.2rem; color: #64748b;'>Análisis pedagógico avanzado para la toma de decisiones.</p>
            </div>
        """, unsafe_allow_html=True)
        configurar_uploader()
    else:
        tab_global, tab_individual = st.tabs(["🌎 VISTA GLOBAL DEL AULA", "👤 PERFIL POR ESTUDIANTE"])
        
        with tab_global:
            st.markdown("<h3 style='color: #1e293b; margin-bottom:20px;'>📊 Panorama General del Aula</h3>", unsafe_allow_html=True)
            info_areas = st.session_state.get('info_areas')
            mostrar_analisis_general(info_areas)
            
        with tab_individual:
            df = st.session_state.get('df')
            df_config = st.session_state.get('df_config')
            info_areas = st.session_state.get('info_areas')
            mostrar_analisis_por_estudiante(df, df_config, info_areas)

def configurar_uploader():
    """Maneja la carga y el procesamiento inicial del archivo Excel."""
    with st.container(border=True):
        archivo_cargado = st.file_uploader("Selecciona el Registro Auxiliar (Excel)", type=['xlsx', 'xls'])
        if archivo_cargado is not None:
            with st.spinner('🛠️ Analizando estructura...'):
                try:
                    resultado = analysis_core.procesar_archivo_evaluacion(archivo_cargado)
                    if resultado:
                        st.session_state.df = resultado['df_notas']
                        st.session_state.df_config = resultado['df_config']
                        st.session_state.info_areas = resultado['info_areas']
                        st.session_state.all_dataframes = resultado['all_dataframes']
                        st.session_state.df_cargado = True
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def mostrar_analisis_general(info_areas):
    """Muestra el resumen estadístico con gráfico de barras horizontales premium."""
    if not info_areas:
        st.warning("⚠️ No hay datos disponibles.")
        return

    st.markdown("""
        <style>
            .tabla-frecuencias { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 0.9rem; }
            .tabla-frecuencias th { background-color: #f1f5f9; padding: 12px; border: 1px solid #cbd5e1; font-weight: bold; }
            .tabla-frecuencias td { padding: 10px; border: 1px solid #e2e8f0; text-align: center; }
            .nivel-ad { background-color: #dcfce7; color: #166534; font-weight: bold; }
            .nivel-a { background-color: #f0fdf4; color: #166534; }
            .nivel-b { background-color: #fef9c3; color: #854d0e; }
            .nivel-c { background-color: #fee2e2; color: #991b1b; }
            .col-comp { text-align: left !important; min-width: 250px; font-weight: 500; }
        </style>
    """, unsafe_allow_html=True)

    for area, datos in info_areas.items():
        with st.container(border=True):
            st.markdown(f"#### 📚 Área: {area}")
            
            df_bar = datos['df_frecuencias'].copy()
            cols_niveles = [c for c in ['AD', 'A', 'B', 'C'] if c in df_bar.columns]
            
            # --- MEJORA: GRÁFICO DE BARRAS HORIZONTALES ---
            fig_bar = go.Figure()
            colores = {'AD': '#166534', 'A': '#22c55e', 'B': '#eab308', 'C': '#ef4444'}
            
            # Invertimos el orden para que la primera competencia salga arriba
            df_plot = df_bar.iloc[::-1]

            for nivel in cols_niveles:
                fig_bar.add_trace(go.Bar(
                    name=nivel,
                    y=df_plot.index,
                    x=df_plot[nivel],
                    orientation='h',
                    marker_color=colores.get(nivel),
                    text=df_plot[nivel],
                    textposition='inside',
                    textfont=dict(size=14, color='white', family="Arial Black"),
                    hovertemplate=f"Nivel {nivel}: %{{x}} alumnos"
                ))

            fig_bar.update_layout(
                barmode='group',
                height=300 + (len(df_bar) * 50), # Altura dinámica
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=14)),
                xaxis=dict(
                    title="Número de Estudiantes", 
                    gridcolor='rgba(200, 200, 200, 0.2)',
                    dtick=1
                ),
                yaxis=dict(
                    tickfont=dict(size=13, color='#1e293b'),
                    # Truncar nombres si son excesivamente largos para la vista
                    ticktext=[(c[:60] + '...') if len(c) > 60 else c for c in df_plot.index],
                    tickmode='array',
                    tickvals=df_plot.index
                ),
                margin=dict(l=20, r=20, t=60, b=50),
                plot_bgcolor='rgba(255,255,255,0)',
                paper_bgcolor='rgba(255,255,255,0)',
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

            # Tabla HTML
            html_table = '<table class="tabla-frecuencias"><thead><tr>'
            for col in df_bar.columns:
                html_table += f'<th>{col}</th>'
            html_table += '</tr></thead><tbody>'

            for _, row in df_bar.iterrows():
                html_table += '<tr>'
                for i, col in enumerate(df_bar.columns):
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
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                excel_data = convert_df_to_excel(df_bar, area, datos['general_info'])
                st.download_button(label=f"📥 Excel {area}", data=excel_data, file_name=f"Analisis_{area}.xlsx", key=f"xl_{area}", use_container_width=True)
            with col_btn2:
                ppt_buffer = pptx_generator.generate_area_report(area, datos)
                st.download_button(label=f"📊 PPTX {area}", data=ppt_buffer, file_name=f"Reporte_{area}.pptx", key=f"ppt_{area}", use_container_width=True)

def mostrar_analisis_por_estudiante(df, df_config, info_areas):
    """Muestra el perfil integral con limpieza de datos y gráfico premium."""
    st.markdown("### 🧑‍🎓 Perfil Integral del Estudiante")
    
    if 'all_dataframes' not in st.session_state or not st.session_state.all_dataframes:
        st.warning("⚠️ No hay datos cargados.")
        return

    all_dfs = st.session_state.all_dataframes
    posibles_nombres = ["ESTUDIANTE", "APELLIDOS Y NOMBRES", "ALUMNO", "NOMBRES Y APELLIDOS", "NOMBRES"]
    
    first_sheet_name = next(iter(all_dfs))
    df_base = all_dfs[first_sheet_name]
    
    col_nombre = next((col for col in df_base.columns if str(col).strip().upper() in posibles_nombres), None)
    
    if not col_nombre:
        st.error("❌ No se encontró la columna de nombres.")
        return

    lista_cruda = df_base[col_nombre].dropna().unique()
    stop_words = ["NOMBRES", "ESTUDIANTE", "APELLIDOS", "ALUMNO", "NOMBRE COMPLETO", "NOMBRES Y APELLIDOS", "NOMBRE"]
    lista_estudiantes = sorted([est for est in lista_cruda if str(est).strip().upper() not in stop_words])

    estudiante_sel = st.selectbox("🔍 Selecciona un estudiante:", options=lista_estudiantes, index=None, placeholder="Escribe para buscar...")

    if estudiante_sel:
        st.markdown(f"#### 📈 Reporte de Desempeño: {estudiante_sel}")
        
        total_conteo = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        desglose_areas = {'AD': [], 'A': [], 'B': [], 'C': []}
        
        for area_name, df_area in all_dfs.items():
            c_local = next((c for c in df_area.columns if str(c).strip().upper() in posibles_nombres), None)
            if c_local:
                fila = df_area[df_area[c_local] == estudiante_sel]
                if not fila.empty:
                    vals = [str(v).upper().strip() for v in fila.iloc[0].values]
                    for niv in ['AD', 'A', 'B', 'C']:
                        cant = vals.count(niv)
                        total_conteo[niv] += cant
                        if cant > 0: desglose_areas[niv].append(f"{area_name} ({cant})")

        suma_total = sum(total_conteo.values())
        col_izq, col_der = st.columns([1, 1.2])
        
        with col_izq:
            st.metric("Total Competencias", suma_total)
            for cod, label, color, expand in [('AD', '🏆 Logro Destacado', '#166534', False), ('A', '✅ Logro Esperado', '#15803d', False), ('B', '⚠️ En Proceso', '#a16207', True), ('C', '🛑 En Inicio', '#b91c1c', True)]:
                cant = total_conteo[cod]
                if cant > 0:
                    with st.expander(f"{label}: {cant}", expanded=expand):
                        for area in desglose_areas[cod]: st.markdown(f"• {area}")

        with col_der:
            if suma_total > 0:
                labels = [k for k, v in total_conteo.items() if v > 0]
                values = [v for v in total_conteo.values() if v > 0]
                colors = {'AD': '#166534', 'A': '#22c55e', 'B': '#eab308', 'C': '#ef4444'}
                
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=.5,
                    marker=dict(colors=[colors[l] for l in labels], line=dict(color='#FFFFFF', width=2)),
                    textinfo='label+percent',
                    textfont_size=16,
                    pull=[0.05] * len(labels)
                )])
                
                fig.update_layout(
                    title=dict(text="Balance de Calificaciones", font=dict(size=18, family="Arial Black")),
                    annotations=[dict(text=f'Total<br>{suma_total}', x=0.5, y=0.5, font_size=20, showarrow=False, font_family="Arial Black")],
                    showlegend=False,
                    margin=dict(t=50, b=10, l=10, r=10)
                )
                st.plotly_chart(fig, use_container_width=True)

        if suma_total > 0:
            if st.button("🛠️ Generar Informe Psicopedagógico (Word)", use_container_width=True):
                with st.spinner("Redactando..."):
                    doc_buffer = pedagogical_assistant.generar_reporte_estudiante(estudiante_sel, total_conteo, desglose_areas)
                    st.download_button(label="📥 Descargar Informe", data=doc_buffer, file_name=f"Informe_{estudiante_sel.replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        info_sheet = workbook.add_worksheet("Generalidades")
        bold_fmt = workbook.add_format({'bold': True, 'font_size': 12})
        info_sheet.write('A1', 'Área:', bold_fmt); info_sheet.write('B1', area_name)
        info_sheet.write('A2', 'Nivel:', bold_fmt); info_sheet.write('B2', general_info.get('nivel', 'N/A'))
        info_sheet.write('A3', 'Grado:', bold_fmt); info_sheet.write('B3', general_info.get('grado', 'N/A'))
        
        df.to_excel(writer, sheet_name='Frecuencias', index=True)
        worksheet = writer.sheets['Frecuencias']
        
        fmt_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100', 'bold': True, 'border': 1})
        fmt_orange = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700', 'bold': True, 'border': 1})
        fmt_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'bold': True, 'border': 1})
        fmt_header = workbook.add_format({'bg_color': '#D3D3D3', 'bold': True, 'border': 1})
        
        worksheet.set_column('A:A', 60)
        worksheet.write(0, 0, "Competencia", fmt_header)
        for col_num, value in enumerate(df.columns.values):
            v = str(value).upper()
            fmt = fmt_header
            if any(x in v for x in ["AD", "A"]): fmt = fmt_green
            elif "B" in v: fmt = fmt_orange
            elif "C" in v: fmt = fmt_red
            worksheet.write(0, col_num + 1, value, fmt)
            
    return output.getvalue()
