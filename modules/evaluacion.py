import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter
import pedagogical_assistant
import colorsys  # CAMBIO: Import para manejar colores
import re
import time
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image as PILImage
import plotly.io as pio

# --- CONFIGURACIÓN DE ESTÉTICA POWER BI ---
PBI_BLUE = "#113770"
PBI_LIGHT_BLUE = "#0078D4"
PBI_BG = "#F9FAFB"  # Blanco humo más profesional y limpio
PBI_CARD_BG = "#FFFFFF"
# Paleta de colores oficial de Power BI para niveles
COLORS_NIVELES = {
    'AD': '#008450',  # Verde oscuro
    'A': '#32CD32',  # Verde lima
    'B': '#FFB900',  # Dorado/Amarillo
    'C': '#E81123'  # Rojo
}

# CAMBIO: Función para oscurecer un color HEX (más intenso/borde reforzado)
def darken_color(hex_color, factor=0.7):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    hls = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    new_l = max(0, min(1, hls[1] * factor))
    new_rgb = colorsys.hls_to_rgb(hls[0], new_l, hls[2])
    new_hex = '#%02x%02x%02x' % (int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255))
    return new_hex

def evaluacion_page(asistente):
    """Punto de entrada compatible con app.py"""
    inject_pbi_css()
   
    if not st.session_state.get('df_cargado', False):
        st.markdown(f"<h1 class='pbi-header'>📊 Dashboard de Evaluación</h1>", unsafe_allow_html=True)
        configurar_uploader()
    else:
        # MODIFICACIÓN: agregamos la tercera pestaña
        tab_global, tab_individual, tab_comparar = st.tabs([
            "🌎 VISTA GLOBAL DEL AULA",
            "👤 PERFIL POR ESTUDIANTE",
            "📈 COMPARAR PERÍODOS"              # ← Nueva pestaña
        ])
       
        with tab_global:
            info_areas = st.session_state.get('info_areas', {})
            mostrar_analisis_general(info_areas)
           
        with tab_individual:
            df_first = st.session_state.get('df')
            df_config = st.session_state.get('df_config')
            info_areas = st.session_state.get('info_areas')
            mostrar_analisis_por_estudiante(df_first, df_config, info_areas)
        
        with tab_comparar:
            mostrar_comparacion_entre_periodos()

