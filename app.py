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
# === 1. IMPORTS Y CONFIGURACIÓN INICIAL ===
# =========================================================================
import streamlit as st
import pandas as pd
import analysis_core          # <--- Importante
import pedagogical_assistant  # <--- Importante
from auth import login_user
import plotly.express as px
import io 
import xlsxwriter 
import os 
import base64 

# --- CONFIGURACIÓN DE PÁGINA (SOLO UNA VEZ) ---
# (Este es el st.set_page_config de tu Sección 1, que es el correcto)
st.set_page_config(
    page_title="AulaMetrics", 
    page_icon="assets/isotipo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
# === 2. INICIALIZACIÓN DEL ESTADO DE SESIÓN ===
# =========================================================================
# (Este es tu bloque de Sección 2, está perfecto)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    
if 'user_level' not in st.session_state:
    st.session_state.user_level = None
    
if 'show_welcome_message' not in st.session_state:
    st.session_state.show_welcome_message = False
    
if 'df_cargado' not in st.session_state:
    st.session_state.df_cargado = False

if 'df' not in st.session_state:
    st.session_state.df = None
if 'df_config' not in st.session_state:
    st.session_state.df_config = None
if 'info_areas' not in st.session_state:
    st.session_state.info_areas = None
# ----------------------------------------------------

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
    
    /* --- INICIO DE LA MODIFICACIÓN (Título más compacto) --- */
    .hero-container {
        text-align: center;
        padding: 0.2rem 0 2rem 0; /* <-- Padding superior reducido */
    }
    /* --- FIN DE LA MODIFICACIÓN --- */

    .hero-logo {
        width: 120px;
        height: 120px;
        margin-bottom: 1rem;
    }
    
    .gradient-title-login { 
        font-size: 5.0em; 
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
    
    /* (Solución Definitiva - Sin cambios) */
    div.st-block-container > div:first-child {
        max-width: 100% !important;
    }
    [data-testid="stFullScreenButton"] {
        display: none !important;
    }
    
</style>
""", unsafe_allow_html=True)

# =========================================================================
# === 4. FUNCIONES AUXILIARES (CÁLCULO, DISPLAY, UPLOADERS) ===
# === (Carga las 4 hojas de Estandares) ===
# =========================================================================

# --- DEFINICIÓN DE RUTAS (Paths) ---
ISOTIPO_PATH = "assets/isotipo.png"
RUTA_ESTANDARES = "assets/Estandares de aprendizaje.xlsx" # (Nombre sin tilde)

# --- FUNCIÓN DE LOGOUT ---
def logout():
    """Resetea el estado de sesión y vuelve a la página de login."""
    st.session_state.logged_in = False
    st.session_state.user_level = None
    st.session_state.df_cargado = False
    st.session_state.df = None
    st.session_state.df_config = None
    st.session_state.info_areas = None
    # Reseteamos también las selecciones del asistente
    keys_asistente = [k for k in st.session_state.keys() if k.startswith('asistente_')]
    for k in keys_asistente:
        del st.session_state[k]
    st.rerun()

# --- FUNCIÓN (ASISTENTE PEDAGÓGICO) - ACTUALIZADA (con ffill completo) ---
@st.cache_data(ttl=3600)
def cargar_datos_pedagogicos():
    """
    Carga las 4 hojas del archivo Excel de estándares de aprendizaje.
    """
    try:
        # Cargamos las 4 hojas
        df_generalidades = pd.read_excel(RUTA_ESTANDARES, sheet_name="Generalidades")
        df_ciclos = pd.read_excel(RUTA_ESTANDARES, sheet_name="Cicloseducativos")
        df_desc_sec = pd.read_excel(RUTA_ESTANDARES, sheet_name="Descriptorsecundaria")
        df_desc_prim = pd.read_excel(RUTA_ESTANDARES, sheet_name="Descriptorprimaria")
        
        # --- ¡CORRECCIÓN CLAVE! (Rellenamos todas las celdas combinadas) ---
        
        # Hoja 1: Generalidades
        df_generalidades['NIVEL'] = df_generalidades['NIVEL'].ffill()
        
        # Hoja 2: Cicloseducativos
        df_ciclos['ciclo'] = df_ciclos['ciclo'].ffill()
        
        # Hojas de Descriptores (Primaria y Secundaria)
        # Rellenamos todas las columnas que tienen celdas combinadas
        cols_to_fill_prim = ['Área', 'Competencia', 'Ciclo', 'DESCRIPCIÓN DE LOS NIVELES DE LA COMPETENCIA']
        cols_to_fill_sec = ['Área', 'Competencia', 'Ciclo', 'DESCRIPCIÓN DE LOS NIVELES DE LA COMPETENCIA']
        
        df_desc_prim[cols_to_fill_prim] = df_desc_prim[cols_to_fill_prim].ffill()
        df_desc_sec[cols_to_fill_sec] = df_desc_sec[cols_to_fill_sec].ffill()
        # -----------------------------------------------
        
        return df_generalidades, df_ciclos, df_desc_sec, df_desc_prim
    
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo en la ruta: {RUTA_ESTANDARES}")
        return None, None, None, None
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo Excel: {e}")
        st.error("Verifica los nombres de las 4 hojas: 'Generalidades', 'Cicloseducativos', 'Descriptorsecundaria', 'Descriptorprimaria'.")
        return None, None, None, None

# --- FUNCIÓN (UPLOADER) ---
def configurar_uploader():
    """
    Muestra el file_uploader y maneja la lógica de carga y procesamiento.
    """
    limite_hojas = None if st.session_state.user_level == "premium" else 2
    
    if st.session_state.user_level == "free":
        st.warning("Estás en el **Plan Gratuito**. Solo se analizarán las dos primeras hojas (áreas) de tu archivo.")

    uploaded_file = st.file_uploader(
        "Sube tu archivo de Excel aquí", 
        type=["xlsx", "xls"], 
        key="file_uploader"
    )

    if uploaded_file is not None:
        with st.spinner('Procesando archivo...'):
            try:
                excel_file = pd.ExcelFile(uploaded_file)
                sheet_names = excel_file.sheet_names
                
                IGNORE_SHEETS = [analysis_core.GENERAL_SHEET_NAME.lower(), 'parametros']
                sheet_names = [name for name in sheet_names if name.lower() not in IGNORE_SHEETS]

                if limite_hojas:
                    sheet_names = sheet_names[:limite_hojas]
                
                results_dict = analysis_core.analyze_data(excel_file, sheet_names)
                
                st.session_state.info_areas = results_dict
                st.session_state.df_cargado = True
                
                st.session_state.df = None 
                st.session_state.df_config = None
                try:
                    first_sheet = sheet_names[0]
                    df_consolidado = pd.read_excel(uploaded_file, sheet_name=first_sheet, header=0)
                    if 'APELLIDOS Y NOMBRES' in df_consolidado.columns:
                         df_consolidado = df_consolidado.rename(columns={'APELLIDOS Y NOMBRES': 'Estudiante'})
                    st.session_state.df = df_consolidado
                except Exception as e:
                    pass 
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")
                st.session_state.df_cargado = False

# --- FUNCIÓN (TAB 1: ANÁLISIS GENERAL) ---
def mostrar_analisis_general(results):
    """
    Muestra el contenido de la primera pestaña (Análisis General).
    """
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
        st.session_state.chart_type = st.sidebar.radio("Elige el tipo de visualización:", chart_options, key="chart_radio_premium")
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

            st.markdown("##### 1. Distribución de Logros")
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
            st.dataframe(df_table)
            
            excel_data = convert_df_to_excel(df_table, sheet_name, general_data)
            st.download_button(label=f"⬇️ (Opción de exportar a Excel) ({sheet_name})", data=excel_data, file_name=f'Frecuencias_{sheet_name}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key=f'download_excel_{sheet_name}')

            st.markdown("---")
            competencia_nombres_limpios = df_table.index.tolist()
            selected_comp = None 

            if st.session_state.chart_type == 'Barras (Por Competencia)':
                selected_comp = st.selectbox(f"Selecciona la competencia para ver el Gráfico de Barras en {sheet_name}:", options=competencia_nombres_limpios, key=f'select_comp_bar_{sheet_name}')
                df_bar_data = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']].rename(index={'AD (Est.)': 'AD', 'A (Est.)': 'A', 'B (Est.)': 'B', 'C (Est.)': 'C'})
                df_bar = df_bar_data.reset_index()
                df_bar.columns = ['Nivel', 'Estudiantes']
                fig = px.bar(df_bar, x='Nivel', y='Estudiantes', title=f"Distribución de Logros: {selected_comp}", color='Nivel', color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'})
                st.plotly_chart(fig, use_container_width=True)
            
            elif st.session_state.chart_type == 'Pastel (Proporción)':
                selected_comp = st.selectbox(f"Selecciona la competencia para el Gráfico de Pastel en {sheet_name}:", options=competencia_nombres_limpios, key=f'select_comp_pie_{sheet_name}')
                data_pie_data = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']]
                data_pie = data_pie_data.reset_index()
                data_pie.columns = ['Nivel', 'Estudiantes']
                fig = px.pie(data_pie, values='Estudiantes', names='Nivel', title=f"Distribución Proporcional de Logros: {selected_comp}", color='Nivel', color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'})
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            if selected_comp:
                st.session_state[f'selected_comp_{sheet_name}'] = selected_comp
            selected_comp_key = f'selected_comp_{sheet_name}'
            
            if st.button(f"🎯 (Propuestas de mejora)", key=f"asistente_comp_{sheet_name}", type="primary", disabled=not is_premium):
                if selected_comp_key in st.session_state and st.session_state[selected_comp_key]:
                    comp_name_limpio = st.session_state[selected_comp_key]
                    with st.expander(f"Ver Propuestas de mejora para: {comp_name_limpio}", expanded=True):
                        ai_report_text = pedagogical_assistant.generate_suggestions(results, sheet_name, comp_name_limpio)
                        st.markdown(ai_report_text, unsafe_allow_html=True)
                else:
                    st.warning("Selecciona una competencia en el desplegable de gráficos antes de generar el informe detallado.")
            
            if not is_premium:
                st.caption("🔒 (Propuestas de mejora) es una función Premium.")

# --- FUNCIÓN (TAB 2: ANÁLISIS POR ESTUDIANTE) ---
def mostrar_analisis_por_estudiante(df, df_config, info_areas):
    """
    Muestra el contenido de la segunda pestaña (Análisis por Estudiante).
    """
    st.header("🧑‍🎓 Análisis Individual por Estudiante")
    st.info("Esta función está actualmente en desarrollo.")
    
    if False and df is not None:
        try:
            lista_estudiantes = df['Estudiante'].unique()
            estudiante_seleccionado = st.selectbox("Selecciona un Estudiante", options=lista_estudiantes, key="select_student_tab")
            if estudiante_seleccionado:
                st.subheader(f"Perfil de: {estudiante_seleccionado}")
                datos_estudiante = df[df['Estudiante'] == estudiante_seleccionado]
                st.dataframe(datos_estudiante)
        except KeyError:
            st.error("Error: La columna 'Estudiante' no se encontró en el DataFrame consolidado.")
        except Exception as e:
            st.error(f"Ocurrió un error al mostrar el análisis por estudiante: {e}")

# --- FUNCIÓN (Conversión a Excel) ---
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
        df.to_excel(writer, sheet_name='Frecuencias', startrow=0, startcol=0, index=True)

    return output.getvalue()
    
# =========================================================================
# === 5. FUNCIÓN PRINCIPAL `home_page` (EL DASHBOARD) ===
# === (Corrección del SyntaxError 'else:') ===
# =========================================================================

def home_page():
    
    # 1. MENSAJE DE BIENVENIDA
    if st.session_state.show_welcome_message:
        nivel_usuario = "Premium" if st.session_state.user_level == "premium" else "Gratuito"
        st.toast(f"¡Bienvenido! Has iniciado sesión como usuario {nivel_usuario}.", icon="👋")
        st.session_state.show_welcome_message = False

    # 2. CONFIGURACIÓN DEL DASHBOARD (Logo y Título)
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        try:
            st.image(ISOTIPO_PATH, width=120)
        except:
            st.warning("No se pudo cargar el isotipo. (Verifica 'assets/isotipo.png')")
            
    with col_titulo:
        st.markdown(
            '<h1 class="gradient-title-dashboard">Generador de Análisis Pedagógico</h1>', 
            unsafe_allow_html=True
        )
        st.markdown("Selecciona una herramienta para comenzar.")

    # Botón de cerrar sesión
    if st.sidebar.button("Cerrar Sesión", key="logout_sidebar_button"):
        logout()

    # 3. LÓGICA DE PESTAÑAS (Se muestra SIEMPRE)
    tab_general, tab_estudiante, tab_asistente = st.tabs([
        "📊 Análisis General", 
        "🧑‍🎓 Análisis por Estudiante", 
        "🧠 Asistente Pedagógico"
    ])

    # --- Pestaña 1: Análisis General (Contiene el cargador) ---
    with tab_general:
        if st.session_state.df_cargado:
            info_areas = st.session_state.info_areas
            mostrar_analisis_general(info_areas)
        else:
            st.subheader("Subir Archivo de Notas")
            st.info("Para comenzar el análisis de notas, sube tu registro de Excel aquí.")
            configurar_uploader() 

    # --- Pestaña 2: Análisis por Estudiante (Depende de la Pestaña 1) ---
    with tab_estudiante:
        if st.session_state.df_cargado:
            df = st.session_state.df
            df_config = st.session_state.df_config
            info_areas = st.session_state.info_areas
            mostrar_analisis_por_estudiante(df, df_config, info_areas)
        else:
            st.header("🧑‍🎓 Análisis Individual por Estudiante")
            st.info("Esta función requiere un archivo de notas.")
            st.warning("Por favor, ve a la pestaña **'📊 Análisis General'** y sube tu archivo de Excel para activar esta vista.")

        
    # --- Pestaña 3: Asistente Pedagógico (CONEXIÓN A IA) ---
    with tab_asistente:
        st.header("🧠 Asistente Pedagógico")
        
        tipo_herramienta = st.radio(
            "01. Selecciona la herramienta que deseas usar:",
            options=["Sesión de aprendizaje", "Unidad de aprendizaje", "Planificación Anual"],
            index=0, 
            horizontal=True,
            key="asistente_tipo_herramienta"
        )
        st.markdown("---")

        if st.session_state.asistente_tipo_herramienta == "Sesión de aprendizaje":
            st.subheader("Generador de Sesión de Aprendizaje")
            
            df_gen, df_cic, df_desc_sec, df_desc_prim = cargar_datos_pedagogicos()
            
            if df_gen is None or df_cic is None or df_desc_sec is None or df_desc_prim is None:
                st.error("Error crítico: No se pudieron cargar todas las hojas de 'Estandares de aprendizaje.xlsx'.")
            else:
                # --- FORMULARIO DEPENDIENTE DE 6 PASOS ---
                
                # PASO 1: Nivel
                niveles = df_gen['NIVEL'].dropna().unique()
                nivel_sel = st.selectbox("Paso 1: Selecciona el Nivel", options=niveles, index=None, placeholder="Elige una opción...", key="asistente_nivel_sel" )
                
                # PASO 2: Grado
                grados_options = []
                if st.session_state.asistente_nivel_sel:
                    grados_options = df_gen[df_gen['NIVEL'] == st.session_state.asistente_nivel_sel]['GRADO CORRESPONDIENTE'].dropna().unique()
                
                grado_sel = st.selectbox("Paso 2: Selecciona el Grado", options=grados_options, index=None, placeholder="Elige un Nivel primero...", disabled=(not st.session_state.asistente_nivel_sel), key="asistente_grado_sel")

                # PASO 3: Área
                areas_options = []
                df_hoja_descriptor = None 
                
                if st.session_state.asistente_grado_sel:
                    if st.session_state.asistente_nivel_sel == "SECUNDARIA":
                        df_hoja_descriptor = df_desc_sec
                    elif st.session_state.asistente_nivel_sel == "PRIMARIA":
                        df_hoja_descriptor = df_desc_prim
                    
                    if df_hoja_descriptor is not None:
                        areas_options = df_hoja_descriptor['Área'].dropna().unique()
                
                area_sel = st.selectbox("Paso 3: Selecciona el Área", options=areas_options, index=None, placeholder="Elige un Grado primero...", disabled=(not st.session_state.asistente_grado_sel), key="asistente_area_sel")

                # PASO 4: Competencia
                competencias_options = []
                if st.session_state.asistente_area_sel and (df_hoja_descriptor is not None):
                    competencias_options = df_hoja_descriptor[
                        df_hoja_descriptor['Área'] == st.session_state.asistente_area_sel
                    ]['Competencia'].dropna().unique()

                competencias_sel = st.multiselect("Paso 4: Selecciona la(s) Competencia(s)", options=competencias_options, placeholder="Elige un Área primero...", disabled=(not st.session_state.asistente_area_sel), key="asistente_competencias_sel")
                
                # PASOS 5 y 6: Dentro de un formulario
                with st.form(key="session_form"):
                    form_disabled = not st.session_state.asistente_competencias_sel
                    
                    tema_sel = st.text_input("Paso 5: Escribe el tema o temática a tratar", placeholder="Ej: El sistema solar...", disabled=form_disabled)
                    tiempo_sel = st.selectbox("Paso 6: Selecciona la duración de la sesión", options=["90 minutos", "180 minutos"], index=None, placeholder="Elige una opción...", disabled=form_disabled)
                    
                    submitted = st.form_submit_button("Generar Sesión de Aprendizaje", disabled=form_disabled)
                    
                    if submitted:
                        if not tema_sel or not tiempo_sel:
                            st.error("Por favor, completa los Pasos 5 y 6.")
                        else:
                            with st.spinner("🤖 Generando tu sesión de aprendizaje... Esto puede tomar un minuto..."):
                                try:
                                    # 1. Recolectar datos
                                    nivel = st.session_state.asistente_nivel_sel
                                    grado = st.session_state.asistente_grado_sel
                                    area = st.session_state.asistente_area_sel
                                    competencias = st.session_state.asistente_competencias_sel 
                                    tema = tema_sel
                                    tiempo = tiempo_sel
                                    
                                    # 2. Buscar datos pedagógicos
                                    ciclo_encontrado = df_cic[df_cic['grados que corresponde'] == grado]['ciclo'].iloc[0]
                                    
                                    datos_filtrados = df_hoja_descriptor[
                                        (df_hoja_descriptor['Área'] == area) &
                                        (df_hoja_descriptor['Competencia'].isin(competencias))
                                    ]
                                    capacidades_lista = datos_filtrados['capacidad'].dropna().unique().tolist()
                                    estandares_lista = datos_filtrados['DESCRIPCIÓN DE LOS NIVELES DE LA COMPETENCIA'].dropna().unique().tolist()
                                    estandar_texto_completo = "\n\n".join(estandares_lista)

                                    # 3. Llamar a la IA
                                    sesion_generada = pedagogical_assistant.generar_sesion_aprendizaje(
                                        nivel=nivel,
                                        grado=grado,
                                        ciclo=str(ciclo_encontrado), 
                                        area=area,
                                        competencias_lista=competencias,
                                        capacidades_lista=capacidades_lista,
                                        estandar_texto=estandar_texto_completo,
                                        tematica=tema,
                                        tiempo=tiempo
                                    )
                                    
                                    # 4. Mostrar el resultado
                                    st.success("¡Sesión de aprendizaje generada!")
                                    st.markdown(sesion_generada)

                                except Exception as e:
                                    st.error(f"Ocurrió un error al generar la sesión:")
                                    st.error(e)
        
        elif st.session_state.asistente_tipo_herramienta == "Unidad de aprendizaje":
            st.info("Función de Unidades de Aprendizaje (Próximamente).")
        
        elif st.session_state.asistente_tipo_herramienta == "Planificación Anual":
            st.info("Función de Planificación Anual (Próximamente).")
            
    # --- ¡ERROR CORREGIDO! ---
    # El 'else:' huérfano que causaba el SyntaxError (`image_636ede.png`) ha sido eliminado.

# =========================================================================
# === 6. LÓGICA DE INICIO (LOGIN) Y PANTALLA INICIAL ===
# =========================================================================

if not st.session_state.logged_in:

    _col1, col_form, _col3 = st.columns([1, 1.5, 1])
    
    with col_form:
        
        try:
            # (ISOTIPO_PATH ahora está definido globalmente en la Sección 4)
            st.image(ISOTIPO_PATH, width=120)
        except Exception as e:
            pass 
        
        st.markdown(
            '<h1 class="gradient-title-dashboard" style="text-align: center;">AulaMetrics</h1>', 
            unsafe_allow_html=True
        )
        st.write("") 
        
        st.header("🔑 Iniciar Sesión")
        
        username = st.text_input("Usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", key="login_pass")
        
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
else:
    # MOSTRAR EL DASHBOARD (POST-LOGIN)
    home_page()



















