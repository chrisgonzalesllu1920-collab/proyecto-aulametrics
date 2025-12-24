import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import xlsxwriter
import pptx_generator
import pedagogical_assistant

# --- NUEVA FUNCIÓN: Estilos Visuales ---
def inject_custom_styles():
    """Inyecta CSS para mejorar la estética de la Vista Global."""
    st.markdown("""
        <style>
        .area-card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #e6e9ef;
        }
        .area-title {
            color: #1f77b4;
            font-size: 1.4rem;
            font-weight: bold;
            margin-bottom: 15px;
            border-left: 5px solid #1f77b4;
            padding-left: 10px;
        }
        /* Ajuste para que las tablas no tengan scroll innecesario */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
    """, unsafe_allow_html=True)

def evaluacion_page(asistente):
    """Controlador principal del Sistema de Evaluación."""
    if not st.session_state.get('df_cargado', False):
        st.header("📊 Sistema de Evaluación")
        st.info("Para comenzar, sube tu registro de notas (Excel).")
        configurar_uploader()
    else:
        tab_global, tab_individual = st.tabs(["🌎 Vista Global", "👤 Vista por Estudiante"])
        
        with tab_global:
            # Aplicamos los estilos solo en esta vista
            inject_custom_styles()
            st.subheader("Panorama General del Aula")
            info_areas = st.session_state.get('info_areas')
            mostrar_analisis_general(info_areas)
            
        with tab_individual:
            # Nota: Corregido el paso de argumentos según tu definición
            mostrar_analisis_por_estudiante(
                st.session_state.df, 
                st.session_state.df_config, 
                st.session_state.info_areas
            )

def configurar_uploader():
    """Maneja la carga y el procesamiento inicial del archivo Excel."""
    archivo_cargado = st.file_uploader("Elige tu archivo Excel", type=['xlsx', 'xls'])
    if archivo_cargado is not None:
        with st.spinner('Procesando datos...'):
            try:
                resultado = analysis_core.procesar_archivo_evaluacion(archivo_cargado)
                if resultado:
                    st.session_state.df = resultado['df_notas']
                    st.session_state.df_config = resultado['df_config']
                    st.session_state.info_areas = resultado['info_areas']
                    st.session_state.all_dataframes = resultado['all_dataframes']
                    st.session_state.df_cargado = True
                    st.rerun()
            except Exception as e:
                st.error(f"Error al procesar el archivo: {str(e)}")

