import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter
import pedagogical_assistant

# --- CONFIGURACIÓN DE ESTÉTICA POWER BI ---
PBI_BLUE = "#113770"
PBI_LIGHT_BLUE = "#0078D4"
PBI_BG = "#F9FAFB" # Blanco humo más profesional y limpio
PBI_CARD_BG = "#FFFFFF"

# Paleta de colores oficial de Power BI para niveles
COLORS_NIVELES = {
    'AD': '#008450', # Verde oscuro
    'A': '#32CD32',  # Verde lima
    'B': '#FFB900',  # Dorado/Amarillo
    'C': '#E81123'   # Rojo
}

def evaluacion_page(asistente):
    """Punto de entrada compatible con app.py"""
    inject_pbi_css()
    
    if not st.session_state.get('df_cargado', False):
        st.markdown(f"<h1 class='pbi-header'>📊 Dashboard de Evaluación</h1>", unsafe_allow_html=True)
        configurar_uploader()
    else:
        tab_global, tab_individual = st.tabs(["🌎 VISTA GLOBAL DEL AULA", "👤 PERFIL POR ESTUDIANTE"])
        
        with tab_global:
            info_areas = st.session_state.get('info_areas', {})
            mostrar_analisis_general(info_areas)
            
        with tab_individual:
            # Recuperamos los datos de la sesión para la vista individual
            df_first = st.session_state.get('df')
            df_config = st.session_state.get('df_config')
            info_areas = st.session_state.get('info_areas')
            mostrar_analisis_por_estudiante(df_first, df_config, info_areas)

