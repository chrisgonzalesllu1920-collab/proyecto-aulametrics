import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter
import pedagogical_assistant

# --- CONFIGURACIÓN DE COLORES PBI ---
PBI_BLUE = "#113770"
PBI_LIGHT_BLUE = "#0078D4"
PBI_BG = "#F3F2F1"
PBI_CARD_BG = "#FFFFFF"
COLORS_NIVELES = {'AD': '#008450', 'A': '#4CAF50', 'B': '#FFEB3B', 'C': '#F44336'}

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
            df_first = st.session_state.get('df')
            df_config = st.session_state.get('df_config')
            mostrar_analisis_por_estudiante(df_first, df_config, st.session_state.get('info_areas'))

def mostrar_analisis_general(results):
    """Tu lógica original con piel de Power BI"""
    st.markdown(f"<h2 class='pbi-header'>Resultados Consolidados por Área</h2>", unsafe_allow_html=True)

    first_sheet_key = next(iter(results), None)
    general_data = {}
    if first_sheet_key and 'generalidades' in results[first_sheet_key]:
        general_data = results[first_sheet_key]['generalidades']
        st.markdown(f"""
            <div class='pbi-card' style='padding: 10px 20px; border-left: 5px solid {PBI_LIGHT_BLUE};'>
                <b>Grupo:</b> Nivel {general_data.get('nivel', 'Descon.')} | Grado {general_data.get('grado', 'Descon.')}
            </div>
        """, unsafe_allow_html=True)
    
    # Sidebar de Configuración (Power BI Slicer Style)
    with st.sidebar:
        st.markdown(f"<h3 style='color:{PBI_BLUE};'>⚙️ Visualización</h3>", unsafe_allow_html=True)
        chart_options = ('Barras (Por Competencia)', 'Pastel (Proporción)')
        st.session_state.chart_type = st.radio("Tipo de gráfico:", chart_options, key="chart_radio_pbi")

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
            st.markdown("<div class='pbi-card'><b>1. Distribución de Logros</b>", unsafe_allow_html=True)
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
            st.download_button(label=f"⬇️ Exportar Excel ({sheet_name})", data=excel_data, 
                                file_name=f'Frecuencias_{sheet_name}.xlsx', key=f'btn_dl_{i}')
            st.markdown("</div>", unsafe_allow_html=True)

            # --- GRÁFICOS ---
            st.markdown("<div class='pbi-card'><b>2. Análisis Gráfico</b>", unsafe_allow_html=True)
            competencia_nombres_limpios = df_table.index.tolist()
            selected_comp = st.selectbox(f"Selecciona la competencia:", options=competencia_nombres_limpios, key=f'sel_{sheet_name}')

            if selected_comp:
                try:
                    df_plot = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']].reset_index()
                    df_plot.columns = ['Nivel', 'Estudiantes']
                    df_plot['Nivel'] = df_plot['Nivel'].str.replace(' (Est.)', '', regex=False)

                    # Validación de datos para el gráfico
                    if df_plot['Estudiantes'].sum() == 0:
                        st.warning(f"No hay datos numéricos para graficar en la competencia: {selected_comp}")
                    else:
                        if st.session_state.chart_type == 'Barras (Por Competencia)':
                            fig = px.bar(df_plot, x='Nivel', y='Estudiantes', color='Nivel', 
                                        color_discrete_map={'AD': 'green', 'A': '#90EE90', 'B': 'orange', 'C': 'red'})
                        else:
                            fig = px.pie(df_plot, values='Estudiantes', names='Nivel', hole=0.4,
                                        color='Nivel', color_discrete_map={'AD': 'green', 'A': '#90EE90', 'B': 'orange', 'C': 'red'})
                        
                        fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=350)
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error al generar gráfico para {selected_comp}: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)

            # --- ASISTENTE IA ---
            if st.button(f"🎯 Propuestas de mejora - {sheet_name}", type="primary", use_container_width=True):
                with st.expander("Análisis Pedagógico IA", expanded=True):
                    ai_text = pedagogical_assistant.generate_suggestions(results, sheet_name, selected_comp)
                    st.markdown(ai_text, unsafe_allow_html=True)

