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
# === PALETA DE COLORES Y ESTILOS (PARA DISEÑO WOW) ===
# =========================================================================
# Colores pedagógicos modernos (Emerald, Mint, Amber, Coral)
COLORS_PREMIUM = {
    'AD': '#059669',  # Verde Esmeralda
    'A':  '#34D399',  # Verde Menta
    'B':  '#FBBF24',  # Ámbar / Oro
    'C':  '#FB7185'   # Coral / Rosa suave
}

def apply_wow_layout(fig, title_text):
    """Aplica un diseño profesional y limpio a los gráficos de Plotly."""
    fig.update_layout(
        title={
            'text': f"<b>{title_text}</b>",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20, 'color': '#1E293B'}
        },
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=80, b=40, l=40, r=40),
        font=dict(family="Inter, sans-serif", size=14, color="#475569"),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Inter, sans-serif"
        )
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color="#94A3B8")
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False) # Limpiamos el eje Y para que los datos estén sobre las barras
    return fig

# =========================================================================
# === FUNCIONES DE VISUALIZACIÓN ACTUALIZADAS ===
# =========================================================================

def mostrar_analisis_general(info_areas):
    """Muestra el análisis descriptivo y comparativo con diseño premium."""
    if not info_areas:
        st.warning("No hay datos para mostrar.")
        return

    # Selector de Área
    areas = list(info_areas.keys())
    area_sel = st.selectbox("Selecciona un Área para analizar:", areas)
    
    comp_data = info_areas[area_sel]['competencias']
    
    # Procesar datos para el gráfico
    resumen_list = []
    for comp_name, stats in comp_data.items():
        frecuencias = stats['frecuencias']
        for nivel, cant in frecuencias.items():
            resumen_list.append({
                'Competencia': comp_name,
                'Nivel': nivel,
                'Cantidad': cant
            })
    
    df_plot = pd.DataFrame(resumen_list)
    
    # Crear gráfico de barras agrupadas con estilo WOW
    if not df_plot.empty:
        fig = px.bar(
            df_plot, 
            x='Competencia', 
            y='Cantidad', 
            color='Nivel',
            barmode='group',
            text='Cantidad',
            color_discrete_map=COLORS_PREMIUM,
            category_orders={"Nivel": ["AD", "A", "B", "C"]}
        )
        
        fig.update_traces(
            textposition='outside',
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Nivel %{fullData.name}: %{y} Estudiantes<extra></extra>"
        )
        
        fig = apply_wow_layout(fig, f"Distribución de Logros: {area_sel}")
        st.plotly_chart(fig, use_container_width=True)

    # Botones de exportación (se mantienen igual)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Descargar Reporte Excel"):
            buffer = descargar_excel_frecuencias(info_areas)
            st.download_button("Click aquí para guardar Excel", data=buffer, file_name="reporte_pedagogico.xlsx")
    with col2:
        if st.button("📊 Generar PPT de Resultados"):
            st.info("Función de exportación a PowerPoint en desarrollo.")

def mostrar_analisis_por_estudiante():
    """Muestra el progreso individual con barras horizontales de estilo limpio."""
    df = st.session_state.get('df')
    if df is None: return

    estudiantes = df['Estudiante'].unique()
    est_sel = st.selectbox("Buscar Estudiante:", estudiantes)
    
    # Filtrar datos del estudiante
    row = df[df['Estudiante'] == est_sel].iloc[0]
    
    # Extraer competencias y notas
    conceptuales = [c for c in df.columns if c not in ['Estudiante', 'Promedio']]
    notas = [row[c] for c in conceptuales]
    
    df_est = pd.DataFrame({
        'Competencia': conceptuales,
        'Nota': notas
    })

    # Gráfico de Barras Horizontales (Progreso Individual)
    # Es mucho más profesional que un pastel para mostrar niveles alcanzados
    fig = px.bar(
        df_est,
        y='Competencia',
        x='Nota',
        orientation='h',
        color='Nota',
        color_discrete_map=COLORS_PREMIUM,
        text='Nota',
        category_orders={"Nota": ["AD", "A", "B", "C"]}
    )

    fig.update_traces(
        textposition='inside',
        insidetextanchor='end',
        marker_line_width=0,
        width=0.6 # Barras un poco más delgadas para elegancia
    )

    fig = apply_wow_layout(fig, f"Perfil de Logros: {est_sel}")
    fig.update_xaxes(visible=False) # Ocultamos eje X porque el texto ya está en la barra
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Análisis cualitativo (asistente)
    st.markdown("---")
    st.subheader("💡 Recomendación Pedagógica Personalizada")
    # ... resto del código del asistente cualitativo ...

# =========================================================================
# === FUNCIONES DE CARGA Y LOGICA DE NEGOCIO (COPIADAS DE EVALUACION.PY) ===
# =========================================================================

def configurar_uploader():
    """Maneja la carga y el procesamiento inicial del archivo Excel."""
    archivo = st.file_uploader("Sube tu archivo .xlsx", type=['xlsx'])
    if archivo:
        with st.spinner("Procesando registro..."):
            df, info_areas = analysis_core.procesar_excel(archivo)
            if df is not None:
                st.session_state['df'] = df
                st.session_state['info_areas'] = info_areas
                st.session_state['df_cargado'] = True
                st.success("¡Datos cargados con éxito!")
                st.rerun()

def descargar_excel_frecuencias(info_areas):
    """Genera un archivo Excel con los datos de frecuencia."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for area, datos in info_areas.items():
            df_area = pd.DataFrame.from_dict(datos['competencias'], orient='index')
            # Extraer frecuencias a columnas
            frec_df = df_area['frecuencias'].apply(pd.Series)
            frec_df.to_excel(writer, sheet_name=area[:30]) # Excel limita nombre hoja a 31 chars
    return output.getvalue()
