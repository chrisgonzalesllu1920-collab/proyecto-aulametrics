import streamlit as st
import pandas as pd
import analysis_core
import pedagogical_assistant
import plotly.express as px
import io 
import xlsxwriter 
import os 
import base64 
# --- NUEVOS IMPORTS PARA SUPABASE (FASE 3) ---
from supabase import create_client, Client
# -----------------------------------------------

# =========================================================================
# === 1. IMPORTS Y CONFIGURACIÓN INICIAL ===
# =========================================================================
import streamlit as st
import pandas as pd
import analysis_core       # <--- Importante
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
# === 2.1 INICIALIZACIÓN DEL CLIENTE SUPABASE (FASE 3) ===
# =========================================================================
try:
    supabase_url = st.secrets['supabase']['url']
    supabase_key = st.secrets['supabase']['anon_key']
    # Nota: Usamos 'supabase' como el nombre de variable para el cliente
    supabase: Client = create_client(supabase_url, supabase_key)
except KeyError:
    st.error("Error: Faltan las claves de Supabase en 'secrets.toml'.")
    st.info("Asegúrate de haber añadido [supabase] con 'url' y 'anon_key' a tu archivo secrets.toml.")
    st.stop()
except Exception as e:
    st.error(f"Error al conectar con Supabase: {e}")
    st.stop()
# -------------------------------------------------------------------------

# =========================================================================
# === 2.2 INICIALIZACIÓN DEL ESTADO DE SESIÓN ===
# =========================================================================
# (Este es tu bloque de Sección 2, está perfecto)

if 'logged_in' not in st.session_state:
  st.session_state.logged_in = False
  
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

# --- FUNCIÓN (LOGIN / REGISTRO) v2.8 - (¡BOTÓN DE CONTACTO MEJORADO!) ---
def login_page():
    """
    Muestra la página de inicio de sesión y registro, centrada en la pantalla.
    Maneja la lógica de autenticación (SOLO EMAIL/CONTRASEÑA).
    """
    
    # --- ¡TRUCO DE CENTRADO! ---
    col1, col_centro, col3 = st.columns([1, 2, 1])
    
    # Todo el contenido de la página ahora va DENTRO de la columna central
    with col_centro:
        st.image("assets/logotipo-aulametrics.png", width=300)
        st.subheader("Bienvenido a AulaMetrics", anchor=False)
        st.markdown("Tu asistente pedagógico para el análisis de notas.")
        
        tab_login, tab_register = st.tabs(["Iniciar Sesión", "Registrarme"])

        # --- Pestaña de Iniciar Sesión ---
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Correo Electrónico", key="login_email")
                password = st.text_input("Contraseña", type="password", key="login_password")
                submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True, type="primary")
                
                if submitted:
                    try:
                        session = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        st.session_state.logged_in = True
                        st.session_state.user = session.user
                        st.session_state.show_welcome_message = True
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Error al iniciar sesión: {e}")

        # --- Pestaña de Registrarme ---
        with tab_register:
            with st.form("register_form"):
                name = st.text_input("Nombre", key="register_name")
                email = st.text_input("Correo Electrónico", key="register_email")
                password = st.text_input("Contraseña", type="password", key="register_password")
                submitted = st.form_submit_button("Registrarme", use_container_width=True)
                
                if submitted:
                    if not name or not email or not password:
                        st.warning("Por favor, completa todos los campos.")
                    else:
                        try:
                            user = supabase.auth.sign_up({
                                "email": email,
                                "password": password,
                                "options": {
                                    "data": {
                                        'full_name': name
                                    }
                                }
                            })
                            st.success("¡Registro exitoso! Ya puedes iniciar sesión.")
                            st.info("Ve a la pestaña 'Iniciar Sesión' para ingresar.")
                        except Exception as e:
                            st.error(f"Error en el registro: {e}")

        # --- ¡NUEVO BLOQUE DE CONTACTO (HTML/CSS)! ---
        st.divider()
        
        # ¡¡¡IMPORTANTE: REEMPLAZA LA URL DE AQUÍ ABAJO!!!
        url_netlify = "https://bejewelled-moonbeam-7c18d0.netlify.app/" # <-- PEGA TU URL DE NETLIFY AQUÍ
        
        st.markdown(f"""
        <a href="{url_netlify}" target="_blank" style="
            display: inline-block;
            width: 100%;
            padding: 10px 0;
            background-color: #FF5733; /* Color verde WhatsApp */
            color: white;
            text-align: center;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            box-sizing: border-box; /* Asegura que el padding no rompa el ancho */
        ">
            ¿Dudas? Contáctanos (WhatsApp/TikTok/Email)
        </a>
        """, unsafe_allow_html=True)
        # --- FIN DEL NUEVO BLOQUE ---

