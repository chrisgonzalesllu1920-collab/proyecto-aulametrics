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
            st.markdown("<h3 style='color: #1e293b; margin-bottom:20px;'>👤 Análisis Individual</h3>", unsafe_allow_html=True)
            mostrar_analisis_estudiante(df, df_config)
            
        if st.sidebar.button("🗑️ Cargar Nuevo Archivo"):
            for key in ['df_cargado', 'df', 'df_config', 'info_areas', 'general_info']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def configurar_uploader():
    """Configura la zona de carga de archivos con estilo premium."""
    with st.container():
        uploaded_file = st.file_uploader("", type=['xlsx'], help="Cargue el registro auxiliar en formato Excel.")
        
        if uploaded_file is not None:
            with st.spinner('🚀 Procesando datos pedagógicos...'):
                procesar_archivo(uploaded_file)
                st.rerun()

def procesar_archivo(file):
    """Procesa el Excel aplicando el filtro estricto para ignorar hojas de configuración."""
    try:
        xls = pd.ExcelFile(file)
        # FILTRO ESTRICTO: Ignorar "Generalidades" y "Parametros"
        hojas_validas = [sheet for sheet in xls.sheet_names if sheet not in ["Generalidades", "Parametros"]]
        
        if not hojas_validas:
            st.error("No se encontraron hojas de calificación válidas.")
            return

        dict_dfs = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in hojas_validas}
        
        # Simulación de extracción de metadatos (ajustar según estructura real)
        general_info = {
            "institucion": "I.E. Mercedes Cabello",
            "nivel": "Secundaria",
            "grado": "4to",
            "seccion": "B"
        }
        
        # Integración con el core de análisis
        df_consolidado, df_config, info_areas = analysis_core.consolidar_datos(dict_dfs)
        
        st.session_state['df'] = df_consolidado
        st.session_state['df_config'] = df_config
        st.session_state['info_areas'] = info_areas
        st.session_state['general_info'] = general_info
        st.session_state['df_cargado'] = True
        
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")

def mostrar_analisis_general(info_areas):
    """Visualización de alto nivel del rendimiento del aula."""
    cols = st.columns(len(info_areas) if info_areas else 1)
    
    for i, (area, datos) in enumerate(info_areas.items()):
        with cols[i]:
            score = datos['promedio']
            color = "#10b981" if score >= 14 else "#f59e0b" if score >= 11 else "#ef4444"
            st.markdown(f"""
                <div style='background: white; padding: 20px; border-radius: 15px; border-left: 5px solid {color}; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);'>
                    <p style='margin:0; font-size: 0.9rem; color: #64748b; font-weight: 600;'>{area.upper()}</p>
                    <h2 style='margin:0; color: #1e293b;'>{score:.1f}</h2>
                </div>
            """, unsafe_allow_html=True)

    # Gráfico de barras comparativo
    st.markdown("<br>", unsafe_allow_html=True)
    df_plot = pd.DataFrame([{'Área': a, 'Promedio': d['promedio']} for a, d in info_areas.items()])
    fig = px.bar(df_plot, x='Área', y='Promedio', text_auto='.1f',
                 title="Promedio por Área Competencial",
                 color='Promedio', color_continuous_scale='Viridis')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

    # Botones de exportación
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📄 Generar Reporte Excel Profesional"):
            generar_excel_reporte(info_areas)
    with c2:
        if st.button("📊 Exportar Presentación PPTX"):
            generar_pptx_reporte(info_areas)

def mostrar_analisis_estudiante(df, df_config):
    """Interfaz de consulta individual con radar de competencias."""
    estudiante = st.selectbox("Seleccione un estudiante:", df.index.unique())
    
    if estudiante:
        data_est = df.loc[estudiante]
        
        col_radar, col_info = st.columns([2, 1])
        
        with col_radar:
            # Gráfico de Radar
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=data_est.values,
                theta=data_est.index,
                fill='toself',
                line_color='#1E3A8A'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 20])),
                showlegend=False,
                title=f"Perfil de Competencias: {estudiante}"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col_info:
            st.markdown("#### 📝 Resumen")
            promedio_gen = data_est.mean()
            st.metric("Promedio General", f"{promedio_gen:.2f}")
            
            # Recomendación IA básica
            st.info("💡 **Sugerencia Pedagógica:** Reforzar las áreas con puntaje menor a 13 mediante proyectos interdisciplinarios.")

def generar_excel_reporte(info_areas):
    """Genera un archivo Excel con formato avanzado."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Resumen de frecuencias
        resumen_data = []
        for area, d in info_areas.items():
            resumen_data.append({
                'Área': area,
                'Promedio': d['promedio'],
                'Logro Destacado (AD)': d.get('AD', 0),
                'Logrado (A)': d.get('A', 0),
                'En Proceso (B)': d.get('B', 0),
                'En Inicio (C)': d.get('C', 0)
            })
        
        df = pd.DataFrame(resumen_data)
        df.to_excel(writer, sheet_name='frecuencias', index=False)
        
        # Formateo estético con XlsxWriter
        workbook = writer.book
        worksheet = writer.sheets['frecuencias']
        
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#1E3A8A', 'font_color': 'white', 'border': 1
        })
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
    st.download_button(
        label="📥 Descargar Reporte Excel",
        data=output.getvalue(),
        file_name="reporte_pedagogico.xlsx",
        mime="application/vnd.ms-excel"
    )

def generar_pptx_reporte(info_areas):
    """Llama al generador de presentaciones para exportar resultados."""
    try:
        prs_data = pptx_generator.crear_presentacion(info_areas, st.session_state.get('general_info'))
        st.download_button(
            label="📥 Descargar Presentación",
            data=prs_data,
            file_name="analisis_pedagogico.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    except Exception as e:
        st.error(f"Error al generar PPTX: {e}")

# Ejecución (Placeholder para integración)
# if __name__ == "__main__":
#    evaluacion_page(pedagogical_assistant.Asistente())