def mostrar_analisis_general(results):
    """Lógica original con diseño avanzado de Power BI"""
    st.markdown(f"<h2 class='pbi-header'>Resultados Consolidados por Área</h2>", unsafe_allow_html=True)
    
    # Mensaje amigable para hojas ignoradas (opción 2)
    ignored_sheets = [name for name, data in results.items() if data.get('ignored', False)]
    if ignored_sheets:
        st.info(
            f"Nota: Se ignoraron automáticamente las hojas de: {', '.join(ignored_sheets)}. "
            "Solo se analizaron las áreas con competencias válidas.",
            icon="ℹ️"
        )
    
    # Filtrar solo áreas válidas (con competencias)
    valid_areas = {name: data for name, data in results.items() if 'competencias' in data and data['competencias']}
    
    if not valid_areas:
        st.warning("No se encontraron áreas con competencias válidas para procesar.")
        return
    
    # Mostrar badges o chips solo de áreas válidas
    cols = st.columns(len(valid_areas))
    for i, (area_name, data) in enumerate(valid_areas.items()):
        with cols[i]:
            st.markdown(f"● {area_name}")
    
    # Contexto del grupo (incluyendo Sección)
    first_sheet_key = next(iter(results), None)
    general_data = {}
    if first_sheet_key and 'generalidades' in results[first_sheet_key]:
        general_data = results[first_sheet_key]['generalidades']
        nivel = general_data.get('nivel', 'Descon.')
        grado = general_data.get('grado', 'Descon.')
        seccion = general_data.get('seccion', 'Descon.')  # ← Nueva línea
        st.markdown(f"""
            <div class='pbi-card' style='padding: 10px 20px; border-left: 5px solid {PBI_LIGHT_BLUE}; margin-bottom: 25px;'>
                <span style='color: #666; font-size: 0.8rem;'>CONTEXTO DEL GRUPO</span><br>
                <span style='font-size: 1.1rem; font-weight: bold; color: {PBI_BLUE};'>
                    Nivel {nivel} | Grado {grado} | Sección {seccion}
                </span>
            </div>
        """, unsafe_allow_html=True)
    
    # Sidebar de Configuración (Power BI Slicer Style)
    with st.sidebar:
        st.markdown(f"<h3 style='color:{PBI_BLUE}; border-bottom: 1px solid #ccc; padding-bottom:5px;'>⚙️ Visualización</h3>", unsafe_allow_html=True)
        chart_options = (
            'Barras (Clásico PBI)',
            'Anillo (Proporción)',
            'Mapa de Árbol (Jerarquía)',
            'Radar de Competencias',
            'Solar (Sunburst)'
        )
        st.session_state.chart_type = st.radio("Seleccionar Visual:", chart_options, key="chart_radio_pbi")
        st.info("Tip: Los gráficos son interactivos. Haz clic en las leyendas para filtrar niveles.")
    
    # Tabs solo con áreas válidas
    tabs = st.tabs([f"📍 {sheet_name}" for sheet_name in valid_areas.keys()])
    for i, (sheet_name, result) in enumerate(valid_areas.items()):
        with tabs[i]:
            # Definimos competencias antes del for
            competencias = result.get('competencias', {})
            
            if not competencias:
                st.info(f"Sin datos en '{sheet_name}'.")
                continue
            
            # --- TABLA DE DATOS (ESTILO PBI) ---
            st.markdown("<div class='pbi-card'><b>1. Matriz de Frecuencias de Evaluación</b>", unsafe_allow_html=True)
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
            st.download_button(label=f"⬇️ Exportar Datos a Excel", data=excel_data,
                              file_name=f'Reporte_PBI_{sheet_name}.xlsx', key=f'btn_dl_{i}')
            st.markdown("</div>", unsafe_allow_html=True)
            
            # --- GRÁFICOS INTERACTIVOS ---
            st.markdown(f"<div class='pbi-card'><b>2. Visualización Dinámica: {st.session_state.chart_type}</b>", unsafe_allow_html=True)
            competencia_nombres_limpios = df_table.index.tolist()
            selected_comp = st.selectbox(f"Filtrar por Competencia específica:", options=competencia_nombres_limpios, key=f'sel_{sheet_name}_{i}')
            if selected_comp:
                df_plot = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']].reset_index()
                df_plot.columns = ['Nivel', 'Estudiantes']
                df_plot['Nivel'] = df_plot['Nivel'].str.replace(' (Est.)', '', regex=False)
               
                if st.session_state.chart_type == 'Barras (Clásico PBI)':
                    fig = px.bar(df_plot, x='Nivel', y='Estudiantes', color='Nivel',
                                  text='Estudiantes', color_discrete_map=COLORS_NIVELES)
                    # CAMBIO: Bordes personalizados por barra (más intensos)
                    for trace in fig.data:
                        fill_color = trace.marker.color
                        dark_color = darken_color(fill_color)
                        trace.marker.line = dict(color=dark_color, width=2)
                    fig.update_traces(textposition='outside')
                
                elif st.session_state.chart_type == 'Anillo (Proporción)':
                    fig = px.pie(df_plot, values='Estudiantes', names='Nivel', hole=0.6,
                                  color='Nivel', color_discrete_map=COLORS_NIVELES)
                    # CAMBIO: Bordes personalizados por sector (más intensos)
                    colors = fig.data[0].marker.colors
                    dark_colors = [darken_color(c) for c in colors]
                    fig.update_traces(textinfo='percent+label', marker=dict(line=dict(color=dark_colors, width=2)))
                
                elif st.session_state.chart_type == 'Mapa de Árbol (Jerarquía)':
                    fig = px.treemap(df_plot, path=['Nivel'], values='Estudiantes',
                                      color='Nivel', color_discrete_map=COLORS_NIVELES)
                    # CAMBIO: Bordes personalizados por rectángulo (más intensos)
                    colors = fig.data[0].marker.colors
                    dark_colors = [darken_color(c) for c in colors]
                    fig.update_traces(marker=dict(line=dict(color=dark_colors, width=2)))
                
                elif st.session_state.chart_type == 'Radar de Competencias':
                    # CAMBIO: Relleno original, borde más intenso
                    fig = go.Figure(data=go.Scatterpolar(
                        r=df_plot['Estudiantes'],
                        theta=df_plot['Nivel'],
                        fill='toself',
                        fillcolor=PBI_LIGHT_BLUE,  # Relleno original
                        line=dict(color=darken_color(PBI_LIGHT_BLUE), width=3)  # Borde más intenso
                    ))
               
                elif st.session_state.chart_type == 'Solar (Sunburst)':
                    fig = px.sunburst(df_plot, path=['Nivel'], values='Estudiantes',
                                       color='Nivel', color_discrete_map=COLORS_NIVELES)
                    # CAMBIO: Bordes personalizados por sector (más intensos)
                    colors = fig.data[0].marker.colors
                    dark_colors = [darken_color(c) for c in colors]
                    fig.update_traces(marker=dict(line=dict(color=dark_colors, width=2)))
                
                fig.update_layout(
                    margin=dict(t=40, b=20, l=20, r=20),
                    height=450,
                    font_family="Segoe UI",
                    font=dict(size=12),
                    hovermode="closest",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True, key=f"plotly_v2_{sheet_name}_{selected_comp}_{i}")
            st.markdown("</div>", unsafe_allow_html=True)
            if st.button(f"💡 Ideas de mejora IA para {sheet_name}", type="primary", use_container_width=True, key=f"btn_ai_{i}"):
                with st.expander("Panel de Sugerencias Pedagógicas (Generado por IA)", expanded=True):
                    ai_text = pedagogical_assistant.generate_suggestions(results, sheet_name, selected_comp)
                    st.markdown(f"<div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid {PBI_BLUE};'>{ai_text}</div>", unsafe_allow_html=True)