def mostrar_analisis_general(results):
    """Lógica original con diseño avanzado de Power BI"""
    st.markdown(f"<h2 class='pbi-header'>Resultados Consolidados por Área</h2>", unsafe_allow_html=True)

    first_sheet_key = next(iter(results), None)
    general_data = {}
    if first_sheet_key and 'generalidades' in results[first_sheet_key]:
        general_data = results[first_sheet_key]['generalidades']
        st.markdown(f"""
            <div class='pbi-card' style='padding: 10px 20px; border-left: 5px solid {PBI_LIGHT_BLUE}; margin-bottom: 25px;'>
                <span style='color: #666; font-size: 0.8rem;'>CONTEXTO DEL GRUPO</span><br>
                <span style='font-size: 1.1rem; font-weight: bold; color: {PBI_BLUE};'>
                    Nivel {general_data.get('nivel', 'Descon.')} | Grado {general_data.get('grado', 'Descon.')}
                </span>
            </div>
        """, unsafe_allow_html=True)
    
    # Sidebar de Configuración (Power BI Slicer Style)
    with st.sidebar:
        st.markdown(f"<h3 style='color:{PBI_BLUE}; border-bottom: 1px solid #ccc; padding-bottom:5px;'>⚙️ Visualización</h3>", unsafe_allow_html=True)
        chart_options = (
            'Barras (Clásico PBI)', 
            'Anillo (Proporción)', 
            'Mapa de Árbol (Jerarquía)', 
            'Radar de Competencias',
            'Solar (Sunburst)'
        )
        st.session_state.chart_type = st.radio("Seleccionar Visual:", chart_options, key="chart_radio_pbi")
        st.info("Tip: Los gráficos son interactivos. Haz clic en las leyendas para filtrar niveles.")

    tabs = st.tabs([f"📍 {sheet_name}" for sheet_name in results.keys()])

    for i, (sheet_name, result) in enumerate(results.items()):
        with tabs[i]:
            if 'error' in result:
                st.error(f"Error en '{sheet_name}': {result['error']}")
                continue
            
            competencias = result.get('competencias', {})
            if not competencias:
                st.info(f"Sin datos en '{sheet_name}'.")
                continue

            # --- TABLA DE DATOS (ESTILO PBI) ---
            st.markdown("<div class='pbi-card'><b>1. Matriz de Frecuencias de Evaluación</b>", unsafe_allow_html=True)
            data = {'Competencia': [], 'AD (Est.)': [], '% AD': [], 'A (Est.)': [], '% A': [], 'B (Est.)': [], '% B': [], 'C (Est.)': [], '% C': [], 'Total': []}
            
            for col_original_name, comp_data in competencias.items():
                counts = comp_data['conteo_niveles']
                total = comp_data['total_evaluados']
                data['Competencia'].append(comp_data['nombre_limpio'])
                for level in ['AD', 'A', 'B', 'C']:
                    count = counts.get(level, 0)
                    porcentaje = (count / total * 100) if total > 0 else 0
                    data[f'{level} (Est.)'].append(count)
                    data[f'% {level}'].append(f"{porcentaje:.1f}%")
                data['Total'].append(total)
            
            df_table = pd.DataFrame(data).set_index('Competencia')
            st.dataframe(df_table, use_container_width=True)
            
            excel_data = convert_df_to_excel(df_table, sheet_name, general_data)
            st.download_button(label=f"⬇️ Exportar Datos a Excel", data=excel_data, 
                              file_name=f'Reporte_PBI_{sheet_name}.xlsx', key=f'btn_dl_{i}')
            st.markdown("</div>", unsafe_allow_html=True)

            # --- GRÁFICOS INTERACTIVOS ---
            st.markdown(f"<div class='pbi-card'><b>2. Visualización Dinámica: {st.session_state.chart_type}</b>", unsafe_allow_html=True)
            competencia_nombres_limpios = df_table.index.tolist()
            selected_comp = st.selectbox(f"Filtrar por Competencia específica:", options=competencia_nombres_limpios, key=f'sel_{sheet_name}_{i}')

            if selected_comp:
                df_plot = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']].reset_index()
                df_plot.columns = ['Nivel', 'Estudiantes']
                df_plot['Nivel'] = df_plot['Nivel'].str.replace(' (Est.)', '', regex=False)
                
                if st.session_state.chart_type == 'Barras (Clásico PBI)':
                    fig = px.bar(df_plot, x='Nivel', y='Estudiantes', color='Nivel', 
                                 text='Estudiantes', color_discrete_map=COLORS_NIVELES)
                    fig.update_traces(textposition='outside')

                elif st.session_state.chart_type == 'Anillo (Proporción)':
                    fig = px.pie(df_plot, values='Estudiantes', names='Nivel', hole=0.6,
                                 color='Nivel', color_discrete_map=COLORS_NIVELES)
                    fig.update_traces(textinfo='percent+label')

                elif st.session_state.chart_type == 'Mapa de Árbol (Jerarquía)':
                    fig = px.treemap(df_plot, path=['Nivel'], values='Estudiantes',
                                     color='Nivel', color_discrete_map=COLORS_NIVELES)

                elif st.session_state.chart_type == 'Radar de Competencias':
                    fig = go.Figure(data=go.Scatterpolar(
                        r=df_plot['Estudiantes'],
                        theta=df_plot['Nivel'],
                        fill='toself',
                        line_color=PBI_LIGHT_BLUE
                    ))
                
                elif st.session_state.chart_type == 'Solar (Sunburst)':
                    fig = px.sunburst(df_plot, path=['Nivel'], values='Estudiantes',
                                      color='Nivel', color_discrete_map=COLORS_NIVELES)

                fig.update_layout(
                    margin=dict(t=40, b=20, l=20, r=20), 
                    height=450,
                    font_family="Segoe UI",
                    font=dict(size=20),
                    hovermode="closest",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig, use_container_width=True, key=f"plotly_v2_{sheet_name}_{selected_comp}_{i}")
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button(f"🎯 Generar Insights IA - {sheet_name}", type="primary", use_container_width=True, key=f"btn_ai_{i}"):
                with st.expander("Panel de Sugerencias Pedagógicas (Generado por IA)", expanded=True):
                    ai_text = pedagogical_assistant.generate_suggestions(results, sheet_name, selected_comp)
                    st.markdown(f"<div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid {PBI_BLUE};'>{ai_text}</div>", unsafe_allow_html=True)