# =========================================================================
# === 4. FUNCIONES AUXILIARES (CÁLCULO, DISPLAY, UPLOADERS) ===
# === (Carga las 4 hojas de Estandares) ===
# =========================================================================

# --- DEFINICIÓN DE RUTAS (Paths) ---
ISOTIPO_PATH = "assets/isotipo.png"
RUTA_ESTANDARES = "assets/Estandares de aprendizaje.xlsx" # (Nombre sin tilde)


# --- FUNCIÓN (ASISTENTE PEDAGÓGICO) - ACTUALIZADA (con nombre de columna CORRECTO) ---
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
        
        # --- ¡AQUÍ ESTÁ LA CORRECIÓN DEL NOMBRE DE LA COLUMNA! ---
        # (Usamos el nombre correcto que tú identificaste)
        columna_estandar = "DESCRIPCIÓN DE LOS NIVELES DEL DESARROLLO DE LA COMPETENCIA"
        
        cols_to_fill_prim = ['Área', 'Competencia', 'Ciclo', columna_estandar]
        cols_to_fill_sec = ['Área', 'Competencia', 'Ciclo', columna_estandar]
        
        df_desc_prim[cols_to_fill_prim] = df_desc_prim[cols_to_fill_prim].ffill()
        df_desc_sec[cols_to_fill_sec] = df_desc_sec[cols_to_fill_sec].ffill()
        # -----------------------------------------------
        
        return df_generalidades, df_ciclos, df_desc_sec, df_desc_prim
    
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo en la ruta: {RUTA_ESTANDARES}")
        return None, None, None, None
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo Excel: {e}")
        st.error("Verifica los nombres de las 4 hojas: 'Generalidades', 'Cicloseducativos', 'Descriptorsecundaria', 'Descriptorprimaria' y sus columnas.")
        return None, None, None, None

# --- FUNCIÓN (UPLOADER) - ¡CORREGIDA PARA SUPABASE! ---
def configurar_uploader():
    """
    Muestra el file_uploader y maneja la lógica de carga y procesamiento.
    (Se eliminó la lógica de 'user_level' de "premium"/"free")
    """
    # --- LÓGICA ANTIGUA ELIMINADA ---
    # limite_hojas = None if st.session_state.user_level == "premium" else 2
    # if st.session_state.user_level == "free":
    #     st.warning("Estás en el **Plan Gratuito**...")
    # -----------------------------------

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

                # --- LÓGICA DE LÍMITE ELIMINADA ---
                # (Ahora procesará todas las hojas por defecto)
                # if limite_hojas:
                #     sheet_names = sheet_names[:limite_hojas]
                
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

# --- FUNCIÓN (TAB 1: ANÁLISIS GENERAL) - ¡CORREGIDA (DE VERDAD)! ---
def mostrar_analisis_general(results):
    """
    Muestra el contenido de la primera pestaña (Análisis General).
    (Se eliminó la lógica de 'user_level' de "premium"/"free")
    """
    # --- LÓGICA ANTIGUA ELIMINADA ---
    # is_premium = (st.session_state.user_level == "premium")
    # -----------------------------------
    
    st.markdown("---")
    st.subheader("Resultados Consolidados por Área")

    first_sheet_key = next(iter(results), None)
    general_data = {}
    if first_sheet_key and 'generalidades' in results[first_sheet_key]:
        general_data = results[first_sheet_key]['generalidades']
        st.info(f"Datos del Grupo: Nivel: **{general_data.get('nivel', 'Desconocido')}** | Grado: **{general_data.get('grado', 'Desconocido')}**")
    
    st.sidebar.subheader("⚙️ Configuración del Gráfico")
    
    # --- LÓGICA ANTIGUA ELIMINADA ---
    # (Ahora todos los usuarios tienen todas las funciones premium por defecto)
    chart_options = ('Barras (Por Competencia)', 'Pastel (Proporción)')
    st.session_state.chart_type = st.sidebar.radio("Elige el tipo de visualización:", chart_options, key="chart_radio_premium")
    # -----------------------------------

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
            
            # --- ¡LÍNEA CORREGIDA! ---
            # (El error "KeyError: '% A'" estaba aquí. Faltaba '% A' y 'A (Est.)')
            data = {'Competencia': [], 'AD (Est.)': [], '% AD': [], 'A (Est.)': [], '% A': [], 'B (Est.)': [], '% B': [], 'C (Est.)': [], '% C': [], 'Total': []}
            # --------------------------
            
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
            
            # --- LÓGICA ANTIGUA ELIMINADA ---
            # (El botón ahora está siempre habilitado)
            if st.button(f"🎯 (Propuestas de mejora)", key=f"asistente_comp_{sheet_name}", type="primary"):
                if selected_comp_key in st.session_state and st.session_state[selected_comp_key]:
                    comp_name_limpio = st.session_state[selected_comp_key]
                    with st.expander(f"Ver Propuestas de mejora para: {comp_name_limpio}", expanded=True):
                        ai_report_text = pedagogical_assistant.generate_suggestions(results, sheet_name, comp_name_limpio)
                        st.markdown(ai_report_text, unsafe_allow_html=True)
                else:
                    st.warning("Selecciona una competencia en el desplegable de gráficos antes de generar el informe detallado.")
            
            # --- LÓGICA ANTIGUA ELIMINADA ---
            # (Se eliminó el caption "función Premium")

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
# === (¡VERSIÓN ACTUALIZADA CON CÓDIGO DE DONACIÓN YAPE!) ===
# =========================================================================

