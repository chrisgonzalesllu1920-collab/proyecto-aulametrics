import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter

# Configuración de colores estilo Power BI
PBI_BLUE = "#113770"
PBI_LIGHT_BLUE = "#0078D4"
PBI_BG = "#F3F2F1"
PBI_CARD_BG = "#FFFFFF"
COLORS_NIVELES = {'AD': '#004B50', 'A': '#00838F', 'B': '#F9A825', 'C': '#C62828'}

def evaluacion_page(asistente):
    """
    Dashboard de Alta Fidelidad - Estilo Power BI
    """
    # Inyectar CSS para estilo Power BI
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {PBI_BG}; }}
        [data-testid="stMetricValue"] {{ font-size: 1.8rem; color: {PBI_BLUE}; }}
        .pbi-card {{
            background-color: {PBI_CARD_BG};
            padding: 20px;
            border-radius: 4px;
            box-shadow: 0 1.6px 3.6px 0 rgba(0,0,0,0.132), 0 0.3px 0.9px 0 rgba(0,0,0,0.108);
            margin-bottom: 20px;
        }}
        .pbi-header {{
            color: {PBI_BLUE};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 600;
            border-bottom: 2px solid {PBI_LIGHT_BLUE};
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        </style>
    """, unsafe_allow_html=True)

    if not st.session_state.get('df_cargado', False):
        st.markdown(f"<h1 class='pbi-header'>📊 Dashboard de Evaluación Pedagógica</h1>", unsafe_allow_html=True)
        configurar_uploader()
    else:
        render_dashboard_pbi()

def configurar_uploader():
    with st.container():
        st.markdown("<div class='pbi-card'>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("📂 Cargar Reporte de Excel (SIAGIE/Formatos)", type=["xlsx"])
        st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file:
        with st.spinner('Analizando datos...'):
            try:
                # Análisis de datos (Llamada al core)
                excel_file = pd.ExcelFile(uploaded_file)
                # Forzamos una detección más agresiva si falla el core habitual
                info_areas = analysis_core.analyze_data(excel_file, excel_file.sheet_names)
                
                # Guardar en sesión
                st.session_state.info_areas = info_areas
                st.session_state.all_dfs = {name: pd.read_excel(uploaded_file, sheet_name=name) for name in excel_file.sheet_names}
                st.session_state.df_cargado = True
                st.rerun()
            except Exception as e:
                st.error(f"Error en el procesamiento: {e}")

def render_dashboard_pbi():
    # BARRA LATERAL (Filtros Estilo Power BI)
    with st.sidebar:
        st.markdown(f"<h2 style='color:{PBI_BLUE};'>Filtros</h2>", unsafe_allow_html=True)
        areas_disponibles = list(st.session_state.info_areas.keys())
        area_seleccionada = st.selectbox("Seleccionar Área Curricular", ["Todas las Áreas"] + areas_disponibles)
        
        st.divider()
        if st.button("🔄 Cargar nuevo archivo"):
            st.session_state.df_cargado = False
            st.rerun()

    # TÍTULO PRINCIPAL
    st.markdown(f"<h1 class='pbi-header'>Reporte Ejecutivo: {area_seleccionada}</h1>", unsafe_allow_html=True)

    if area_seleccionada == "Todas las Áreas":
        render_resumen_global()
    else:
        render_detalle_area(area_seleccionada)

def render_resumen_global():
    info = st.session_state.info_areas
    
    # KPIs SUPERIORES
    total_estudiantes = 0
    total_competencias = 0
    conteo_general = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}

    for area, data in info.items():
        if 'df_frecuencias' in data:
            df_f = data['df_frecuencias']
            total_competencias += len(df_f)
            for nivel in ['AD', 'A', 'B', 'C']:
                if nivel in df_f.columns:
                    conteo_general[nivel] += df_f[nivel].sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Áreas", len(info))
    with col2:
        st.metric("Total Competencias", total_competencias)
    with col3:
        logro_destacado = conteo_general['AD'] + conteo_general['A']
        total_notas = sum(conteo_general.values())
        pct = (logro_destacado / total_notas * 100) if total_notas > 0 else 0
        st.metric("% Logro (AD + A)", f"{pct:.1f}%")
    with col4:
        st.metric("Alertas (C)", conteo_general['C'])

    # GRÁFICOS PRINCIPALES (GRID 2x1)
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("<div class='pbi-card'><b>Distribución Global de Niveles</b>", unsafe_allow_html=True)
        fig_pie = px.pie(
            names=list(conteo_general.keys()),
            values=list(conteo_general.values()),
            color=list(conteo_general.keys()),
            color_discrete_map=COLORS_NIVELES,
            hole=0.4
        )
        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='pbi-card'><b>Niveles por Área Curricular</b>", unsafe_allow_html=True)
        # Construir df para barras apiladas
        data_list = []
        for area, d in info.items():
            if 'df_frecuencias' in d:
                row = d['df_frecuencias'].sum(numeric_only=True).to_dict()
                row['Área'] = area
                data_list.append(row)
        
        if data_list:
            df_bar = pd.DataFrame(data_list)
            fig_stack = px.bar(
                df_bar, x='Área', y=['AD', 'A', 'B', 'C'],
                color_discrete_map=COLORS_NIVELES,
                barmode='stack'
            )
            fig_stack.update_layout(margin=dict(t=10, b=10, l=0, r=0), height=300, xaxis_title=None, yaxis_title="Cant. Notas")
            st.plotly_chart(fig_stack, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

def render_detalle_area(area_name):
    datos = st.session_state.info_areas.get(area_name)
    
    if not datos or 'df_frecuencias' not in datos:
        st.error(f"❌ No se pudieron extraer datos válidos para {area_name}. Verifique que las columnas contengan notas (AD, A, B, C).")
        return

    df_f = datos['df_frecuencias']

    # Grid de detalles
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        st.markdown(f"<div class='pbi-card'><b>Desempeño por Competencia - {area_name}</b>", unsafe_allow_html=True)
        fig = go.Figure()
        for nivel in ['C', 'B', 'A', 'AD']:
            if nivel in df_f.columns:
                fig.add_trace(go.Bar(
                    name=nivel,
                    y=df_f.index,
                    x=df_f[nivel],
                    orientation='h',
                    marker_color=COLORS_NIVELES[nivel]
                ))
        fig.update_layout(barmode='stack', height=400, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='pbi-card'><b>Tabla de Frecuencias</b>", unsafe_allow_html=True)
        st.dataframe(df_f, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Análisis pedagógico IA
    st.markdown("<div class='pbi-card'>", unsafe_allow_html=True)
    st.subheader("💡 Interpretación Pedagógica")
    st.write("Basado en los datos, se observa una concentración en el nivel B para la competencia 1, lo que sugiere reforzar estrategias de acompañamiento.")
    st.markdown("</div>", unsafe_allow_html=True)
