import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter
import pedagogical_assistant

# --- PALETA DE COLORES POWER BI (CAPTURA 03) ---
PBI_DARK = "#252423"
PBI_BLUE = "#113770"
PBI_LIGHT_BLUE = "#0078D4"
PBI_CANVAS = "#F2F2F2"  # Fondo de la aplicación
PBI_WHITE = "#FFFFFF"  # Fondo de las tarjetas
COLORS_NIVELES = {
    'AD': '#118D95', # Teal Power BI
    'A': '#28B463',  # Verde
    'B': '#FBC02D',  # Ámbar
    'C': '#E74C3C'   # Rojo
}

def evaluacion_page(asistente):
    """Punto de entrada con diseño de alta fidelidad Power BI"""
    inject_pbi_css()
    
    if not st.session_state.get('df_cargado', False):
        st.markdown(f"<div class='pbi-header'>📊 Panel de Control de Evaluación</div>", unsafe_allow_html=True)
        configurar_uploader()
    else:
        # Contenedor principal para control de márgenes
        st.markdown("<div class='main-canvas'>", unsafe_allow_html=True)
        tab_global, tab_individual = st.tabs(["🌎 PANORAMA GLOBAL", "👤 PERFIL ESTUDIANTE"])
        
        with tab_global:
            info_areas = st.session_state.get('info_areas', {})
            mostrar_analisis_general(info_areas)
            
        with tab_individual:
            all_dfs = st.session_state.get('all_dataframes', {})
            mostrar_analisis_por_estudiante(all_dfs)
        st.markdown("</div>", unsafe_allow_html=True)

def mostrar_analisis_general(results):
    """Visualización estilo Dashboard Pro"""
    first_sheet_key = next(iter(results), None)
    if first_sheet_key and 'generalidades' in results[first_sheet_key]:
        gen = results[first_sheet_key]['generalidades']
        st.markdown(f"""
            <div style='display: flex; gap: 15px; margin-bottom: 20px;'>
                <div class='pbi-kpi-mini'><b>NIVEL:</b> {gen.get('nivel', 'N/A')}</div>
                <div class='pbi-kpi-mini'><b>GRADO:</b> {gen.get('grado', 'N/A')}</div>
            </div>
        """, unsafe_allow_html=True)

    # Selector de visualización en Sidebar (Estilo Slicer)
    with st.sidebar:
        st.markdown(f"<div style='font-weight:bold; color:{PBI_DARK}; margin-bottom:10px;'>VISUALIZACIÓN</div>", unsafe_allow_html=True)
        chart_options = (
            'Gráfico de Columnas', 
            'Gráfico de Anillo', 
            'Treemap (Jerárquico)', 
            'Radar de Competencias',
            'Sunburst Dinámico'
        )
        st.session_state.chart_type = st.radio("Tipo de Gráfico:", chart_options, key="pbi_viz_selector")

    tabs = st.tabs([f"{sheet_name}" for sheet_name in results.keys()])

    for i, (sheet_name, result) in enumerate(results.items()):
        with tabs[i]:
            competencias = result.get('competencias', {})
            if not competencias: continue

            # Generar DataFrame de trabajo
            data = {'Competencia': [], 'AD': [], 'A': [], 'B': [], 'C': [], 'Total': []}
            for _, comp_data in competencias.items():
                counts = comp_data['conteo_niveles']
                data['Competencia'].append(comp_data['nombre_limpio'])
                for level in ['AD', 'A', 'B', 'C']:
                    data[level].append(counts.get(level, 0))
                data['Total'].append(comp_data['total_evaluados'])
            
            df_table = pd.DataFrame(data)

            # --- FILA 1: TABLA Y GRÁFICO ---
            col_tbl, col_grf = st.columns([1, 1])
            
            with col_tbl:
                st.markdown("<div class='pbi-card'><b>Matriz de Datos</b>", unsafe_allow_html=True)
                st.dataframe(df_table, use_container_width=True, hide_index=True)
                excel_data = convert_df_to_excel(df_table, sheet_name, {})
                st.download_button(f"📥 Excel {sheet_name}", excel_data, f"Reporte_{sheet_name}.xlsx", key=f"dl_{i}")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_grf:
                selected_comp = st.selectbox(f"Competencia ({sheet_name}):", df_table['Competencia'].tolist(), key=f"sel_{i}")
                st.markdown("<div class='pbi-card'>", unsafe_allow_html=True)
                
                df_plot = df_table[df_table['Competencia'] == selected_comp].melt(
                    id_vars=['Competencia'], value_vars=['AD', 'A', 'B', 'C'], 
                    var_name='Nivel', value_name='Estudiantes'
                )

                if st.session_state.chart_type == 'Gráfico de Columnas':
                    fig = px.bar(df_plot, x='Nivel', y='Estudiantes', color='Nivel', 
                                 color_discrete_map=COLORS_NIVELES, text_auto=True)
                elif st.session_state.chart_type == 'Gráfico de Anillo':
                    fig = px.pie(df_plot, values='Estudiantes', names='Nivel', hole=0.5, 
                                 color='Nivel', color_discrete_map=COLORS_NIVELES)
                elif st.session_state.chart_type == 'Treemap (Jerárquico)':
                    fig = px.treemap(df_plot, path=['Nivel'], values='Estudiantes', 
                                     color='Nivel', color_discrete_map=COLORS_NIVELES)
                elif st.session_state.chart_type == 'Radar de Competencias':
                    fig = go.Figure(data=go.Scatterpolar(r=df_plot['Estudiantes'], theta=df_plot['Nivel'], fill='toself'))
                else:
                    fig = px.sunburst(df_plot, path=['Nivel'], values='Estudiantes', 
                                      color='Nivel', color_discrete_map=COLORS_NIVELES)

                fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"plt_{i}")
                st.markdown("</div>", unsafe_allow_html=True)

            # --- IA INSIGHTS ---
            if st.button(f"🔍 Analizar {sheet_name} con IA", key=f"ai_btn_{i}"):
                res_ai = pedagogical_assistant.generate_suggestions(results, sheet_name, selected_comp)
                st.info(res_ai)