def mostrar_analisis_por_estudiante(df_first, df_config, info_areas):
    """Perfil individual con tarjetas de KPI estilo Power BI"""
    st.markdown(f"<h2 class='pbi-header'>Perfil Integral del Estudiante</h2>", unsafe_allow_html=True)
    
    all_dfs = st.session_state.get('all_dataframes', {})
    if not all_dfs:
        st.warning("⚠️ No se detectaron datos en la sesión actual.")
        return

    posibles = ["Estudiante", "ESTUDIANTE", "APELLIDOS Y NOMBRES", "Apellidos y Nombres", "ALUMNO"]
    first_sheet = next(iter(all_dfs))
    df_base = all_dfs[first_sheet]
    col_nombre = next((c for c in df_base.columns if str(c).strip() in posibles), None)

    if not col_nombre:
        st.error("Error estructural: No se localizó la columna de identidad del estudiante.")
        return

    estudiante_sel = st.selectbox("👤 Seleccionar Estudiante para análisis focalizado:", 
                                options=df_base[col_nombre].dropna().unique(), 
                                index=None, key="pbi_student_selector")

    if estudiante_sel:
        st.markdown(f"<div class='pbi-card'><h3 style='color:{PBI_BLUE}; margin-top:0;'>Estudiante: {estudiante_sel}</h3>", unsafe_allow_html=True)
        
        total_conteo = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        desglose_areas = {'AD': [], 'A': [], 'B': [], 'C': []}
        
        for area_name, df_area in all_dfs.items():
            fila = df_area[df_area[col_nombre] == estudiante_sel]
            if not fila.empty:
                vals = [str(v).upper().strip() for v in fila.iloc[0].values]
                for n in total_conteo.keys():
                    count = vals.count(n)
                    total_conteo[n] += count
                    if count > 0: desglose_areas[n].append(f"{area_name} ({count})")

        cols = st.columns(4)
        for idx, (n, label) in enumerate([('AD', 'Destacado'), ('A', 'Logrado'), ('B', 'Proceso'), ('C', 'Inicio')]):
            with cols[idx]:
                st.markdown(f"""
                    <div style='background: {COLORS_NIVELES[n]}; padding: 15px; border-radius: 5px; color: white; text-align: center;'>
                        <div style='font-size: 0.8rem; opacity: 0.9;'>{label}</div>
                        <div style='font-size: 1.8rem; font-weight: bold;'>{total_conteo[n]}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("<b>Distribución por Competencias</b>", unsafe_allow_html=True)
            for n, label in [('AD', '🏆 Destacado'), ('A', '✅ Logrado'), ('B', '⚠️ Proceso'), ('C', '🛑 Inicio')]:
                if total_conteo[n] > 0:
                    with st.expander(f"{label}: {total_conteo[n]}"):
                        for a in desglose_areas[n]: st.write(f"• {a}")
        
        with c2:
            fig = px.pie(values=list(total_conteo.values()), names=list(total_conteo.keys()), hole=0.5,
                        color=list(total_conteo.keys()), color_discrete_map=COLORS_NIVELES)
            fig.update_layout(showlegend=True, height=280, margin=dict(t=0, b=0, l=0, r=0),
                            legend=dict(orientation="v", x=1))
            st.plotly_chart(fig, use_container_width=True, key=f"pie_ind_pbi_{estudiante_sel}")
        
        doc_buffer = pedagogical_assistant.generar_reporte_estudiante(estudiante_sel, total_conteo, desglose_areas)
        st.download_button(label="📥 Descargar Informe Individual (Word)", data=doc_buffer, 
                          file_name=f"Informe_{estudiante_sel}.docx", use_container_width=True, key=f"dl_word_{estudiante_sel}")
        st.markdown("</div>", unsafe_allow_html=True)

@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Frecuencias', index=True)
        workbook = writer.book
        worksheet = writer.sheets['Frecuencias']
        fmt_header = workbook.add_format({'bg_color': '#113770', 'font_color': 'white', 'bold': True, 'border': 1})
        fmt_comp = workbook.add_format({'text_wrap': True, 'valign': 'vcenter', 'border': 1})
        worksheet.set_column('A:A', 50, fmt_comp)
        worksheet.set_column('B:Z', 12)
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num + 1, value, fmt_header)
    return output.getvalue()

def configurar_uploader():
    st.markdown("<div class='pbi-card' style='text-align: center; border: 2px dashed #ccc;'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Arrastra o selecciona el archivo Excel de SIAGIE", type=["xlsx"])
    if uploaded_file:
        with st.spinner('Sincronizando datos...'):
            excel_file = pd.ExcelFile(uploaded_file)
            hojas_validas = [s for s in excel_file.sheet_names if s not in ["Generalidades", "Parametros"]]
            st.session_state.all_dataframes = {sheet: excel_file.parse(sheet) for sheet in hojas_validas}
            st.session_state.info_areas = analysis_core.analyze_data(excel_file, hojas_validas)
            st.session_state.df_cargado = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def inject_pbi_css():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
        
        /* USANDO EL SELECTOR QUE TE FUNCIONÓ EN HOME PARA EL FONDO */
        [data-testid="stAppViewContainer"] {{
            background-color: {PBI_BG} !important;
            background-attachment: fixed;
        }}

        .stApp {{ 
            background-color: transparent !important;
            font-family: 'Segoe UI', sans-serif;
        }}

        .pbi-card {{
            background-color: {PBI_CARD_BG};
            padding: 24px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 24px;
            border: 1px solid #E5E7EB;
        }}
        .pbi-header {{
            color: {PBI_BLUE};
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            border-bottom: 4px solid {PBI_LIGHT_BLUE};
            padding-bottom: 8px;
            text-transform: uppercase;
        }}
        div.stDownloadButton > button {{
            background-color: {PBI_LIGHT_BLUE} !important;
            color: white !important;
            border-radius: 2px !important;
            font-weight: 600 !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: #E5E7EB;
            border-radius: 4px 4px 0 0;
            padding: 8px 16px;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {PBI_CARD_BG} !important;
            border-top: 3px solid {PBI_LIGHT_BLUE} !important;
            font-weight: bold;
        }}
        </style>
    """, unsafe_allow_html=True)