def extraer_periodo_de_generalidades(excel_file):
    """
    Extrae el período de evaluación desde la hoja 'Generalidades'
    Busca específicamente la fila con 'Período de evaluación :' y toma el valor de la columna siguiente
    """
    if "Generalidades" not in excel_file.sheet_names:
        return {
            "periodo": "Hoja 'Generalidades' no encontrada",
            "grado": "No encontrado",
            "seccion": "No encontrado"
        }
   
    try:
        # Leemos la hoja sin encabezados para preservar todo el formato
        df_gen = pd.read_excel(excel_file, sheet_name="Generalidades", header=None)
       
        # Convertimos todo a string para búsqueda segura
        df_gen = df_gen.astype(str).apply(lambda x: x.str.strip())
       
        # Buscamos la fila donde aparece "Período de evaluación" (insensible a mayúsculas)
        mask = df_gen.apply(lambda row: row.str.contains("período de evaluación", case=False).any(), axis=1)
       
        if not mask.any():
            return {
                "periodo": "Texto 'Período de evaluación' no encontrado",
                "grado": "No encontrado",
                "seccion": "No encontrado"
            }
       
        # Tomamos la primera fila que coincida
        row_idx = mask.idxmax()
        row = df_gen.iloc[row_idx]
       
        # Buscamos la posición del texto en la fila
        col_idx = row[row.str.contains("período de evaluación", case=False)].index[0]
       
        result = {"periodo": "No encontrado", "grado": "No encontrado", "seccion": "No encontrado"}
       
        # Extraemos período (hasta 10 columnas a la derecha, por si hay espacios)
        for offset in range(1, 11):
            col_try = col_idx + offset
            if col_try < len(row):
                valor = row[col_try].strip()
                if valor and valor.lower() != "nan" and valor != "":
                    result["periodo"] = valor.title()
                    break
       
        # Extraemos grado: buscamos "grado :" en la misma fila
        mask_grado = row.str.contains("grado :", case=False)
        if mask_grado.any():
            col_grado = mask_grado.idxmax()
            for offset in range(1, 6):
                col_try = col_grado + offset
                if col_try < len(row):
                    valor = row[col_try].strip()
                    if valor and valor.lower() != "nan" and valor != "":
                        result["grado"] = valor.title()
                        break
       
        # Extraemos sección: buscamos "sección :" en la misma fila
        mask_seccion = row.str.contains("sección :", case=False)
        if mask_seccion.any():
            col_seccion = mask_seccion.idxmax()
            for offset in range(1, 6):
                col_try = col_seccion + offset
                if col_try < len(row):
                    valor = row[col_try].strip()
                    if valor and valor.lower() != "nan" and valor != "":
                        result["seccion"] = valor.upper()  # Sección suele ser mayúscula (A, B...)
                        break
       
        return result
   
    except Exception as e:
        return {
            "periodo": f"Error al leer: {str(e)}",
            "grado": "Error",
            "seccion": "Error"
        }