def mostrar_analisis_por_estudiante(all_dfs):
    """Vista de perfil con estética limpia"""
    posibles = ["Estudiante", "ESTUDIANTE", "APELLIDOS Y NOMBRES", "Apellidos y Nombres", "ALUMNO"]
    first_sheet = next(iter(all_dfs))
    col_nombre = next((c for c in all_dfs[first_sheet].columns if str(c).strip() in posibles), None)

    if not col_nombre: return

    estudiante_sel = st.selectbox("Buscar Estudiante:", all_dfs[first_sheet][col_nombre].unique(), index=None)

    if estudiante_sel:
        st.markdown(f"<h3 style='color:{PBI_BLUE};'>{estudiante_sel}</h3>", unsafe_allow_html=True)
        
        counts = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        for df in all_dfs.values():
            fila = df[df[col_nombre] == estudiante_sel]
            if not fila.empty:
                for n in counts.keys(): counts[n] += list(fila.iloc[0].values).count(n)

        cols = st.columns(4)
        for idx, n in enumerate(['AD', 'A', 'B', 'C']):
            with cols[idx]:
                st.markdown(f"""
                    <div class='pbi-kpi-card'>
                        <div style='color:#666; font-size:0.8rem;'>Nivel {n}</div>
                        <div style='color:{COLORS_NIVELES[n]}; font-size:1.8rem; font-weight:bold;'>{counts[n]}</div>
                    </div>
                """, unsafe_allow_html=True)

def configurar_uploader():
    """Cargador de archivos minimalista"""
    st.markdown("<div class='pbi-card'>", unsafe_allow_html=True)
    up = st.file_uploader("Subir archivos SIAGIE (Excel)", type=["xlsx"])
    if up:
        excel_file = pd.ExcelFile(up)
        hojas = [s for s in excel_file.sheet_names if s not in ["Generalidades", "Parametros"]]
        st.session_state.all_dataframes = {s: excel_file.parse(s) for s in hojas}
        st.session_state.info_areas = analysis_core.analyze_data(excel_file, hojas)
        st.session_state.df_cargado = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

@st.cache_data
def convert_df_to_excel(df, area_name, gen):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Reporte', index=False)
    return output.getvalue()

def inject_pbi_css():
    """CSS para transformar la UI de opaca a Canvas Profesional"""
    st.markdown(f"""
        <style>
        /* Fondo General */
        .stApp {{
            background-color: {PBI_CANVAS} !important;
        }}
        
        /* Contenedor principal sin el gris opaco */
        .main-canvas {{
            padding: 10px;
        }}

        /* Tarjetas estilo Power BI */
        .pbi-card {{
            background-color: {PBI_WHITE};
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            border: 1px solid #E0E0E0;
        }}

        /* Encabezado */
        .pbi-header {{
            background-color: {PBI_WHITE};
            padding: 15px 25px;
            font-size: 1.4rem;
            font-weight: bold;
            color: {PBI_DARK};
            border-bottom: 3px solid {PBI_LIGHT_BLUE};
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        /* KPIs Estilo Dashboard */
        .pbi-kpi-card {{
            background-color: {PBI_WHITE};
            padding: 20px;
            text-align: center;
            border-radius: 8px;
            border-bottom: 4px solid #CCC;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .pbi-kpi-mini {{
            background: {PBI_WHITE};
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.85rem;
            border: 1px solid #DDD;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }}

        /* Ajustes de Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: transparent !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 40px;
            white-space: pre-wrap;
            background-color: #E0E0E0 !important;
            margin-right: 5px;
            border-radius: 4px 4px 0 0;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {PBI_WHITE} !important;
            border-top: 2px solid {PBI_LIGHT_BLUE} !important;
        }}
        </style>
    """, unsafe_allow_html=True)
