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
    Maneja la carga de archivos y la visualización de resultados.
    """
    if not st.session_state.get('df_cargado', False):
        st.header("📊 Sistema de Evaluación")
        st.info("Para comenzar, sube tu registro de notas (Excel).")
        configurar_uploader()
    else:
        tab_global, tab_individual = st.tabs(["🌎 Vista Global", "👤 Vista por Estudiante"])
        
        with tab_global:
            st.subheader("Panorama General del Aula")
            info_areas = st.session_state.get('info_areas')
            mostrar_analisis_general(info_areas)
            
        with tab_individual:
            mostrar_analisis_por_estudiante()

# =========================================================================
# === PALETA DE COLORES Y ESTILOS (DISEÑO WOW) ===
# =========================================================================
COLORS_PREMIUM = {
    'AD': '#059669',  # Esmeralda
    'A':  '#34D399',  # Menta
    'B':  '#FBBF24',  # Ámbar
    'C':  '#FB7185'   # Coral
}

def apply_wow_layout(fig, title_text):
    """Aplica estética moderna: sin cuadrículas, fuentes limpias y títulos elegantes."""
    fig.update_layout(
        title={'text': f"<b>{title_text}</b>", 'x': 0.5, 'font': {'size': 20}},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=80, b=40, l=40, r=40),
        font=dict(family="sans-serif", size=14, color="#475569"),
        showlegend=True
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig

# =========================================================================
# === FUNCIONES DE VISUALIZACIÓN ===
# =========================================================================

def mostrar_analisis_general(info_areas):
    if not info_areas:
        st.warning("No hay datos para mostrar.")
        return

    areas = list(info_areas.keys())
    area_sel = st.selectbox("Selecciona un Área para analizar:", areas)
    comp_data = info_areas[area_sel]['competencias']
    
    resumen_list = []
    for comp_name, stats in comp_data.items():
        for nivel, cant in stats['frecuencias'].items():
            resumen_list.append({'Competencia': comp_name, 'Nivel': nivel, 'Cantidad': cant})
    
    df_plot = pd.DataFrame(resumen_list)
    
    if not df_plot.empty:
        fig = px.bar(
            df_plot, x='Competencia', y='Cantidad', color='Nivel',
            barmode='group', text='Cantidad',
            color_discrete_map=COLORS_PREMIUM,
            category_orders={"Nivel": ["AD", "A", "B", "C"]}
        )
        fig.update_traces(textposition='outside')
        fig = apply_wow_layout(fig, f"Distribución de Logros: {area_sel}")
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Descargar Reporte Excel"):
            # Usamos el DataFrame de frecuencias consolidado para la descarga
            df_frecuencias = pd.DataFrame({area: datos['competencias'] for area, datos in info_areas.items()})
            buffer = convert_df_to_excel(df_frecuencias)
            st.download_button("Guardar Excel", data=buffer, file_name="reporte_notas.xlsx")

def mostrar_analisis_por_estudiante():
    df = st.session_state.get('df')
    if df is None: return

    est_sel = st.selectbox("Buscar Estudiante:", df['Estudiante'].unique())
    row = df[df['Estudiante'] == est_sel].iloc[0]
    conceptuales = [c for c in df.columns if c not in ['Estudiante', 'Promedio']]
    
    df_est = pd.DataFrame({'Competencia': conceptuales, 'Nota': [row[c] for c in conceptuales]})

    fig = px.bar(
        df_est, y='Competencia', x='Nota', orientation='h', color='Nota',
        color_discrete_map=COLORS_PREMIUM, text='Nota',
        category_orders={"Nota": ["AD", "A", "B", "C"]}
    )
    fig = apply_wow_layout(fig, f"Perfil de Logros: {est_sel}")
    st.plotly_chart(fig, use_container_width=True)

# =========================================================================
# === FUNCIONES DE SOPORTE Y EXPORTACIÓN (OBLIGATORIAS) ===
# =========================================================================

def configurar_uploader():
    archivo = st.file_uploader("Sube tu archivo .xlsx", type=['xlsx'])
    if archivo:
        with st.spinner("Procesando..."):
            df, info_areas = analysis_core.procesar_excel(archivo)
            if df is not None:
                st.session_state['df'] = df
                st.session_state['info_areas'] = info_areas
                st.session_state['df_cargado'] = True
                st.rerun()

def convert_df_to_excel(df):
    """
    Función requerida por el sistema para exportar a Excel.
    Mantenemos el nombre original para evitar errores de importación.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Lógica de escritura personalizada según la estructura de info_areas
        df.to_excel(writer, sheet_name='Resumen_Evaluacion')
        workbook  = writer.book
        worksheet = writer.sheets['Resumen_Evaluacion']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        worksheet.set_column('A:Z', 15)
    return output.getvalue()
