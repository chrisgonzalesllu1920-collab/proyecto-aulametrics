import streamlit as st
import pandas as pd
import analysis_core
import pedagogical_assistant
from auth import login_user
import plotly.express as px
import io 
import xlsxwriter 
import os 
import base64 

# =========================================================================
# === 1. CONFIGURACIÓN DE LA PÁGINA ===
# =========================================================================
import streamlit as st
import base64 # Asegúrate de que 'base64' esté importado

# --- INICIO DE LA MODIFICACIÓN (Configuración Completa) ---
# Se ha verificado 'layout="wide"' y se ha añadido 'initial_sidebar_state'
st.set_page_config(
    page_title="AulaMetrics", 
    page_icon="assets/isotipo.png", # <-- Actualizado al logo
    layout="wide",
    initial_sidebar_state="collapsed" # <-- Esta línea es importante
)
# --- FIN DE LA MODIFICACIÓN ---

@st.cache_data 
def get_image_as_base64(file_path):
    """Carga una imagen y la convierte a Base64 string."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# =========================================================================
# === 2. INICIALIZACIÓN DEL ESTADO DE SESIÓN (Global) ===
# =========================================================================
def initialize_session_state():
    """Inicializa todos los estados de sesión necesarios."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'analisis_results' not in st.session_state:
        st.session_state.analisis_results = None
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'sheet_options' not in st.session_state:
        st.session_state.sheet_options = []
    if 'chart_type' not in st.session_state:
        st.session_state.chart_type = 'Barras (Por Competencia)'
    if 'user_level' not in st.session_state:
        st.session_state.user_level = None 
    if 'show_welcome_message' not in st.session_state:
        st.session_state.show_welcome_message = False 
        
initialize_session_state()