# --- FUNCIÓN ACTUALIZADA (Vista Global) ---
def mostrar_analisis_general(info_areas):
    """Muestra el resumen estadístico con diseño de tarjetas y tablas estilizadas."""
    if not info_areas:
        st.warning("No hay datos de áreas para mostrar.")
        return

    for area, datos in info_areas.items():
        # Inicio de Tarjeta Personalizada
        st.markdown(f'<div class="area-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="area-title">📚 Área: {area}</div>', unsafe_allow_html=True)
        
        # 1. Métricas de Resumen
        resumen = datos['resumen_frecuencias']
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🏆 AD", resumen.get('AD', 0))
        m2.metric("✅ A", resumen.get('A', 0))
        m3.metric("⚠️ B", resumen.get('B', 0))
        m4.metric("🛑 C", resumen.get('C', 0))

        # 2. Tabla de Frecuencias con Estilo Condicional
        st.write("#### 📊 Distribución por Competencia")
        df_frec = datos['df_frecuencias']
        
        # Aplicamos gradientes para que las notas bajas resalten en rojo y las altas en verde
        st.dataframe(
            df_frec.style.background_gradient(cmap='YlGn', subset=[c for c in df_frec.columns if 'AD' in c or 'A' in c])
            .background_gradient(cmap='OrRd', subset=[c for c in df_frec.columns if 'B' in c or 'C' in c])
            .format(precision=0),
            use_container_width=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 3. Botones de Exportación
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            excel_data = convert_df_to_excel(datos['df_frecuencias'], area, datos['general_info'])
            st.download_button(
                label=f"📥 Descargar Excel - {area}",
                data=excel_data,
                file_name=f"Analisis_{area}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"btn_xl_{area}",
                use_container_width=True
            )
        
        with col_btn2:
            ppt_buffer = pptx_generator.generate_area_report(area, datos)
            st.download_button(
                label=f"📊 Descargar PPTX - {area}",
                data=ppt_buffer,
                file_name=f"Reporte_{area}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                key=f"btn_ppt_{area}",
                use_container_width=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)

def mostrar_analisis_por_estudiante(df, df_config, info_areas):
    """Muestra el perfil INTEGRAL del estudiante."""
    st.markdown("---")
    st.header("🧑‍🎓 Perfil Integral del Estudiante")
    
    if 'all_dataframes' not in st.session_state or not st.session_state.all_dataframes:
        st.warning("⚠️ No se han cargado datos.")
        return

    all_dfs = st.session_state.all_dataframes
    posibles_nombres = ["Estudiante", "ESTUDIANTE", "APELLIDOS Y NOMBRES", "Apellidos y Nombres", "ALUMNO", "Alumno", "Nombres y Apellidos"]
    
    first_sheet_name = next(iter(all_dfs))
    df_base = all_dfs[first_sheet_name]
    col_nombre = next((c for c in df_base.columns if str(c).strip() in posibles_nombres), None)
    
    if not col_nombre:
        st.error(f"❌ No encontramos la columna de nombres.")
        return

    lista_estudiantes = sorted(df_base[col_nombre].dropna().unique())
    estudiante_sel = st.selectbox("🔍 Busca al estudiante:", options=lista_estudiantes, index=None, placeholder="Escribe nombre...")

    if estudiante_sel:
        st.divider()
        st.subheader(f"📊 Reporte Global: {estudiante_sel}")
        total_conteo = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        desglose_areas = {'AD': [], 'A': [], 'B': [], 'C': []}
        areas_analizadas = 0
        
        my_bar = st.progress(0, text="Analizando...")
        for i, (area_name, df_area) in enumerate(all_dfs.items()):
            my_bar.progress((i + 1) / len(all_dfs))
            c_name_local = next((c for c in df_area.columns if str(c).strip() in posibles_nombres), None)
            if c_name_local:
                fila = df_area[df_area[c_name_local] == estudiante_sel]
                if not fila.empty:
                    areas_analizadas += 1
                    vals = [str(v).upper().strip() for v in fila.iloc[0].values]
                    for nivel in total_conteo.keys():
                        c = vals.count(nivel)
                        total_conteo[nivel] += c
                        if c > 0: desglose_areas[nivel].append(f"{area_name} ({c})")
        my_bar.empty()

        col_izq, col_der = st.columns([1, 1.5])
        with col_izq:
            st.markdown("#### 📈 Detalle por Nivel")
            niveles = [('AD', '🏆 Logro Destacado', 'green', False), ('A', '✅ Logro Esperado', 'lightgreen', False),
                       ('B', '⚠️ En Proceso', 'orange', True), ('C', '🛑 En Inicio', 'red', True)]
            for cod, label, color, expand in niveles:
                cant = total_conteo[cod]
                with st.expander(f"{label}: {cant}", expanded=expand if cant > 0 else False):
                    if cant > 0:
                        if cod in ['B', 'C']: st.markdown(f"**:{color}[Reforzar en:]**")
                        for a in desglose_areas[cod]: st.markdown(f"- {a}")
                    else: st.write("Sin registros.")

        with col_der:
            if sum(total_conteo.values()) > 0:
                df_chart = pd.DataFrame({'Nivel': list(total_conteo.keys()), 'Cantidad': list(total_conteo.values())})
                df_chart = df_chart[df_chart['Cantidad'] > 0]
                fig = px.pie(df_chart, values='Cantidad', names='Nivel', hole=0.4,
                             color='Nivel', color_discrete_map={'AD': '#2E7D32', 'A': '#66BB6A', 'B': '#FFA726', 'C': '#EF5350'})
                st.plotly_chart(fig, use_container_width=True)

        # Informe Word
        st.write("---")
        doc_buffer = pedagogical_assistant.generar_reporte_estudiante(estudiante_sel, total_conteo, desglose_areas)
        st.download_button(label="📄 Descargar Informe de Progreso (Word)", data=doc_buffer,
                           file_name=f"Informe_{estudiante_sel.replace(' ', '_')}.docx", use_container_width=True)

@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    """Convierte DataFrame a Excel con formato profesional."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        info_sheet = workbook.add_worksheet("Generalidades")
        bold_fmt = workbook.add_format({'bold': True, 'font_size': 12})
        info_sheet.write('A1', 'Área:', bold_fmt)
        info_sheet.write('B1', area_name)
        info_sheet.write('A2', 'Nivel:', bold_fmt)
        info_sheet.write('B2', general_info.get('nivel', 'N/A'))
        
        df.to_excel(writer, sheet_name='Frecuencias', index=True)
        worksheet = writer.sheets['Frecuencias']
        fmt_header = workbook.add_format({'bg_color': '#D3D3D3', 'bold': True, 'border': 1, 'align': 'center'})
        worksheet.set_column('A:A', 60)
        worksheet.set_column('B:Z', 10)
    return output.getvalue()