def mostrar_analisis_por_estudiante(df_first, df_config, info_areas):
    """Tu lógica de perfil individual con diseño mejorado"""
    st.markdown(f"<h2 class='pbi-header'>Perfil Integral del Estudiante</h2>", unsafe_allow_html=True)
    
    all_dfs = st.session_state.get('all_dataframes', {})
    if not all_dfs:
        st.warning("⚠️ No hay datos cargados.")
        return

    # Detección de columna de nombre
    posibles = ["Estudiante", "ESTUDIANTE", "APELLIDOS Y NOMBRES", "Apellidos y Nombres", "ALUMNO"]
    first_sheet = next(iter(all_dfs))
    df_base = all_dfs[first_sheet]
    col_nombre = next((c for c in df_base.columns if str(c).strip() in posibles), None)

    if not col_nombre:
        st.error("No se encontró la columna de nombres.")
        return

    estudiante_sel = st.selectbox("🔍 Buscar estudiante:", options=df_base[col_nombre].dropna().unique(), index=None)

    if estudiante_sel:
        st.markdown(f"<div class='pbi-card'><h3>📊 Reporte: {estudiante_sel}</h3>", unsafe_allow_html=True)
        
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

        c1, c2 = st.columns([1, 1])
        with c1:
            for n, label in [('AD', '🏆 Destacado'), ('A', '✅ Logrado'), ('B', '⚠️ Proceso'), ('C', '🛑 Inicio')]:
                if total_conteo[n] > 0:
                    with st.expander(f"{label}: {total_conteo[n]}"):
                        for a in desglose_areas[n]: st.write(f"- {a}")
                else:
                    st.caption(f"{label}: 0")
        
        with c2:
            if sum(total_conteo.values()) > 0:
                fig = px.pie(values=list(total_conteo.values()), names=list(total_conteo.keys()), hole=0.5,
                            color=list(total_conteo.keys()), color_discrete_map={'AD': 'green', 'A': '#90EE90', 'B': 'orange', 'C': 'red'})
                fig.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de calificación para este estudiante.")

        # Botón Word Azul
        doc_buffer = pedagogical_assistant.generar_reporte_estudiante(estudiante_sel, total_conteo, desglose_areas)
        st.download_button(label="📄 Descargar Informe de Progreso (Word)", data=doc_buffer, 
                        file_name=f"Informe_{estudiante_sel}.docx", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    """Tu función de Excel con formato mejorado"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Frecuencias', index=True)
        workbook = writer.book
        worksheet = writer.sheets['Frecuencias']
        
        # Formatos
        fmt_header = workbook.add_format({'bg_color': '#113770', 'font_color': 'white', 'bold': True, 'border': 1})
        fmt_comp = workbook.add_format({'text_wrap': True, 'valign': 'vcenter', 'border': 1})
        
        worksheet.set_column('A:A', 50, fmt_comp)
        worksheet.set_column('B:Z', 10)
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num + 1, value, fmt_header)
            
    return output.getvalue()

def configurar_uploader():
    st.markdown("<div class='pbi-card'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("📂 Subir archivo Excel SIAGIE", type=["xlsx"])
    if uploaded_file:
        with st.spinner('Procesando...'):
            excel_file = pd.ExcelFile(uploaded_file)
            
            # --- CAMBIO SOLICITADO: FILTRAR HOJAS NO DESEADAS ---
            hojas_validas = [s for s in excel_file.sheet_names if s not in ["Generalidades", "Parametros"]]
            
            st.session_state.all_dataframes = {sheet: excel_file.parse(sheet) for sheet in hojas_validas}
            info_areas = analysis_core.analyze_data(excel_file, hojas_validas)
            st.session_state.info_areas = info_areas
            st.session_state.df_cargado = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def inject_pbi_css():
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {PBI_BG}; }}
        .pbi-card {{
            background-color: {PBI_CARD_BG};
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            border: 1px solid #E1E1E1;
        }}
        .pbi-header {{
            color: {PBI_BLUE};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            border-bottom: 3px solid {PBI_LIGHT_BLUE};
            padding-bottom: 10px;
        }}
        div.stDownloadButton > button {{
            background-color: #0056b3 !important;
            color: white !important;
            border-radius: 6px !important;
            border: none !important;
            padding: 10px 20px !important;
        }}
        </style>
    """, unsafe_allow_html=True)