# =========================================================================
# === 3. ESTILOS CSS (Con Títulos, Cartel, HERO y FONDO DE PÁGINA) ===
# =========================================================================
st.markdown("""
<style>
    /* Reduce el padding superior de la página (default es 6rem) */
    div.st-block-container {
        padding-top: 2rem;
    }

    /* Importa la fuente Oswald (más gruesa) */
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@700&display=swap');

    /* (Estilos de Títulos - Sin cambios) */
    .gradient-title-login, .gradient-title-dashboard {
        font-family: 'Oswald', sans-serif;
        font-weight: 700;
        background: linear-gradient(45deg, #00BFA5, #2196F3);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        -webkit-text-fill-color: transparent; 
        display: inline-block;
    }
    @supports not (-webkit-background-clip: text) {
        .gradient-title-login, .gradient-title-dashboard {
            color: #2196F3; 
            background: none;
        }
    }
    
    .gradient-title-dashboard { font-size: 2.5em; }
    
    /* (Bordes Dorados - Sin cambios) */
    div[data-testid="stTextInput"] input:focus {
        background-color: #FFFFE0;
        border: 2px solid #FFD700;
        box-shadow: 0 0 5px #FFD700;
    }
    
    /* (Cartel de planes - Sin cambios) */
    .plan-box {
        border-radius: 10px;
        padding: 20px;
        margin-top: 15px;
        height: 100%; 
    }
    .plan-box-free {
        background-color: #FFF0F0; 
        border: 2px solid #FFCDCD;
    }
    .plan-box-premium {
        background-color: #F0F8FF; 
        border: 2px solid #00BFA5; 
    }
    .plan-title {
        font-family: 'Oswald', sans-serif;
        font-size: 1.75em;
        font-weight: 700;
        margin-bottom: 15px;
    }
    .plan-feature {
        margin-bottom: 10px;
        font-size: 1.0em;
    }
    
    /* (Estilo de botones expander - Sin cambios) */
    [data-testid="stExpander"] summary {
        background-color: #00BFA5;
        color: white !important;
        border-radius: 5px;
        padding: 10px 15px;
        font-weight: 600;
    }
    [data-testid="stExpander"] summary svg { fill: white !important; }
    [data-testid="stExpander"] summary:hover {
        background-color: #008f7a;
        color: white !important;
    }
    [data-testid="stExpander"] summary:hover svg { fill: white !important; }
    [data-testid="stExpander"][aria-expanded="true"] summary {
         background-color: #f0f2f6; 
         color: #31333F !important;
    }
    [data-testid="stExpander"][aria-expanded="true"] summary svg {
         fill: #31333F !important;
    }
    
    /* (Estilos del Hero - Sin cambios) */
    .hero-container {
        text-align: center;
        padding: 1rem 0 2rem 0;
    }
    .hero-logo {
        width: 120px;
        height: 120px;
        margin-bottom: 1rem;
    }
    .gradient-title-login { 
        font-size: 4.5em;
        line-height: 1.1;
    }
    .hero-slogan {
        font-size: 1.75rem;
        font-weight: 300;
        color: #333;
        margin-top: -0.5rem;
    }
    .hero-tagline {
        font-size: 1.1rem;
        color: #555;
        font-weight: 300;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# === 4. FUNCIONES DE DISPLAY (TABLERO Y EXCEL) ===
# =========================================================================
# (Esta sección no tiene cambios)

@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    """Convierte DataFrame a formato Excel (xlsx) en memoria con formato."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        info_sheet = workbook.add_worksheet("Generalidades")
        bold = workbook.add_format({'bold': True})
        info_sheet.write('A1', 'Área:', bold)
        info_sheet.write('B1', area_name)
        info_sheet.write('A2', 'Nivel:', bold)
        info_sheet.write('B2', general_info.get('nivel', 'N/A'))
        info_sheet.write('A3', 'Grado:', bold)
        info_sheet.write('B3', general_info.get('grado', 'N/A'))
        
        sheet = workbook.add_worksheet('Frecuencias')
        header_base_props = {'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'border': 1, 'align': 'center'}
        header_comp_format = workbook.add_format(header_base_props) 
        ad_header_format = workbook.add_format({**header_base_props, 'fg_color': '#C6EFCE'}) 
        a_header_format = workbook.add_format({**header_base_props, 'fg_color': '#D9EAD3'})  
        b_header_format = workbook.add_format({**header_base_props, 'fg_color': '#FFEB9C'})  
        c_header_format = workbook.add_format({**header_base_props, 'fg_color': '#FFC7CE'})  
        total_header_format = workbook.add_format({**header_base_props, 'fg_color': '#DAE8FC'}) 
        data_format = workbook.add_format({'border': 1, 'align': 'left'})
        data_center_format = workbook.add_format({'border': 1, 'align': 'center'})
        
        col_formats = {
            'Competencia': header_comp_format,
            'AD (Est.)': ad_header_format, '% AD': ad_header_format,
            'A (Est.)': a_header_format, '% A': a_header_format,
            'B (Est.)': b_header_format, '% B': b_header_format,
            'C (Est.)': c_header_format, '% C': c_header_format,
            'Total': total_header_format
        }

        for col_num, value in enumerate(df.columns.values):
            header_fmt = col_formats.get(value, header_comp_format)
            sheet.write(0, col_num + 1, value, header_fmt)
        sheet.write(0, 0, 'Competencia', col_formats.get('Competencia'))
        
        for row_num, (index, row) in enumerate(df.iterrows()):
            sheet.write(row_num + 1, 0, index, data_format)
            for col_num, value in enumerate(row):
                if df.columns[col_num] in ['AD (Est.)', '% AD', 'A (Est.)', '% A', 
                                            'B (Est.)', '% B', 'C (Est.)', '% C', 'Total']:
                    sheet.write(row_num + 1, col_num + 1, value, data_center_format)
                else:
                    sheet.write(row_num + 1, col_num + 1, value, data_format)
                
        sheet.set_column('A:A', 50)
        sheet.set_column('B:K', 12)
        
    return output.getvalue()


def display_analysis_dashboard(results):
    """Muestra los resultados del análisis y el botón del asistente."""
    
    is_premium = (st.session_state.user_level == "premium")

    st.markdown("---")
    st.subheader("Resultados Consolidados por Área")

    first_sheet_key = next(iter(results), None)
    general_data = {}
    if first_sheet_key and 'generalidades' in results[first_sheet_key]:
        general_data = results[first_sheet_key]['generalidades']
        st.info(f"Datos del Grupo: Nivel: **{general_data.get('nivel', 'Desconocido')}** | Grado: **{general_data.get('grado', 'Desconocido')}**")
    
    st.sidebar.subheader("⚙️ Configuración del Gráfico")
    if is_premium:
        chart_options = ('Barras (Por Competencia)', 'Pastel (Proporción)')
        st.session_state.chart_type = st.sidebar.radio(
            "Elige el tipo de visualización:",
            chart_options,
            key="chart_radio_premium"
        )
    else:
        st.sidebar.markdown("Tipo de visualización: **Barras (Por Competencia)**")
        st.sidebar.caption("🔒 (Elección entre gráficos estadísticos) es una función Premium.")
        st.session_state.chart_type = 'Barras (Por Competencia)'

    tabs = st.tabs([f"Área: {sheet_name}" for sheet_name in results.keys()])

    for i, (sheet_name, result) in enumerate(results.items()):
        with tabs[i]:
            if 'error' in result:
                st.error(f"Error al procesar la hoja '{sheet_name}': {result['error']}")
                continue
            
            competencias = result['competencias']

            if not competencias:
                st.info(f"No se encontraron datos de competencias en la hoja '{sheet_name}'.")
                continue

            st.markdown("##### 1. Distribución de Logros (Frecuencias Absolutas y Porcentuales)")
            
            data = {
                'Competencia': [], 'AD (Est.)': [], '% AD': [], 'A (Est.)': [], '% A': [],
                'B (Est.)': [], '% B': [], 'C (Est.)': [], '% C': [], 'Total': []
            }
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
            df_table = pd.DataFrame(data)
            df_table = df_table.set_index('Competencia')
            st.dataframe(df_table)
            
            excel_data = convert_df_to_excel(df_table, sheet_name, general_data)
            
            # Descarga de Excel (Permitida para todos)
            st.download_button(
                label=f"⬇️ (Opción de exportar a Excel) ({sheet_name})",
                data=excel_data,
                file_name=f'Frecuencias_{sheet_name}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                key=f'download_excel_{sheet_name}'
            )

            st.markdown("---")

            # 2. Gráfico de Frecuencias
            competencia_nombres_limpios = df_table.index.tolist()
            selected_comp = None 

            if st.session_state.chart_type == 'Barras (Por Competencia)':
                selected_comp = st.selectbox(
                    f"Selecciona la competencia para ver el Gráfico de Barras en {sheet_name}:",
                    options=competencia_nombres_limpios,
                    key=f'select_comp_bar_{sheet_name}'
                )
                df_bar = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']].rename(
                    index={'AD (Est.)': 'AD', 'A (Est.)': 'A', 'B (Est.)': 'B', 'C (Est.)': 'C'}
                )
                df_bar.name = 'Estudiantes'
                df_bar = df_bar.reset_index()
                df_bar.columns = ['Nivel', 'Estudiantes']
                fig = px.bar(df_bar, x='Nivel', y='Estudiantes', 
                             title=f"Distribución de Logros: {selected_comp}",
                             color='Nivel',
                             color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'})
                st.plotly_chart(fig, use_container_width=True)
            
            elif st.session_state.chart_type == 'Pastel (Proporción)':
                selected_comp = st.selectbox(
                    f"Selecciona la competencia para el Gráfico de Pastel en {sheet_name}:",
                    options=competencia_nombres_limpios,
                    key=f'select_comp_pie_{sheet_name}'
                )
                data_pie = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']].reset_index()
                data_pie.columns = ['Nivel', 'Estudiantes']
                fig = px.pie(data_pie, values='Estudiantes', names='Nivel', 
                             title=f"Distribución Proporcional de Logros: {selected_comp}",
                             color='Nivel',
                             color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'})
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            
            # 3. Botones para el Asistente Pedagógico (Bloqueado para free)
            if selected_comp:
                st.session_state[f'selected_comp_{sheet_name}'] = selected_comp
            
            selected_comp_key = f'selected_comp_{sheet_name}'
            
            if st.button(
                f"🎯 (Propuestas de mejora)", 
                key=f"asistente_comp_{sheet_name}", 
                type="primary",
                disabled=not is_premium # RESTRICCIÓN MANTENIDA
            ):
                if selected_comp_key in st.session_state and st.session_state[selected_comp_key]:
                    comp_name_limpio = st.session_state[selected_comp_key]
                    
                    with st.expander(f"Ver Propuestas de mejora para: {comp_name_limpio}", expanded=True):
                        ai_report_text = pedagogical_assistant.generate_suggestions(results, sheet_name, comp_name_limpio)
                        st.session_state[f'ai_report_{sheet_name}_comp_{comp_name_limpio}'] = ai_report_text
                        
                        if ai_report_text and "Error" not in ai_report_text:
                            st.markdown(ai_report_text, unsafe_allow_html=True)
                        else:
                            st.error(ai_report_text) 
                        
                        st.markdown("---")
                        
                        if ai_report_text and "Error" not in ai_report_text and "No se requiere intervención crítica" not in ai_report_text:
                            docx_buffer = pedagogical_assistant.generate_docx_report(
                                results, sheet_name, comp_name_limpio, ai_report_text
                            )
                            
                            st.download_button(
                                label="📄 (Opción de exportar tablas y propuestas de mejora)",
                                data=docx_buffer,
                                file_name=f'Propuestas_{sheet_name}_{comp_name_limpio}.docx',
                                mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                key=f'download_word_comp_{sheet_name}_{comp_name_limpio}'
                            )
                else:
                    st.warning("Selecciona una competencia en el desplegable de gráficos antes de generar el informe detallado.")
            
            if not is_premium:
                st.caption("🔒 (Propuestas de mejora) es una función Premium.")


# =========================================================================
# === 5. FUNCIÓN PRINCIPAL DEL DASHBOARD (POST-LOGIN) ===
# =========================================================================

def home_page():
    """Contenido principal de la aplicación después del login."""
    
    is_premium = (st.session_state.user_level == "premium")
    
    # Mensaje de bienvenida
    if st.session_state.get('show_welcome_message', False):
        if is_premium:
            st.toast("¡Bienvenido! Has iniciado sesión como Usuario Premium. ✨", icon="⭐")
        else:
            st.toast("¡Bienvenido! Has iniciado sesión como Usuario Gratuito.", icon="👋")
        st.session_state.show_welcome_message = False
    
    # Título del dashboard
    st.markdown('<h1 class="gradient-title-dashboard">AulaMetrics: Dashboard de Análisis de Logros</h1>', unsafe_allow_html=True)
    st.markdown("Cargue su archivo Excel para visualizar los datos.")

    # --- Sidebar para Carga de Archivo ---
    st.sidebar.header("📁 Carga de Datos")
    
    uploader_key = "file_uploader_logged" if st.session_state.logged_in else "file_uploader_unlogged"

    uploaded_file = st.sidebar.file_uploader(
        "Sube tu archivo de datos de AulaMetrics (formato .xlsx)",
        type=["xlsx"],
        key=uploader_key
    )

    # Botón Cerrar Sesión (movido aquí para visibilidad)
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión", key="logout_button_final_key"):
        st.session_state.logged_in = False
        st.session_state.user_level = None
        st.session_state.show_welcome_message = False
        st.session_state.analisis_results = None
        st.session_state.selected_file = None
        st.session_state.sheet_options = []
        st.rerun() 

    if uploaded_file is not None:
        st.session_state.selected_file = uploaded_file
        
        try:
            xlsx = pd.ExcelFile(uploaded_file)
            # Filtro robusto: excluye si 'generalidades' o 'parámetros' están EN CUALQUIER LUGAR del nombre
            sheet_names = [name for name in xlsx.sheet_names if 'generalidades' not in name.lower() and 'parámetros' not in name.lower()]
            st.session_state.sheet_options = sheet_names
            uploaded_file.seek(0)
        except Exception as e:
            st.error(f"Error al leer las hojas del archivo: {e}")
            st.session_state.sheet_options = []
            
        st.sidebar.subheader("Selecciona Área a Analizar")
        
        # --- (Selector de Hojas: Lógica de 'selectbox' - Sin cambios) ---
        selected_sheet = None 
        
        if is_premium:
            # Premium: Puede seleccionar UNA de TODAS las áreas
            selected_sheet = st.sidebar.selectbox(
                "Elige el área que deseas procesar:",
                options=st.session_state.sheet_options,
                key="select_premium",
                index=None,
                placeholder="Selecciona un área..."
            )
        else:
            # Free: Puede seleccionar UNA de las DOS primeras áreas
            free_options = st.session_state.sheet_options[:2] 
            selected_sheet = st.sidebar.selectbox(
                "Elige una de las dos áreas permitidas:",
                options=free_options,
                key="select_free",
                index=None,
                placeholder="Selecciona un área..."
            )
            st.sidebar.caption("🔒 (Análisis de todas las hojas) es una función Premium.")
        
        selected_sheets_list = []
        if selected_sheet:
            selected_sheets_list = [selected_sheet]
        # --- Fin Selector de Hojas ---


        if st.sidebar.button("▶ Ejecutar Análisis", key="run_analysis_button", type="primary"):
            if selected_sheets_list: 
                with st.spinner('Procesando datos y generando análisis...'):
                    uploaded_file.seek(0) 
                    analisis_results = analysis_core.analyze_data(uploaded_file, selected_sheets_list)
                    st.session_state.analisis_results = analisis_results
                    st.success("✅ Análisis de datos completado.")
            else:
                st.sidebar.warning("Por favor, selecciona al menos un área para analizar.")
        
        uploaded_file.seek(0)

    if st.session_state.analisis_results:
        display_analysis_dashboard(st.session_state.analisis_results)


# =========================================================================
# === 6. LÓGICA DE INICIO (LOGIN) Y PANTALLA INICIAL ===
# === (MODIFICADO CON FONDO CORAL Y TARJETA FLOTANTE) ===
# =========================================================================

if not st.session_state.logged_in:

    
    # --- FIN DE LA MODIFICACIÓN ---

    
    # 1. TÍTULO, LOGO Y FRASE (HERO SECTION)
    ISOTIPO_PATH = "assets/isotipo.png" 
    isotipo_base64 = get_image_as_base64(ISOTIPO_PATH)
    
    hero_html = """
    <div class="hero-container">
    """
    
    if isotipo_base64:
        hero_html += f'<img src="data:image/png;base64,{isotipo_base64}" class="hero-logo">'
    else:
        # Ya no mostramos el error de C:, sino el error de la ruta relativa
        st.error(f"No se pudo cargar el isotipo. Verifica la ruta: {ISOTIPO_PATH}")
        
    hero_html += """
        <h1 class="gradient-title-login">AulaMetrics</h1>
        <p class="hero-slogan">Datos que impulsan el aprendizaje</p>
        <p class="hero-tagline">Herramienta de Diagnóstico para Intervención Pedagógica</p>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)
        
    # 1.1. SECCIÓN DE PLANES (Desplegable)
    with st.expander("Nuestros Planes"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            <div class="plan-box plan-box-free">
            <div class="plan-title">Plan Gratuito</div>
            <p class="plan-feature">✔️ Análisis de archivos</p>
            <p class="plan-feature">✔️ Análisis de las dos primeras hojas (áreas)</p>
            <p class="plan-feature">✔️ Tabla de frecuencias y porcentajes</p>
            <p class="plan-feature">✔️ Gráficos de barras para los datos</p>
            <p class="plan-feature">✔️ Opción de exportar a Excel</p>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="plan-box plan-box-premium">
            <div class="plan-title">⭐ Plan Premium</div>
            <p class="plan-feature">✔️ Todas las funciones gratuitas</p>
            <p class="plan-feature">✔️ Elección entre gráficos estadísticos</p>
            <p class="plan-feature">✔️ Propuestas de mejora</p>
            <p class="plan-feature">✔️ Opción de exportar tablas y propuestas de mejora</p>
            <p class="plan-feature">✔️ Análisis de todas las hojas del archivo (todas las áreas)</p>
            <p class="plan-feature">✔️ Acceso a todas las nuevas funcionalidades futuras</p>
            </div>
            """, unsafe_allow_html=True)

    # 1.2. SECCIÓN QUIÉNES SOMOS (Desplegable)
    with st.expander("¿Quiénes Somos?"):
        st.subheader("Quiénes Somos")
        st.markdown("""
        Somos una plataforma pedagógica diseñada para transformar datos en conocimiento útil. 
        Analizamos calificaciones y patrones de desempeño estudiantil para generar informes claros, 
        interpretaciones estadísticas y propuestas de mejora orientadas al fortalecimiento de la 
        práctica docente. Nuestro propósito es apoyar a los docentes y equipos directivos en la 
        toma de decisiones estratégicas que optimicen los aprendizajes.
        """)
        st.subheader("Misión")
        st.markdown("""
        Brindar a los docentes una herramienta pedagógica confiable que analiza de manera rigurosa 
        las calificaciones y datos de aprendizaje de los estudiantes, ofreciendo informes y 
        recomendaciones basadas en evidencia. Contribuimos a la mejora continua de los procesos 
        de enseñanza, promoviendo decisiones informadas que permitan elevar el logro de 
        aprendizajes en toda la institución educativa.
        """)
        st.subheader("Visión")
        st.markdown("""
        Convertirnos en la herramienta líder en el análisis educativo dentro de las instituciones, 
        reconocida por impulsar una cultura de evaluación formativa, innovación pedagógica y 
        mejora permanente, donde cada docente cuente con información precisa para potenciar 
        el rendimiento y desarrollo integral de sus estudiantes.
        """)
    
    st.markdown("---") # Divisor
        
    # 2. FORMULARIO DE INICIO DE SESIÓN
    st.header("🔑 Iniciar Sesión")
    username = st.text_input("Usuario", key="login_user")
    password = st.text_input("Contraseña", type="password", key="login_pass")
    
    # Lógica de login (Modificada para aceptar "free")
    if st.button("Entrar", key="login_button", type="primary"):
        
        user_level = login_user(username, password)
        
        if user_level == "premium": 
            st.session_state.logged_in = True
            st.session_state.user_level = "premium"
            st.session_state.show_welcome_message = True 
            st.rerun() 
        
        elif user_level == "free": 
            st.session_state.logged_in = True
            st.session_state.user_level = "free"
            st.session_state.show_welcome_message = True
            st.rerun()
            
        else:
            st.error("Usuario o contraseña incorrectos.")

# 3. FOOTER Y REDES SOCIALES
    st.markdown("---") # Divisor
    
    # --- INICIO DE LA MODIFICACIÓN (Enlaces de Texto) ---
    
    # Usamos Markdown simple. Esto es 100% confiable.
    # RECUERDA: Cambia los enlaces por los tuyos.
    st.markdown(
        "[Contáctanos en WhatsApp](https://wa.me/51XXXXXXXXX) &nbsp; | &nbsp; "
        "[Síguenos en TikTok](https://www.tiktok.com/@tu_usuario_tiktok)",
        unsafe_allow_html=True # Se usa solo para el espacio "&nbsp;"
    )
    
    st.caption("© 2025 AulaMetrics. Todos los derechos reservados.")
    # --- FIN DE LA MODIFICACIÓN ---

else:
    # 4. MOSTRAR EL DASHBOARD (POST-LOGIN)
    home_page()
    
    # 5. BOTÓN CERRAR SESIÓN (Movido a home_page)

