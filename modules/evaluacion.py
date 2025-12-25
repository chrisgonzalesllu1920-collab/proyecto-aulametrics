import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter

# Paleta de Colores Power BI
PBI_BLUE = "#113770"
PBI_LIGHT_BLUE = "#0078D4"
PBI_BG = "#F3F2F1"
PBI_CARD_BG = "#FFFFFF"
COLORS_NIVELES = {'AD': '#004B50', 'A': '#00838F', 'B': '#F9A825', 'C': '#C62828'}

def evaluacion_page(asistente):
    """Controlador principal compatible con app.py"""
    inject_pbi_css()
    
    if not st.session_state.get('df_cargado', False):
        st.markdown(f"<h1 class='pbi-header'>📊 Dashboard de Evaluación Pedagógica</h1>", unsafe_allow_html=True)
        configurar_uploader()
    else:
        # Recuperar datos
        info_areas = st.session_state.get('info_areas', {})
        
        # Sidebar de Filtros (Estilo Slicer de Power BI)
        with st.sidebar:
            st.markdown(f"<h2 style='color:{PBI_BLUE};'>Filtros</h2>", unsafe_allow_html=True)
            areas_disponibles = list(info_areas.keys())
            area_sel = st.selectbox("Seleccionar Área Curricular", ["Vista General"] + areas_disponibles)
            st.divider()
            if st.button("🔄 Cargar nuevo archivo"):
                st.session_state.df_cargado = False
                st.rerun()

        if area_sel == "Vista General":
            mostrar_analisis_general(info_areas)
        else:
            render_detalle_area(area_sel, info_areas[area_sel])

def mostrar_analisis_general(info_areas):
    """Función requerida por app.py - Renderiza el Dashboard Global"""
    st.markdown(f"<h1 class='pbi-header'>Resumen Ejecutivo de Desempeño</h1>", unsafe_allow_html=True)
    
    # KPIs SUPERIORES
    total_comps = sum(len(d.get('df_frecuencias', [])) for d in info_areas.values() if 'df_frecuencias' in d)
    
    conteo_gen = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
    for d in info_areas.values():
        if 'df_frecuencias' in d:
            for nivel in conteo_gen:
                if nivel in d['df_frecuencias'].columns:
                    conteo_gen[nivel] += d['df_frecuencias'][nivel].sum()

    cols = st.columns(4)
    with cols[0]: render_kpi("Áreas Analizadas", len(info_areas))
    with cols[1]: render_kpi("Competencias", total_comps)
    with cols[2]: 
        total = sum(conteo_gen.values())
        pct = (conteo_gen['AD'] + conteo_gen['A']) / total * 100 if total > 0 else 0
        render_kpi("% Logro (AD+A)", f"{pct:.1f}%")
    with cols[3]: render_kpi("Alertas (C)", conteo_gen['C'])

    # Dashboard Grid
    c1, c2 = st.columns([1, 1.2])
    
    with c1:
        st.markdown("<div class='pbi-card'><b>Distribución de Logros</b>", unsafe_allow_html=True)
        fig_pie = px.pie(names=list(conteo_gen.keys()), values=list(conteo_gen.values()), 
                         color=list(conteo_gen.keys()), color_discrete_map=COLORS_NIVELES, hole=0.5)
        fig_pie.update_layout(margin=dict(t=20, b=20, l=0, r=0), height=350, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='pbi-card'><b>Desempeño Comparativo por Área</b>", unsafe_allow_html=True)
        data_stack = []
        for area, d in info_areas.items():
            if 'df_frecuencias' in d:
                res = d['df_frecuencias'].sum(numeric_only=True).to_dict()
                res['Área'] = area
                data_stack.append(res)
        
        if data_stack:
            df_stack = pd.DataFrame(data_stack)
            fig_bar = px.bar(df_stack, x='Área', y=['AD', 'A', 'B', 'C'], 
                             color_discrete_map=COLORS_NIVELES, barmode='stack')
            fig_bar.update_layout(margin=dict(t=20, b=20, l=0, r=0), height=350, xaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

def render_detalle_area(nombre, datos):
    """Visualización detallada por área"""
    st.markdown(f"<h1 class='pbi-header'>Detalle: {nombre}</h1>", unsafe_allow_html=True)
    
    if 'df_frecuencias' not in datos:
        st.warning("No hay datos de frecuencias para esta área.")
        return

    df_f = datos['df_frecuencias']
    
    col_t, col_g = st.columns([1, 1.5])
    with col_t:
        st.markdown("<div class='pbi-card'><b>Tabla de Datos</b>", unsafe_allow_html=True)
        st.dataframe(df_f, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Botón de descarga estilizado
        excel_data = convert_df_to_excel(df_f, nombre, datos.get('general_info', {}))
        st.download_button("📥 Descargar Reporte Excel", data=excel_data, file_name=f"Reporte_{nombre}.xlsx")

    with col_g:
        st.markdown("<div class='pbi-card'><b>Análisis por Competencia</b>", unsafe_allow_html=True)
        fig = go.Figure()
        for n in ['C', 'B', 'A', 'AD']:
            if n in df_f.columns:
                fig.add_trace(go.Bar(name=n, y=df_f.index, x=df_f[n], orientation='h', marker_color=COLORS_NIVELES[n]))
        fig.update_layout(barmode='stack', height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

def render_kpi(label, value):
    st.markdown(f"""
        <div class='pbi-card' style='text-align: center; padding: 10px;'>
            <div style='color: #666; font-size: 0.9rem; font-weight: 500;'>{label}</div>
            <div style='color: {PBI_BLUE}; font-size: 1.8rem; font-weight: 700;'>{value}</div>
        </div>
    """, unsafe_allow_html=True)

def convert_df_to_excel(df, area_name, general_info):
    """Función requerida por app.py para exportación"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Frecuencias')
        workbook = writer.book
        worksheet = writer.sheets['Frecuencias']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#113770', 'font_color': 'white'})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num + 1, value, header_format)
    return output.getvalue()

def configurar_uploader():
    with st.container():
        st.markdown("<div class='pbi-card'>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("📂 Cargar Reporte SIAGIE (Excel)", type=["xlsx"])
        if uploaded_file:
            with st.spinner('Analizando estructura...'):
                excel_file = pd.ExcelFile(uploaded_file)
                # Llamada al core de análisis
                info_areas = analysis_core.analyze_data(excel_file, excel_file.sheet_names)
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
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }}
        .pbi-header {{
            color: {PBI_BLUE};
            font-family: 'Segoe UI', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            border-left: 5px solid {PBI_LIGHT_BLUE};
            padding-left: 15px;
            margin-bottom: 20px;
        }}
        </style>
    """, unsafe_allow_html=True)
