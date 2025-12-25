import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter
import pedagogical_assistant

# --- CONFIGURACIÓN DE ESTILOS POWER BI ---
PBI_BLUE = "#113770"
PBI_LIGHT_BLUE = "#0078D4"
PBI_BG = "#F3F2F1"
PBI_CARD_BG = "#FFFFFF"
# Paleta de colores estándar para niveles de logro
COLORS_MAP = {
    'AD': '#007A33', # Verde oscuro
    'A': '#43B02A',  # Verde brillante
    'B': '#FFC20E',  # Ámbar/Amarillo
    'C': '#E81123'   # Rojo Microsoft
}

def evaluacion_page(asistente):
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
            all_dfs = st.session_state.get('all_dataframes', {})
            mostrar_analisis_por_estudiante(all_dfs)

def mostrar_analisis_general(results):
    st.markdown(f"<h2 class='pbi-header'>Resultados Consolidados por Área</h2>", unsafe_allow_html=True)

    first_sheet_key = next(iter(results), None)
    general_data = {}
    if first_sheet_key and 'generalidades' in results[first_sheet_key]:
        general_data = results[first_sheet_key]['generalidades']
        st.markdown(f"""
            <div class='pbi-card' style='padding: 10px 20px; border-left: 5px solid {PBI_LIGHT_BLUE}; margin-bottom: 20px;'>
                <span style='color:#666'>Nivel:</span> <b>{general_data.get('nivel', 'N/A')}</b> | 
                <span style='color:#666'>Grado:</span> <b>{general_data.get('grado', 'N/A')}</b>
            </div>
        """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown(f"<h3 style='color:{PBI_BLUE};'>Visualización</h3>", unsafe_allow_html=True)
        chart_options = ('Barras (Por Competencia)', 'Donut (Proporción)')
        st.session_state.chart_type = st.radio("Tipo de gráfico:", chart_options, key="pbi_chart_selector")

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

            # Tabla de Frecuencias
            st.markdown(f"<div class='pbi-card'><b>Matriz de Logros: {sheet_name}</b>", unsafe_allow_html=True)
            data_table = {'Competencia': [], 'AD': [], 'A': [], 'B': [], 'C': [], 'Total': []}
            
            for comp_key, comp_data in competencias.items():
                counts = comp_data['conteo_niveles']
                data_table['Competencia'].append(comp_data['nombre_limpio'])
                for level in ['AD', 'A', 'B', 'C']:
                    data_table[level].append(counts.get(level, 0))
                data_table['Total'].append(comp_data['total_evaluados'])
            
            df_table = pd.DataFrame(data_table).set_index('Competencia')
            st.dataframe(df_table.style.background_gradient(cmap='Blues', subset=['Total']), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Sección de Gráficos con Claves Únicas para evitar errores de ID
            st.markdown("<div class='pbi-card'><b>Análisis Visual Interactivo</b>", unsafe_allow_html=True)
            
            # Selector de competencia para el gráfico
            selected_comp = st.selectbox(
                "Seleccione Competencia para analizar:", 
                options=df_table.index.tolist(), 
                key=f"sel_comp_{sheet_name}_{i}"
            )

            if selected_comp:
                try:
                    row = df_table.loc[selected_comp]
                    df_plot = pd.DataFrame({
                        'Nivel': ['AD', 'A', 'B', 'C'],
                        'Cantidad': [row['AD'], row['A'], row['B'], row['C']]
                    })

                    if df_plot['Cantidad'].sum() == 0:
                        st.warning("No hay datos suficientes para generar el gráfico en esta competencia.")
                    else:
                        if st.session_state.chart_type == 'Barras (Por Competencia)':
                            fig = px.bar(
                                df_plot, x='Nivel', y='Cantidad', color='Nivel',
                                text='Cantidad',
                                color_discrete_map=COLORS_MAP,
                                title=f"Distribución: {selected_comp}"
                            )
                            fig.update_traces(textposition='outside')
                        else:
                            fig = px.pie(
                                df_plot, values='Cantidad', names='Nivel', hole=0.5,
                                color='Nivel', color_discrete_map=COLORS_MAP,
                                title=f"Proporción: {selected_comp}"
                            )
                        
                        fig.update_layout(
                            font_family="Segoe UI",
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            margin=dict(t=50, b=20, l=20, r=20),
                            height=400
                        )
                        # Clave única obligatoria para evitar el error de ID duplicado
                        st.plotly_chart(fig, use_container_width=True, key=f"plot_{sheet_name}_{selected_comp}_{i}")
                
                except Exception as e:
                    st.error(f"Error al generar gráfico para {selected_comp}: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)

            # Botón de IA
            if st.button(f"🔍 Generar Análisis Pedagógico - {sheet_name}", key=f"ai_btn_{i}"):
                with st.expander("Sugerencias de la IA", expanded=True):
                    ai_text = pedagogical_assistant.generate_suggestions(results, sheet_name, selected_comp)
                    st.markdown(ai_text, unsafe_allow_html=True)

def mostrar_analisis_por_estudiante(all_dfs):
    st.markdown(f"<h2 class='pbi-header'>Perfil Individual del Estudiante</h2>", unsafe_allow_html=True)
    
    if not all_dfs:
        st.warning("No hay datos disponibles.")
        return

    # Buscar columna de identificación
    first_sheet = next(iter(all_dfs))
    df_sample = all_dfs[first_sheet]
    posibles_cols = ["ESTUDIANTE", "APELLIDOS Y NOMBRES", "Estudiante", "Apellidos y Nombres", "ALUMNO"]
    col_nombre = next((c for c in df_sample.columns if str(c).strip() in posibles_cols), None)

    if not col_nombre:
        st.error("No se pudo identificar la columna de nombres de estudiantes.")
        return

    lista_estudiantes = sorted(df_sample[col_nombre].dropna().unique().tolist())
    estudiante_sel = st.selectbox("Seleccione un estudiante:", options=lista_estudiantes, index=None, placeholder="Escriba el nombre...")

    if estudiante_sel:
        st.markdown(f"<div class='pbi-card'><h3>📊 Reporte: {estudiante_sel}</h3>", unsafe_allow_html=True)
        
        # Consolidar datos del estudiante en todas las áreas
        resumen_niveles = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        detalles = []
        
        for area, df_area in all_dfs.items():
            fila = df_area[df_area[col_nombre] == estudiante_sel]
            if not fila.empty:
                # Contar niveles en las columnas de competencias (asumiendo que son las que tienen AD, A, B, C)
                notas = fila.iloc[0].astype(str).str.upper().str.strip()
                for n in resumen_niveles.keys():
                    count = (notas == n).sum()
                    resumen_niveles[n] += count
                    if count > 0:
                        detalles.append({"Área": area, "Nivel": n, "Cantidad": count})

        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.write("**Resumen de Calificaciones:**")
            df_res = pd.DataFrame(list(resumen_niveles.items()), columns=['Nivel', 'Total'])
            st.table(df_res.set_index('Nivel'))

        with col_right:
            if sum(resumen_niveles.values()) > 0:
                fig_ind = px.pie(
                    values=list(resumen_niveles.values()), 
                    names=list(resumen_niveles.keys()),
                    hole=0.6,
                    color=list(resumen_niveles.keys()),
                    color_discrete_map=COLORS_MAP
                )
                fig_ind.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
                st.plotly_chart(fig_ind, use_container_width=True, key=f"pie_ind_{estudiante_sel}")
        
        st.markdown("</div>", unsafe_allow_html=True)

def configurar_uploader():
    st.markdown("<div class='pbi-card'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("📂 Cargar archivo Excel (Formato SIAGIE)", type=["xlsx"])
    if uploaded_file:
        with st.spinner('Analizando estructura del archivo...'):
            excel_file = pd.ExcelFile(uploaded_file)
            # Excluir hojas administrativas
            hojas_validas = [s for s in excel_file.sheet_names if s not in ["Generalidades", "Parametros"]]
            
            st.session_state.all_dataframes = {sheet: excel_file.parse(sheet) for sheet in hojas_validas}
            # Procesar lógica pedagógica
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
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 15px;
            border: 1px solid #DEE1E6;
        }}
        .pbi-header {{
            color: {PBI_BLUE};
            font-family: 'Segoe UI Semibold', 'Segoe UI', Arial;
            font-size: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 5px;
            border-bottom: 2px solid {PBI_LIGHT_BLUE};
        }}
        /* Estilo para tablas */
        .styled-table {{ width: 100%; border-collapse: collapse; }}
        /* Ajuste de Tabs */
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
        .stTabs [data-baseweb="tab"] {{
            background-color: #e1e1e1;
            border-radius: 4px 4px 0 0;
            padding: 8px 16px;
        }}
        .stTabs [aria-selected="true"] {{ background-color: {PBI_LIGHT_BLUE} !important; color: white !important; }}
        </style>
    """, unsafe_allow_html=True)