# ----------------------------------------------------------------------
# NUEVA FUNCIÓN PRINCIPAL PARA LA PESTAÑA DE COMPARACIÓN
# ----------------------------------------------------------------------
def mostrar_comparacion_entre_periodos():
    st.markdown("<h2 class='pbi-header'>📈 Comparación entre Períodos</h2>", unsafe_allow_html=True)

    # Timestamp para keys dinámicas: solo cambia cuando reiniciamos explícitamente
    if 'reset_timestamp' not in st.session_state:
        st.session_state['reset_timestamp'] = time.time()
    
    reset_timestamp = st.session_state['reset_timestamp']
    uploader_key1 = f"comparacion_file1_{reset_timestamp}"
    uploader_key2 = f"comparacion_file2_{reset_timestamp}"
    
    st.info("""
    Carga dos archivos Excel con la misma estructura para comparar el desempeño
    del aula entre dos momentos diferentes (bimestres, trimestres, etc.).
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Período 1 (anterior/base)")
        file1 = st.file_uploader(
            "Selecciona el archivo del primer período",
            type=["xlsx"],
            key=uploader_key1,  # ← Key dinámica
            help="Archivo base para la comparación"
        )
       
        if file1 is not None:
            try:
                excel1 = pd.ExcelFile(file1)
                info1 = extraer_periodo_de_generalidades(excel1)
                st.success("Archivo cargado correctamente")
                st.markdown(f"**Período:** {info1['periodo']}")
                st.markdown(f"**Grado:** {info1['grado']}")
                st.markdown(f"**Sección:** {info1['seccion']}")
                st.session_state['excel_periodo1'] = excel1
                st.session_state['info_periodo1'] = info1
            except Exception as e:
                st.error(f"Error al procesar el primer archivo: {str(e)}")

    with col2:
        st.subheader("Período 2 (actual/comparación)")
        file2 = st.file_uploader(
            "Selecciona el archivo del segundo período",
            type=["xlsx"],
            key=uploader_key2,  # ← Key dinámica
            help="Archivo que se comparará con el primero"
        )
       
        if file2 is not None:
            try:
                excel2 = pd.ExcelFile(file2)
                info2 = extraer_periodo_de_generalidades(excel2)
                st.success("Archivo cargado correctamente")
                st.markdown(f"**Período:** {info2['periodo']}")
                st.markdown(f"**Grado:** {info2['grado']}")
                st.markdown(f"**Sección:** {info2['seccion']}")
                st.session_state['excel_periodo2'] = excel2
                st.session_state['info_periodo2'] = info2
            except Exception as e:
                st.error(f"Error al procesar el segundo archivo: {str(e)}")

    # Validación de compatibilidad
    if 'info_periodo1' in st.session_state and 'info_periodo2' in st.session_state:
        info1 = st.session_state['info_periodo1']
        info2 = st.session_state['info_periodo2']
       
        # Verificamos si grado y sección coinciden (ignoramos si no se detectaron)
        if (info1['grado'] != "No encontrado" and info2['grado'] != "No encontrado" and
            info1['grado'] != info2['grado']) or \
           (info1['seccion'] != "No encontrado" and info2['seccion'] != "No encontrado" and
            info1['seccion'] != info2['seccion']):
            st.error("""
            ❌ **Error de compatibilidad**
            Los dos archivos pertenecen a **grados o secciones diferentes**.
            No se puede comparar el desempeño entre grupos distintos.
            Por favor, carga archivos del **mismo grado y sección**.
            """)
            # Limpiamos para obligar recarga
            if 'excel_periodo2' in st.session_state:
                del st.session_state['excel_periodo2']
                del st.session_state['info_periodo2']
            return
       
        st.markdown("---")
        st.success("¡Ambos periodos están cargados y son compatibles! Listo para comparar.")
       
        st.markdown("### Comparación entre:")
        st.markdown(f"""
        **🡅 {info1['periodo']}**
        Grado: {info1['grado']} | Sección: {info1['seccion']}
       
        **🡇 {info2['periodo']}**
        Grado: {info2['grado']} | Sección: {info2['seccion']}
        """, unsafe_allow_html=True)
       
        # Botón "Procesar" (con key para evitar duplicados)
        if st.button("🔄 Procesar ambos periodos y comparar", type="primary", use_container_width=True, key="procesar_comparacion"):
            with st.spinner("Procesando datos de ambos períodos..."):
                try:
                    hojas_validas = [s for s in st.session_state['excel_periodo1'].sheet_names 
                                    if s != "Generalidades" and s != "Parametros"]

                    results1 = analysis_core.analyze_data(st.session_state['excel_periodo1'], hojas_validas)
                    results2 = analysis_core.analyze_data(st.session_state['excel_periodo2'], hojas_validas)

                    st.session_state['results_periodo1'] = results1
                    st.session_state['results_periodo2'] = results2

                    st.success("¡Datos procesados correctamente!")
                except Exception as e:
                    st.error(f"Error al procesar los datos: {str(e)}")
                    return

        # Botón "Nuevo análisis" - aparece SOLO después de procesar
        if 'results_periodo1' in st.session_state and 'results_periodo2' in st.session_state:
            st.markdown("---")
            if st.button("Nuevo análisis", type="primary", use_container_width=True, help="Inicia una nueva comparación desde cero"):
                st.session_state["confirm_reset"] = True  # Activar confirmación
            
            # Mostrar confirmación si está activada
            if st.session_state.get("confirm_reset", False):
                st.warning("¿Estás seguro de querer iniciar un **nuevo análisis**? Se perderán todos los datos actuales.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Sí, confirmar y limpiar", type="primary", use_container_width=True):
                        # Limpieza completa: borramos TODAS las claves relacionadas
                        keys_to_clear = [
                            'excel_periodo1', 'excel_periodo2',
                            'info_periodo1', 'info_periodo2',
                            'results_periodo1', 'results_periodo2',
                            'comparacion_file1', 'comparacion_file2',  # Claves de los uploaders
                            'todas_competencias', 'competencias_comparar', 'tipo_grafico_comparacion'  # Selecciones
                        ]
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        # Limpieza de caché para reinicio total
                        st.cache_data.clear()
                        st.session_state['reset_timestamp'] = time.time()  # Nuevo timestamp → uploaders se recrean
                        
                        st.session_state["confirm_reset"] = False
                        st.success("¡Comparación reiniciada completamente! Listo para cargar nuevos archivos.")
                        st.rerun()  # ← Corregido: sin "experimental"
                with col_no:
                    if st.button("No, cancelar", use_container_width=True):
                        st.session_state["confirm_reset"] = False
                        st.info("Acción cancelada.")
       
    elif 'excel_periodo1' in st.session_state or 'excel_periodo2' in st.session_state:
        st.warning("Carga el segundo archivo para comenzar la comparación.")
    else:
        st.info("Carga ambos archivos para iniciar la comparación entre períodos.")
   
    # ------------------------------------------------
    # Selección de competencias a comparar y visualizaciones
    # ------------------------------------------------
    if 'results_periodo1' in st.session_state and 'results_periodo2' in st.session_state:
        results1 = st.session_state['results_periodo1']
        results2 = st.session_state['results_periodo2']

        st.subheader("Seleccione qué comparar")

        # Obtenemos las competencias disponibles desde la primera hoja válida
        competencias_disponibles = []
        if results1:
            primera_hoja = next(iter(results1))
            competencias_disponibles = list(results1[primera_hoja].get('competencias', {}).keys())

        todas_competencias = st.checkbox("Comparar TODAS las competencias", value=True, key="todas_competencias")

        competencias_sel = []
        if not todas_competencias:
            competencias_sel = st.multiselect(
                "Seleccione las competencias específicas a comparar",
                options=competencias_disponibles,
                default=competencias_disponibles[:3] if competencias_disponibles else [],
                key="competencias_comparar"
            )

        competencias_a_mostrar = competencias_disponibles if todas_competencias else competencias_sel

        if not competencias_a_mostrar:
            st.info("Seleccione al menos una competencia para comparar.")
        else:
            st.subheader("Visualizaciones comparativas")

            tipo_grafico = st.radio(
                "Tipo de visualización",
                options=[
                    "Barras agrupadas (AD/A/B/C por período)",
                    "Barras apiladas (distribución %)",
                    "Líneas - Evolución % Destacado + Logrado (AD+A)"
                ],
                horizontal=True,
                key="tipo_grafico_comparacion"
            )

            for competencia_original in competencias_a_mostrar:
                nombre_limpio = "Competencia desconocida"
                for hoja in results1:
                    comp_data = results1[hoja].get('competencias', {}).get(competencia_original)
                    if comp_data and 'nombre_limpio' in comp_data:
                        nombre_limpio = comp_data['nombre_limpio']
                        break

                with st.expander(f"Competencia: {nombre_limpio}", expanded=True):
                    # ... (el resto del código de métricas, tabla y gráficos que ya tenías va aquí)
                    # Puedes pegar tu código anterior de métricas, deltas, tabla y gráficos
                            
                            # Buscamos la competencia en alguna de las hojas
                            data1 = None
                            for hoja in results1:
                                comp_data = results1[hoja].get('competencias', {}).get(competencia_original)
                                if comp_data:
                                    data1 = comp_data
                                    break

                            data2 = None
                            for hoja in results2:
                                comp_data = results2[hoja].get('competencias', {}).get(competencia_original)
                                if comp_data:
                                    data2 = comp_data
                                    break

                            if not data1 or not data2:
                                st.warning("No se encontraron datos completos para esta competencia en uno de los períodos.")
                                continue

                            # Conteos y porcentajes por nivel
                            conteos1 = data1.get('conteo_niveles', {})
                            total1 = data1.get('total_evaluados', 1)
                            pct1 = {k: (v / total1 * 100) if total1 > 0 else 0 for k, v in conteos1.items()}

                            conteos2 = data2.get('conteo_niveles', {})
                            total2 = data2.get('total_evaluados', 1)
                            pct2 = {k: (v / total2 * 100) if total2 > 0 else 0 for k, v in conteos2.items()}

                            niveles = ['AD', 'A', 'B', 'C']
                            valores1 = [conteos1.get(n, 0) for n in niveles]
                            valores2 = [conteos2.get(n, 0) for n in niveles]

                            # Deltas por nivel (P2 - P1)
                            deltas = {n: pct2.get(n, 0) - pct1.get(n, 0) for n in niveles}

                            # Colores condicionales por nivel (lógica pedagógica)
                            color_rules = {
                                'AD': lambda d: "green" if d > 0 else "red" if d < 0 else "gray",
                                'A': lambda d: "green" if d > 0 else "red" if d < 0 else "gray",
                                'B': lambda d: "green" if d > 0 else "orange" if d < 0 else "gray",  # ↓ en B puede ser bueno (suben a A)
                                'C': lambda d: "green" if d < 0 else "red" if d > 0 else "gray"     # ↓ en C SIEMPRE positivo
                            }

                            # Métricas separadas por nivel (con flecha y color)
                            cols = st.columns(4)
                            for i, nivel in enumerate(niveles):
                                delta = deltas[nivel]
                                color = color_rules[nivel](delta)
                                flecha = "↑" if delta > 0 else "↓" if delta < 0 else "→"
                                with cols[i]:
                                    st.metric(
                                        label=f"% {nivel}",
                                        value=f"{pct2.get(nivel, 0):.1f}%",
                                        delta=f"{delta:+.1f}%",
                                        delta_color="normal"  # Usamos color manual abajo
                                    )
                                    st.markdown(f"""
                                    <div style="font-size: 1.5rem; color: {color}; text-align: center; margin-top: -10px;">
                                        {flecha}
                                    </div>
                                    """, unsafe_allow_html=True)

                            # Tabla comparativa mejorada con deltas y colores
                            st.markdown("**Tabla comparativa detallada**")
                            tabla = pd.DataFrame({
                                'Nivel': niveles,
                                f'Conteos {info1["periodo"]}': valores1,
                                f'% {info1["periodo"]}': [f"{pct1.get(n, 0):.1f}%" for n in niveles],
                                f'Conteos {info2["periodo"]}': valores2,
                                f'% {info2["periodo"]}': [f"{pct2.get(n, 0):.1f}%" for n in niveles],
                                'Δ %': [f"{d:+.1f}%" for d in deltas.values()],
                                'Tendencia': [flecha + (" mejora" if d > 0 else " ↓ mejora" if d < 0 and n == 'C' else " ↓ retroceso" if d < 0 else " estable") 
                                              for d, n in zip(deltas.values(), niveles)]
                            })

                            # Estilo condicional en la tabla (verde/rojo/naranja)
                            def style_delta(val):
                                color = 'green' if float(val.strip('%+')) > 0 else 'red' if float(val.strip('%+')) < 0 else 'gray'
                                return f'color: {color}; font-weight: bold'

                            st.dataframe(
                                tabla.style.map(style_delta, subset=['Δ %']),
                                use_container_width=True
                            )

                            # Preparación de datos comunes para los gráficos
                            niveles = ['AD', 'A', 'B', 'C']
                            valores1 = [conteos1.get(n, 0) for n in niveles]
                            valores2 = [conteos2.get(n, 0) for n in niveles]

                            df_comp = pd.DataFrame({
                                'Nivel': niveles * 2,
                                'Estudiantes': valores1 + valores2,
                                'Período': [info1['periodo']] * 4 + [info2['periodo']] * 4
                            })

                            if tipo_grafico == "Barras agrupadas (AD/A/B/C por período)":
                                fig = px.bar(df_comp, x='Nivel', y='Estudiantes', color='Período',
                                             barmode='group', text='Estudiantes',
                                             color_discrete_sequence=[PBI_LIGHT_BLUE, "#FF6B6B"])
                                fig.update_traces(textposition='outside')
                                st.plotly_chart(fig, use_container_width=True)

                            elif tipo_grafico == "Barras apiladas (distribución %)":
                                df_pct = pd.DataFrame({
                                    'Nivel': niveles,
                                    info1['periodo']: [pct1.get(n, 0) for n in niveles],
                                    info2['periodo']: [pct2.get(n, 0) for n in niveles]
                                }).set_index('Nivel')
                                fig = px.bar(df_pct, barmode='stack', text_auto='.1f',
                                             color_discrete_sequence=['#008450','#32CD32','#FFB900','#E81123'])
                                st.plotly_chart(fig, use_container_width=True)

                            elif tipo_grafico == "Líneas - Evolución % Destacado + Logrado (AD+A)":
                                pct_ad_a_1 = pct1.get('AD', 0) + pct1.get('A', 0)
                                pct_ad_a_2 = pct2.get('AD', 0) + pct2.get('A', 0)

                                df_line = pd.DataFrame({
                                    'Período': [info1['periodo'], info2['periodo']],
                                    '% AD + A': [pct_ad_a_1, pct_ad_a_2]
                                })

                                # Escala dinámica (ya implementada antes)
                                min_pct = min(pct_ad_a_1, pct_ad_a_2) - 5
                                max_pct = max(pct_ad_a_1, pct_ad_a_2) + 5
                                range_y = [max(0, min_pct), min(100, max_pct)]

                                fig = px.line(df_line, x='Período', y='% AD + A', markers=True,
                                              range_y=range_y, text='% AD + A')
                                fig.update_traces(textposition='top center')
                                st.plotly_chart(fig, use_container_width=True)

          
                                        # Guardamos la última fig (la del gráfico seleccionado)
                                        if 'fig' in locals():
                                            st.session_state.last_fig = fig
                            
                                        # Botón de descarga PDF (fuera del bucle, al final de la sección)
                                        if 'last_fig' in st.session_state and st.session_state.last_fig is not None:
                                            # Usamos 'hoja' como nombre del área (es la variable que usas en el loop for hoja in results1)
                                            area_limpia = hoja.replace(" ", "-")  # ← Esta línea resuelve el NameError
                            
                                            periodo1 = info1['periodo'].replace(" ", "_").replace("/", "-")
                                            periodo2 = info2['periodo'].replace(" ", "_").replace("/", "-")
                                            nombre_archivo = f"Comparación_{periodo1}_vs_{periodo2}_{area_limpia}.pdf"
                            
                                            pdf_data = generar_pdf_comparacion(
                                                st.session_state.last_fig,
                                                area_limpia,
                                                info1,
                                                info2,
                                                general_data
                                            )
                            
                                            st.download_button(
                                                label="⬇️ Descargar comparación en PDF",
                                                data=pdf_data,
                                                file_name=nombre_archivo,
                                                mime="application/pdf",
                                                key=f"btn_pdf_comparacion_{int(time.time())}"  # Key única para evitar removeChild
                                            )

def mostrar_analisis_por_estudiante(df_first, df_config, info_areas):
    """Perfil individual con tarjetas de KPI estilo Power BI"""
    st.markdown(f"<h2 class='pbi-header'>Perfil Integral del Estudiante</h2>", unsafe_allow_html=True)
   
    all_dfs = st.session_state.get('all_dataframes', {})
    if not all_dfs:
        st.warning("⚠️ No se detectaron datos en la sesión actual.")
        return
    posibles = ["Estudiante", "ESTUDIANTE", "APELLIDOS Y NOMBRES", "Apellidos y Nombres", "Nombres"]
    first_sheet = next(iter(all_dfs))
    df_base = all_dfs[first_sheet]
    col_nombre = next((c for c in df_base.columns if str(c).strip() in posibles), None)
    if not col_nombre:
        st.error("Error estructural: No se localizó la columna de identidad del estudiante.")
        return
    estudiante_sel = st.selectbox("👤 Seleccionar Estudiante para análisis focalizado:",
                                options=df_base[col_nombre].dropna().unique(),
                                index=None, key="pbi_student_selector")
    if estudiante_sel:
        st.markdown(f"<div class='pbi-card'><h3 style='color:{PBI_BLUE}; margin-top:0;'>Estudiante: {estudiante_sel}</h3>", unsafe_allow_html=True)
       
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
        cols = st.columns(4)
        for idx, (n, label) in enumerate([('AD', 'Destacado'), ('A', 'Logrado'), ('B', 'Proceso'), ('C', 'Inicio')]):
            with cols[idx]:
                st.markdown(f"""
                    <div style='background: {COLORS_NIVELES[n]}; padding: 15px; border-radius: 5px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.15); border: 1px solid rgba(0,0,0,0.1);'>
                        <div style='font-size: 0.8rem; opacity: 0.9;'>{label}</div>
                        <div style='font-size: 1.8rem; font-weight: bold;'>{total_conteo[n]}</div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
       
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("<b>Distribución por Competencias</b>", unsafe_allow_html=True)
            for n, label in [('AD', '🏆 Destacado'), ('A', '✅ Logrado'), ('B', '⚠️ Proceso'), ('C', '🛑 Inicio')]:
                if total_conteo[n] > 0:
                    with st.expander(f"{label}: {total_conteo[n]}"):
                        for a in desglose_areas[n]: st.write(f"• {a}")
       
        with c2:
            fig = px.pie(values=list(total_conteo.values()), names=list(total_conteo.keys()), hole=0.5,
                        color=list(total_conteo.keys()), color_discrete_map=COLORS_NIVELES)
            # CAMBIO: Bordes personalizados por sector (más intensos)
            colors = fig.data[0].marker.colors
            dark_colors = [darken_color(c) for c in colors]
            fig.update_traces(marker=dict(line=dict(color=dark_colors, width=2)))
            fig.update_layout(showlegend=True, height=280, margin=dict(t=0, b=0, l=0, r=0),
                            legend=dict(orientation="v", x=1))
            st.plotly_chart(fig, use_container_width=True, key=f"pie_ind_pbi_{estudiante_sel}")
       
        doc_buffer = pedagogical_assistant.generar_reporte_estudiante(estudiante_sel, total_conteo, desglose_areas)
        st.download_button(label="📥 Descargar Informe Individual (Word)", data=doc_buffer,
                          file_name=f"Informe_{estudiante_sel}.docx", use_container_width=True, key=f"dl_word_{estudiante_sel}")
        st.markdown("</div>", unsafe_allow_html=True)

@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Escribir la tabla empezando en fila 3 (deja espacio arriba para título)
        df.to_excel(writer, sheet_name='Frecuencias', index=True, startrow=2, startcol=0)
        
        workbook = writer.book
        worksheet = writer.sheets['Frecuencias']
        
        # Formatos para encabezados por nivel
        header_formats = {
            'AD': workbook.add_format({'bg_color': '#008450', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'}),
            'A': workbook.add_format({'bg_color': '#32CD32', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'}),
            'B': workbook.add_format({'bg_color': '#FFB900', 'font_color': 'black', 'bold': True, 'border': 1, 'align': 'center'}),
            'C': workbook.add_format({'bg_color': '#E81123', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'}),
            'default': workbook.add_format({'bg_color': '#113770', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})
        }
        
        # Formato para celdas de datos
        fmt_data = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0'})
        fmt_percent = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.0%'})
        fmt_total = workbook.add_format({'bg_color': '#E2E8F0', 'bold': True, 'border': 1, 'align': 'center'})
        
        # Ajustar anchos de columnas
        worksheet.set_column('A:A', 50, fmt_data)
        worksheet.set_column('B:J', 12, fmt_data)
        
        # Aplicar formato a encabezados (según nivel)
        header_row = 2  # Fila de encabezados (startrow=2)
        for col_num, col_name in enumerate(df.columns):
            level = col_name.split(' ')[0]
            fmt = header_formats.get(level, header_formats['default'])
            worksheet.write(header_row, col_num + 1, col_name, fmt)  # +1 por índice
        
        # Título fusionado arriba (sin afectar la tabla)
        title_format = workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'center', 'bg_color': '#E2E8F0', 'border': 1
        })
        title_text = f"Área: {area_name} - Nivel: {general_info.get('nivel', 'Descon.')} | Grado: {general_info.get('grado', 'Descon.')} | Sección: {general_info.get('seccion', 'Descon.')}"
        worksheet.merge_range('A1:J1', title_text, title_format)
        
        # Limpiar filas vacías (sin bordes)
        empty_format = workbook.add_format({'border': 0})
        for row in range(len(df) + 3, 50):  # Limpiar desde la fila siguiente a la tabla
            worksheet.set_row(row, None, empty_format)
        
        # Congelar paneles (encabezados fijos)
        worksheet.freeze_panes(3, 1)  # Congelar fila 3 (encabezados) y columna A
    
    output.seek(0)
    return output.getvalue()
    
def configurar_uploader():
    st.markdown("<div class='pbi-card' style='text-align: center; border: 2px dashed #ccc;'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Arrastra o selecciona el archivo Excel de SIAGIE", type=["xlsx"])
    if uploaded_file:
        with st.spinner('Sincronizando datos...'):
            excel_file = pd.ExcelFile(uploaded_file)
            hojas_validas = [s for s in excel_file.sheet_names if s not in ["Generalidades", "Parametros"]]
            st.session_state.all_dataframes = {sheet: excel_file.parse(sheet) for sheet in hojas_validas}
            st.session_state.info_areas = analysis_core.analyze_data(excel_file, hojas_validas)
            st.session_state.df_cargado = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def inject_pbi_css():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
       
        /* FONDO DE APLICACIÓN */
        [data-testid="stAppViewContainer"] {{
            background-color: {PBI_BG} !important;
            background-attachment: fixed;
        }}
        .stApp {{
            background-color: transparent !important;
            font-family: 'Segoe UI', sans-serif;
        }}
        /* TARJETAS CON SOMBRAS PROFUNDAS Y BORDES REFORZADOS */
        .pbi-card {{
            background-color: {PBI_CARD_BG};
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            margin-bottom: 24px;
            border: 1px solid #E2E8F0;
        }}
        /* ESTILO PARA TABLAS (DATAFRAMES) */
        [data-testid="stDataFrame"] {{
            border: 1px solid #CBD5E0;
            border-radius: 4px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        }}
        .pbi-header {{
            color: {PBI_BLUE};
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            border-bottom: 4px solid {PBI_LIGHT_BLUE};
            padding-bottom: 8px;
            text-transform: uppercase;
        }}
        /* BOTONES ESTILO PREMIUM */
        div.stButton > button {{
            border-radius: 4px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            border: 1px solid rgba(0,0,0,0.1) !important;
        }}
        div.stButton > button:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
            transform: translateY(-1px);
        }}
        div.stDownloadButton > button {{
            background-color: {PBI_LIGHT_BLUE} !important;
            color: white !important;
            border-radius: 4px !important;
            font-weight: 600 !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: #EDF2F7;
            border-radius: 4px 4px 0 0;
            padding: 10px 20px;
            border: 1px solid #E2E8F0;
            margin-right: 4px;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {PBI_CARD_BG} !important;
            border-top: 4px solid {PBI_LIGHT_BLUE} !important;
            border-bottom: none !important;
            font-weight: bold;
            box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        </style>
    """, unsafe_allow_html=True)

def generar_pdf_comparacion(fig, area_name, info1, info2, general_data):
    """
    Genera PDF con el gráfico seleccionado y contexto completo.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Título
    title = f"Comparación entre {info1['periodo']} y {info2['periodo']}"
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))

    # Contexto
    contexto = f"Área: {area_name} | Nivel: {general_data.get('nivel', 'Descon.')} | Grado: {general_data.get('grado', 'Descon.')} | Sección: {general_data.get('seccion', 'Descon.')}"
    elements.append(Paragraph(contexto, styles['Normal']))
    elements.append(Spacer(1, 24))

    # Convertir gráfico Plotly a imagen
    img_bytes = pio.to_image(fig, format="png", width=800, height=600)
    img = PILImage.open(io.BytesIO(img_bytes))
    elements.append(Image(img, width=500, height=375))
    elements.append(Spacer(1, 36))

    # Pie de página
    fecha = date.today().strftime("%d/%m/%Y")
    pie = f"Generado por AulaMetrics – {fecha}"
    elements.append(Paragraph(pie, styles['Italic']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