def home_page():
    
    # 1. MENSAJE DE BIENVENIDA (ACTUALIZADO PARA SUPABASE)
    if st.session_state.show_welcome_message:
        # Obtenemos el email del usuario desde el objeto 'user' de Supabase
        user_email = "Usuario"
        if hasattr(st.session_state, 'user') and st.session_state.user:
            # --- ¡MEJORA DE BIENVENIDA! ---
            # (Usamos el 'full_name' si existe, si no, el email)
            user_name = st.session_state.user.user_metadata.get('full_name', st.session_state.user.email)
            st.toast(f"¡Bienvenido, {user_name}!", icon="👋")
        
        st.session_state.show_welcome_message = False

    # --- ¡NUEVO BLOQUE DE INICIALIZACIÓN! ---
    # (Necesario para que el bloque de 'mostrar' no falle la primera vez)
    if 'sesion_generada' not in st.session_state:
        st.session_state.sesion_generada = None
    if 'docx_bytes' not in st.session_state:
        st.session_state.docx_bytes = None
    if 'tema_sesion' not in st.session_state:
        st.session_state.tema_sesion = ""
    # ----------------------------------------

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

    # --- ¡NUEVO BLOQUE DE DONACIÓN (YAPE)! ---
    # (Insertado en la barra lateral, encima del botón de logout)
    st.sidebar.divider() 
    st.sidebar.image("assets/qr-yape.png") # <-- ¡AQUÍ ESTÁ TU QR!
    st.sidebar.markdown(
        "<div style='text-align: center;'>"
        "¡Ayúdanos con tu colaboración para seguir sosteniendo nuestra página!"
        "</div>", 
        unsafe_allow_html=True
    )
    st.sidebar.divider()
    # --- FIN DEL BLOQUE DE DONACIÓN ---

    # --- Botón de cerrar sesión (ACTUALIZADO PARA SUPABASE) ---
    if st.sidebar.button("Cerrar Sesión", key="logout_sidebar_button"):
        try:
            # Avisar a Supabase que cierre sesión
            supabase.auth.sign_out()
        except Exception as e:
            st.warning(f"Error al cerrar sesión en Supabase: {e}")
        
        # Limpiar el estado de sesión local
        st.session_state.logged_in = False
        if hasattr(st.session_state, 'user'):
            del st.session_state.user
        
        st.rerun() # Recargar para mostrar la página de login
    # ---------------------------------------------------------

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
                # --- FORMULARIO DEPENDIENTE ---
                
                # PASO 1: Nivel
                st.subheader("Paso 1: Selecciona el Nivel")
                niveles = df_gen['NIVEL'].dropna().unique()
                nivel_sel = st.selectbox("Nivel", options=niveles, index=None, placeholder="Elige una opción...", key="asistente_nivel_sel", label_visibility="collapsed")
                
                # PASO 2: Grado
                st.subheader("Paso 2: Selecciona el Grado")
                grados_options = []
                if st.session_state.asistente_nivel_sel:
                    grados_options = df_gen[df_gen['NIVEL'] == st.session_state.asistente_nivel_sel]['GRADO CORRESPONDIENTE'].dropna().unique()
                
                grado_sel = st.selectbox("Grado", options=grados_options, index=None, placeholder="Elige un Nivel primero...", disabled=(not st.session_state.asistente_nivel_sel), key="asistente_grado_sel", label_visibility="collapsed")

                # PASO 3: Área
                st.subheader("Paso 3: Selecciona el Área")
                areas_options = []
                df_hoja_descriptor = None 
                
                if st.session_state.asistente_grado_sel:
                    if st.session_state.asistente_nivel_sel == "SECUNDARIA":
                        df_hoja_descriptor = df_desc_sec
                    elif st.session_state.asistente_nivel_sel == "PRIMARIA":
                        df_hoja_descriptor = df_desc_prim
                    
                    if df_hoja_descriptor is not None:
                        areas_options = df_hoja_descriptor['Área'].dropna().unique()
                
                area_sel = st.selectbox("Área", options=areas_options, index=None, placeholder="Elige un Grado primero...", disabled=(not st.session_state.asistente_grado_sel), key="asistente_area_sel", label_visibility="collapsed")

                # PASO 4: Competencia
                st.subheader("Paso 4: Selecciona la(s) Competencia(s)")
                competencias_options = []
                if st.session_state.asistente_area_sel and (df_hoja_descriptor is not None):
                    competencias_options = df_hoja_descriptor[
                        df_hoja_descriptor['Área'] == st.session_state.asistente_area_sel
                    ]['Competencia'].dropna().unique()

                competencias_sel = st.multiselect("Competencia(s)", options=competencias_options, placeholder="Elige un Área primero...", disabled=(not st.session_state.asistente_area_sel), key="asistente_competencias_sel", label_visibility="collapsed")
                
                form_disabled = not st.session_state.asistente_competencias_sel

                # PASO 5: Contextualización (FUERA DEL FORMULARIO)
                st.markdown("---")
                st.subheader("Paso 5: Contextualización (Opcional)")
                contexto_toggle = st.toggle("¿Desea contextualizar su sesión?", key="asistente_contexto", disabled=form_disabled)

                # PASO 6 y 7: Formulario de Detalles (DENTRO DEL FORMULARIO)
                with st.form(key="session_form"):
                    
                    # Campos de contextualización (Paso 5)
                    if st.session_state.asistente_contexto:
                        st.info("La IA usará estos datos para generar ejemplos y situaciones relevantes.")
                        region_sel = st.text_input("Región de su I.E.", placeholder="Ej: Lambayeque", disabled=form_disabled)
                        provincia_sel = st.text_input("Provincia de su I.E.", placeholder="Ej: Chiclayo", disabled=form_disabled)
                        distrito_sel = st.text_input("Distrito de su I.E.", placeholder="Ej: Monsefú", disabled=form_disabled)
                    else:
                        region_sel = None
                        provincia_sel = None
                        distrito_sel = None
                    
                    st.markdown("---")
                    
                    # PASO 6: Instrucciones Adicionales
                    st.subheader("Paso 6: Instrucciones Adicionales (Opcional)")
                    instrucciones_sel = st.text_area(
                        "Indica un enfoque específico para la IA", 
                        placeholder="Ej: Quiero reforzar el cálculo de porcentajes, ya que mis estudiantes tuvieron problemas la clase pasada.",
                        max_chars=500,
                        disabled=form_disabled
                    )

                    st.markdown("---")
                    st.subheader("Paso 7: Detalles de la Sesión")
                    
                    tema_sel = st.text_input("Escribe el tema o temática a tratar", placeholder="Ej: El sistema solar...", disabled=form_disabled)
                    tiempo_sel = st.selectbox("Selecciona la duración de la sesión", options=["90 minutos", "180 minutos"], index=None, placeholder="Elige una opción...", disabled=form_disabled)
                    
                    submitted = st.form_submit_button("Generar Sesión de Aprendizaje", disabled=form_disabled)
                    
                    if submitted:
                        if not tema_sel or not tiempo_sel:
                            st.error("Por favor, completa los campos del Paso 7.")
                            # Si falla la validación, borramos la sesión anterior
                            st.session_state.sesion_generada = None
                            st.session_state.docx_bytes = None
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
                                    
                                    ciclo_float = df_cic[df_cic['grados que corresponde'] == grado]['ciclo'].iloc[0]
                                    ciclo_encontrado = int(ciclo_float) 

                                    datos_filtrados = df_hoja_descriptor[
                                        (df_hoja_descriptor['Área'] == area) &
                                        (df_hoja_descriptor['Competencia'].isin(competencias))
                                    ]
                                    capacidades_lista = datos_filtrados['capacidad'].dropna().unique().tolist()
                                    
                                    columna_estandar_correcta = "DESCRIPCIÓN DE LOS NIVELES DEL DESARROLLO DE LA COMPETENCIA"
                                    
                                    estandares_lista = datos_filtrados[columna_estandar_correcta].dropna().unique().tolist()
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
                                        tiempo=tiempo,
                                        region=region_sel,
                                        provincia=provincia_sel,
                                        distrito=distrito_sel,
                                        instrucciones_docente=instrucciones_sel 
                                    )
                                    
                                    # 4. Generar el archivo Word en memoria
                                    docx_bytes = pedagogical_assistant.generar_docx_sesion(
                                        sesion_markdown_text=sesion_generada,
                                        area_docente=area 
                                    )
                                    
                                    # --- ¡CAMBIO ARQUITECTURAL! ---
                                    # 5. Guardamos todo en la 'memoria' (session_state)
                                    st.session_state.sesion_generada = sesion_generada
                                    st.session_state.docx_bytes = docx_bytes
                                    st.session_state.tema_sesion = tema_sel
                                    
                                    st.success("¡Sesión de aprendizaje generada!")
                                    # (El st.markdown y st.download_button se eliminan de aquí)
                                    # -------------------------------

                                except KeyError as e:
                                    st.error(f"Error de columna (KeyError): No se pudo encontrar la columna {e} en el DataFrame.")
                                    st.error("Verifica que los nombres de las columnas en tu Excel ('capacidad', 'DESCRIPCIÓN...', etc.) coincidan exact.")
                                    st.session_state.sesion_generada = None
                                    st.session_state.docx_bytes = None
                                except Exception as e:
                                    st.error(f"Ocurrió un error al generar la sesión:")
                                    st.error(e)
                                    st.session_state.sesion_generada = None
                                    st.session_state.docx_bytes = None
                
                # --- ¡NUEVO BLOQUE DE CÓDIGO! (FUERA DEL FORMULARIO) ---
                # Este bloque revisa la 'memoria' después de que el formulario se envía
                # y muestra el resultado y el botón de descarga.
                if st.session_state.sesion_generada:
                    st.markdown("---")
                    st.subheader("Resultado de la Generación")
                    st.markdown(st.session_state.sesion_generada)
                    
                    # ¡Ahora el botón de descarga es 'legal' porque está FUERA del form!
                    st.download_button(
                        label="Exportar Sesión a Word (.docx)",
                        data=st.session_state.docx_bytes,
                        file_name=f"sesion_{st.session_state.tema_sesion.replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="download_button_sesion"
                    )
                # ----------------------------------------------------

        elif st.session_state.asistente_tipo_herramienta == "Unidad de aprendizaje":
            st.info("Función de Unidades de Aprendizaje (Próximamente).")
        
        elif st.session_state.asistente_tipo_herramienta == "Planificación Anual":
            st.info("Función de Planificación Anual (Próximamente).")

