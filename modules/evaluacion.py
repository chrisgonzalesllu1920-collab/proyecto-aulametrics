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
        # Botón de reset para limpiar errores de caché de sesión o datos corruptos
        if st.sidebar.button("🗑️ Limpiar datos y subir otro archivo"):
            keys_to_delete = ['df_cargado', 'info_areas', 'all_dataframes', 'df', 'df_config']
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

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
    """Procesa el archivo Excel y maneja posibles errores de lectura."""
    uploaded_file = st.file_uploader(
        "Sube tu archivo de Excel aquí", 
        type=["xlsx", "xls"], 
        key="file_uploader"
    )

    if uploaded_file is not None:
        with st.spinner('Procesando todas las áreas...'):
            try:
                excel_file = pd.ExcelFile(uploaded_file)
                sheet_names = excel_file.sheet_names
                
                # Ignorar hojas administrativas o de configuración
                IGNORE_SHEETS = [analysis_core.GENERAL_SHEET_NAME.lower(), 'parametros', 'generalidades', 'asistencia', 'resumen']
                valid_sheets = [name for name in sheet_names if name.lower() not in IGNORE_SHEETS]

                if not valid_sheets:
                    st.error("No se encontraron hojas de áreas válidas para analizar.")
                    return

                # Llamada al core de análisis
                results_dict = analysis_core.analyze_data(excel_file, valid_sheets)
                
                if not results_dict:
                    st.error("El análisis no devolvió resultados. Verifica el formato de las competencias.")
                    return

                st.session_state.info_areas = results_dict
                st.session_state.df_cargado = True
                
                # Guardar todos los dataframes para la vista individual
                all_dataframes = {}
                for sheet in valid_sheets:
                    try:
                        df_temp = pd.read_excel(uploaded_file, sheet_name=sheet, header=0)
                        all_dataframes[sheet] = df_temp
                    except Exception:
                        pass
                
                st.session_state.all_dataframes = all_dataframes
                if valid_sheets:
                    st.session_state.df = all_dataframes[valid_sheets[0]]
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error crítico al procesar el archivo: {e}")
                st.session_state.df_cargado = False

def mostrar_analisis_general(info_areas):
    """Muestra el resumen con validación robusta para evitar KeyErrors."""
    if not info_areas:
        st.warning("⚠️ No hay datos de áreas disponibles.")
        return

    # Estilos CSS para tablas y niveles
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
        # SOLUCIÓN AL KEYERROR: Verificar existencia de la clave antes de acceder
        if 'df_frecuencias' not in datos:
            st.warning(f"El área '{area}' se omitió porque no contiene una tabla de frecuencias válida.")
            continue

        try:
            with st.container(border=True):
                st.markdown(f"#### 📚 Área: {area}")
                
                df_bar = datos['df_frecuencias'].copy()
                cols_niveles = [c for c in ['AD', 'A', 'B', 'C'] if c in df_bar.columns]
                
                # Renderizar Gráfico de Barras
                fig_bar = go.Figure()
                colores = {'AD': '#166534', 'A': '#22c55e', 'B': '#eab308', 'C': '#ef4444'}
                df_plot = df_bar.iloc[::-1] # Invertir para que la primera competencia salga arriba

                for nivel in cols_niveles:
                    fig_bar.add_trace(go.Bar(
                        name=nivel,
                        y=df_plot.index,
                        x=df_plot[nivel],
                        orientation='h',
                        marker_color=colores.get(nivel),
                        text=df_plot[nivel],
                        textposition='inside',
                        textfont=dict(size=12, color='white')
                    ))

                fig_bar.update_layout(
                    barmode='group',
                    height=250 + (len(df_bar) * 45),
                    margin=dict(l=20, r=20, t=40, b=40),
                    xaxis=dict(title="Estudiantes"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_bar, use_container_width=True)

                # Tabla de Resumen en HTML
                html_table = '<table class="tabla-frecuencias"><thead><tr>'
                for col in df_bar.columns:
                    html_table += f'<th>{col}</th>'
                html_table += '</tr></thead><tbody>'

                for idx, row in df_bar.iterrows():
                    html_table += '<tr>'
                    html_table += f'<td class="col-comp">{idx}</td>'
                    for col in df_bar.columns[1:]: # Asumiendo que la primera col es competencia
                        val = row[col]
                        clase = ""
                        if 'AD' in str(col).upper(): clase = "nivel-ad"
                        elif 'A' in str(col).upper(): clase = "nivel-a"
                        elif 'B' in str(col).upper(): clase = "nivel-b"
                        elif 'C' in str(col).upper(): clase = "nivel-c"
                        html_table += f'<td class="{clase}">{val}</td>'
                    html_table += '</tr>'
                html_table += '</tbody></table>'
                st.markdown(html_table, unsafe_allow_html=True)
                
                # Botones de exportación
                c1, c2 = st.columns(2)
                with c1:
                    excel_data = convert_df_to_excel(df_bar, area, datos.get('general_info', {}))
                    st.download_button(f"📥 Excel {area}", excel_data, f"{area}.xlsx", "application/vnd.ms-excel", key=f"ex_{area}")
                with c2:
                    ppt_buffer = pptx_generator.generate_area_report(area, datos)
                    st.download_button(f"📊 PPTX {area}", ppt_buffer, f"{area}.pptx", key=f"pt_{area}")
        
        except Exception as e:
            st.error(f"Error renderizando el área {area}: {e}")

def mostrar_analisis_por_estudiante(df, df_config, info_areas):
    """Muestra el desempeño individual buscando el nombre en todas las áreas."""
    st.markdown("### 🧑‍🎓 Seguimiento Individual")
    
    if 'all_dataframes' not in st.session_state:
        st.info("Sube un archivo para habilitar el análisis individual.")
        return

    all_dfs = st.session_state.all_dataframes
    posibles_cols = ["ESTUDIANTE", "APELLIDOS Y NOMBRES", "ALUMNO", "NOMBRES"]
    
    # Obtener lista única de estudiantes de la primera hoja
    first_df = next(iter(all_dfs.values()))
    col_est = next((c for c in first_df.columns if str(c).upper() in posibles_cols), None)
    
    if not col_est:
        st.error("No se detectó la columna de nombres de estudiantes.")
        return

    estudiantes = sorted(first_df[col_est].dropna().unique().tolist())
    seleccion = st.selectbox("Seleccione un estudiante:", estudiantes, index=None)

    if seleccion:
        resumen_notas = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        detalles = {'AD': [], 'A': [], 'B': [], 'C': []}

        for area, df_area in all_dfs.items():
            c_local = next((c for c in df_area.columns if str(c).upper() in posibles_cols), None)
            if c_local:
                fila = df_area[df_area[c_local] == seleccion]
                if not fila.empty:
                    for val in fila.iloc[0].values:
                        v_str = str(val).strip().upper()
                        if v_str in resumen_notas:
                            resumen_notas[v_str] += 1
                            detalles[v_str].append(area)

        # Mostrar métricas y gráfico de torta
        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.write(f"**Resultados para {seleccion}:**")
            for k, v in resumen_notas.items():
                st.write(f"- {k}: {v}")
        
        with c2:
            fig = px.pie(
                values=list(resumen_notas.values()), 
                names=list(resumen_notas.keys()),
                color=list(resumen_notas.keys()),
                color_discrete_map={'AD': '#166534', 'A': '#22c55e', 'B': '#eab308', 'C': '#ef4444'}
            )
            st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Resultados')
    return output.getvalue()