# =========================================================================
# === EJECUCIÓN PRINCIPAL (EL "GUARDIAN") - v2.0 CON MANEJO DE CÓDIGO ===
# =========================================================================

# --- ¡NUEVA LÓGICA DE MANEJO DE CÓDIGO OAuth! ---
# Esto revisa si la URL tiene un "code" (viene de vuelta de Google)
query_params = st.query_params
auth_code = query_params.get("code")

if auth_code and not st.session_state.logged_in:
    try:
        # 1. Intercambia el código por una sesión
        # ¡Este era el paso que faltaba!
        session_data = supabase.auth.exchange_code_for_session(auth_code)
        
        # 2. Si tiene éxito, la sesión está en session_data.session
        if session_data.session:
            st.session_state.logged_in = True
            st.session_state.user = session_data.session.user
            st.session_state.show_welcome_message = True
            
            # 3. Limpia la URL (quita el ?code=...) y recarga
            st.query_params.clear() 
            st.rerun()

    except Exception as e:
        # Si el código ya se usó o expiró, dará un error.
        # Simplemente lo ignoramos y limpiamos la URL.
        st.query_params.clear() 
        pass # Continúa para mostrar la página de login
    
# --- El "Guardia de Seguridad" (La Puerta) ---
# Esta lógica solo se ejecuta si el bloque anterior no inició sesión
if not st.session_state.logged_in:
    # Si el usuario NO está logueado, muestra la página de login
    login_page()
else:
    # Si el usuario SÍ está logueado, ejecuta la app principal
    home_page()

# -------------------------------------------------------------------------







