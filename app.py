import json
import time
import random
from streamlit_lottie import st_lottie
import streamlit as st
import pandas as pd
import analysis_core
import pedagogical_assistant
import plotly.express as px
import io 
import xlsxwriter
import pptx_generator
import os 
import base64 
from supabase import create_client, Client
# --- FUNCIÓN PARA CARGAR ROBOTS (LOTTIE) ---
def cargar_lottie(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

# =========================================================================
# === 1. CONFIGURACIÓN INICIAL ===
# =========================================================================

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
  page_title="AulaMetrics", 
  page_icon="assets/isotipo.png",
  layout="wide",
  initial_sidebar_state="expanded"
)

# --- ESTILOS CSS: MAQUILLAJE FINAL (TIPOGRAFÍA ROBOTO + LIMPIEZA) ---
st.markdown("""
    <style>
    /* =========================================
       A. TIPOGRAFÍA INSTITUCIONAL (ROBOTO)
    ========================================= */
    /* Importamos la fuente de Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    /* Títulos: Fuertes y Estructurados */
    h1, h2, h3 { 
        font-weight: 900 !important; 
        letter-spacing: -0.5px;
        color: #1A237E; /* Azul oscuro institucional por defecto */
    }
    
    /* Texto general: Máxima legibilidad */
    p, div, label, span { 
        font-weight: 400;
        font-size: 16px; /* Un poco más grande para lectura cómoda */
    }

    /* =========================================
       B. LIMPIEZA DE INTERFAZ
    ========================================= */
    /* Ocultamos elementos innecesarios pero DEJAMOS el header funcional */
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }
    [data-testid="stHeaderActionElements"] { display: none !important; }
    footer { visibility: hidden; }
    
    /* EL CAMBIO CLAVE: No usamos display:none, sino transparencia */
    [data-testid="stHeader"] { 
        background-color: rgba(0,0,0,0) !important; /* Transparente */
        z-index: 999 !important; /* Asegurar que esté encima para poder dar click */
    }
    
    /* Ajustamos el color de los iconos del header (hamburguesa/flecha) a blanco/gris para que se vean */
    [data-testid="stHeader"] button {
        color: #1A237E !important;
    }
    
    /* Eliminar margen superior excesivo */
    .block-container {
        padding-top: 3rem !important; /* Un poco más de espacio para que no se solape con el botón del menú */
        padding-bottom: 0rem !important;
    }

    /* =========================================
       C. BARRA LATERAL GLOBAL (AZUL PROFUNDO)
    ========================================= */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a237e 0%, #283593 100%) !important;
        border-right: 1px solid #1a237e;
    }
    
    /* Forzar textos del sidebar a BLANCO */
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] li {
        color: #FFFFFF !important;
    }
    
    /* Estilo de botones dentro del Sidebar */
    section[data-testid="stSidebar"] div.stButton > button {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        font-weight: 500 !important; /* Peso medio para botones */
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-color: white !important;
    }
    
    /* Estilo Botón de Descarga General */
    div[data-testid="stDownloadButton"] > button {
        background-color: #007bff !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 👇 AQUÍ DEBE SEGUIR TU FUNCIÓN get_image_as_base64 (NO LA BORRES) 👇

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
# === 1.B. SISTEMA DE NAVEGACIÓN (EL GPS) ===
# =========================================================================

# Inicializamos la variable que controla dónde está el usuario
if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = 'Inicio'

# Función para cambiar de página
def navegar_a(pagina):
    st.session_state['pagina_actual'] = pagina

# =========================================================================
# === 1.C. PANTALLA DE INICIO (BLOQUEO POR CAPA INVISIBLE) ===
# =========================================================================
def mostrar_home():
    # --- PRUEBA ROJA (SOLO PARA VERIFICAR) ---
    st.markdown("""
        <style>
        /* ESTO DEBE PONER TODO EL FONDO DE ROJO */
        .block-container {
            background-color: red !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # --- CONTENIDO DE LA PÁGINA ---
    st.title("🚀 Bienvenido a AulaMetrics")
    st.markdown("### Selecciona una herramienta para comenzar:")
    st.divider()

    # --- FILA 1 ---
    col1, col2 = st.columns(2)
    
    with col1:
        # TARJETA 1
        st.markdown("""
        <div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; border: 1px solid #90caf9; height: auto; min-height: 220px;">
            <img src="https://img.icons8.com/fluency/96/bullish.png" style="display: block; margin-left: auto; margin-right: auto; width: 60px; margin-bottom: 10px;">
            <h3 style="color: #1565c0; text-align: center; margin-top: 0;">📊 Sistema de Evaluación</h3>
            <p style="text-align: center; color: #555;">Sube tus notas, visualiza estadísticas globales y genera libretas individuales en un solo lugar.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👉 Entrar a Evaluación", key="btn_home_evaluacion", use_container_width=True):
            navegar_a("Sistema de Evaluación") 
            st.rerun()

    with col2:
        # TARJETA 2
        st.markdown("""
        <div style="background-color: #f3e5f5; padding: 20px; border-radius: 10px; border: 1px solid #ce93d8; height: auto; min-height: 220px;">
            <img src="https://img.icons8.com/fluency/96/artificial-intelligence.png" style="display: block; margin-left: auto; margin-right: auto; width: 60px; margin-bottom: 10px;">
            <h3 style="color: #6a1b9a; text-align: center; margin-top: 0;">🧠 Asistente Pedagógico</h3>
            <p style="text-align: center; color: #555;">Diseña sesiones de aprendizaje y documentos curriculares con ayuda de la IA.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👉 Entrar al Asistente", key="btn_home_asistente", use_container_width=True):
            navegar_a("Asistente Pedagógico")
            st.rerun()

    st.write("") 

    # --- FILA 2 ---
    col3, col4 = st.columns(2)
    
    with col3:
        # TARJETA 3
        st.markdown("""
        <div style="background-color: #fff3e0; padding: 20px; border-radius: 10px; border: 1px solid #ffcc80; height: auto; min-height: 220px;">
            <img src="https://img.icons8.com/fluency/96/folder-invoices.png" style="display: block; margin-left: auto; margin-right: auto; width: 60px; margin-bottom: 10px;">
            <h3 style="color: #ef6c00; text-align: center; margin-top: 0;">📂 Banco de Recursos</h3>
            <p style="text-align: center; color: #555;">Descarga formatos oficiales, registros auxiliares y guías.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👉 Entrar a Recursos", key="btn_home_recursos", use_container_width=True):
            navegar_a("Recursos")
            st.rerun()

    with col4:
        # TARJETA 4
        st.markdown("""
        <div style="background-color: #fce4ec; padding: 20px; border-radius: 10px; border: 1px solid #f48fb1; height: auto; min-height: 220px;">
            <img src="https://img.icons8.com/fluency/96/controller.png" style="display: block; margin-left: auto; margin-right: auto; width: 60px; margin-bottom: 10px;">
            <h3 style="color: #c2185b; text-align: center; margin-top: 0;">🎮 Gamificación</h3>
            <p style="text-align: center; color: #555;">Crea trivias y juegos interactivos para motivar a tus estudiantes.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👉 Entrar a Juegos", key="btn_home_juegos", use_container_width=True):
            navegar_a("Gamificación")
            st.rerun()

# =========================================================================
# === 2. INICIALIZACIÓN SUPABASE Y ESTADO ===
# =========================================================================
try:
    supabase_url = st.secrets['supabase']['url']
    supabase_key = st.secrets['supabase']['anon_key']
    supabase: Client = create_client(supabase_url, supabase_key)
except KeyError:
    st.error("Error: Faltan las claves de Supabase en 'secrets.toml'.")
    st.stop()
except Exception as e:
    st.error(f"Error al conectar con Supabase: {e}")
    st.stop()

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

# =========================================================================
# === 3. ESTILOS CSS ===
# =========================================================================
st.markdown("""
<style>
    div.st-block-container { padding-top: 2rem; }
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@700&display=swap');

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
    
    div[data-testid="stTextInput"] input:focus {
        background-color: #FFFFE0;
        border: 2px solid #FFD700;
        box-shadow: 0 0 5px #FFD700;
    }
    
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
    
    .hero-container {
        text-align: center;
        padding: 0.2rem 0 2rem 0; 
    }
    .hero-logo {
        width: 120px;
        height: 120px;
        margin-bottom: 1rem;
    }
    .gradient-title-login { font-size: 5.0em; line-height: 1.1; }
    
    div.st-block-container > div:first-child { max-width: 100% !important; }
    [data-testid="stFullScreenButton"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# === 4. PÁGINA DE LOGIN (V11.0 - COLORES CORREGIDOS Y BOTONES SÓLIDOS) ===
# =========================================================================
def login_page():
    # --- A. INYECCIÓN DE ESTILO VISUAL ---
    st.markdown("""
    <style>
        /* 1. FONDO DEGRADADO */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #2e1437 0%, #948E99 100%);
            background: linear-gradient(135deg, #3E0E69 0%, #E94057 50%, #F27121 100%);
            background-size: cover;
            background-attachment: fixed;
        }
        
        /* 2. LIMPIEZA DE INTERFAZ */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 2rem !important;
        }
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            display: none !important;
        }
        
        /* 3. TARJETA DE CRISTAL */
        div[data-testid="stVerticalBlock"] > div:has(div.stForm) {
            background-color: rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(15px);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.4);
        }

        /* 4. TEXTOS GENERALES (Blancos fuera de la tarjeta) */
        h1, h2, h3, p {
            color: #FFFFFF !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        /* 5. TEXTOS DENTRO DEL FORMULARIO (Negros) */
        div.stForm label p, div.stForm h3, div.stForm h3 span {
            color: #1a1a1a !important;
            text-shadow: none !important;
            font-weight: 600 !important;
        }
        div.stForm p {
             color: #1a1a1a !important;
             text-shadow: none !important;
        }

        /* 6. INPUTS */
        input[type="text"], input[type="password"] {
            color: #000000 !important;
            background-color: rgba(255, 255, 255, 0.9) !important; /* Más blanco */
            border: 1px solid rgba(0, 0, 0, 0.2) !important;
            border-radius: 8px !important;
        }
        ::placeholder {
            color: #555555 !important;
            opacity: 1 !important;
        }

        /* 7. CORRECCIÓN PESTAÑAS (Tabs) */
        /* Texto Negro en las pestañas inactivas para que se lea */
        button[data-baseweb="tab"] div p {
            color: #333333 !important; 
            font-weight: bold !important;
            text-shadow: none !important;
        }
        /* Fondo blanco semitransparente para pestañas inactivas */
        button[data-baseweb="tab"] {
            background-color: rgba(255, 255, 255, 0.6) !important;
            border-radius: 8px !important;
            margin-right: 5px !important;
            border: 1px solid rgba(0,0,0,0.1) !important;
        }
        /* Pestaña Activa: Blanco Sólido y Texto Rosa */
        button[data-baseweb="tab"][aria-selected="true"] {
            background-color: #FFFFFF !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }
        button[data-baseweb="tab"][aria-selected="true"] div p {
            color: #E94057 !important; /* Rosa intenso */
        }
        
        /* 8. BOTÓN REGISTRARME (Hacerlo sólido) */
        /* Afecta a los botones secundarios dentro del form */
        div.stForm button[kind="secondary"] {
            background-color: #ffffff !important;
            color: #E94057 !important;
            border: 2px solid #E94057 !important;
            font-weight: bold !important;
        }
        div.stForm button[kind="secondary"]:hover {
            background-color: #E94057 !important;
            color: white !important;
        }

        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    # --- B. ESTRUCTURA ---
    col1, col_centro, col3 = st.columns([1, 4, 1]) 
    
    with col_centro:
        st.image("assets/logotipo-aulametrics.png", width=300)
        
        st.subheader("Bienvenido a AulaMetrics", anchor=False)
        st.markdown("**Tu asistente pedagógico y analista de datos.**")
        
        st.write("") 
        
        tab_login, tab_register = st.tabs(["Iniciar Sesión", "Registrarme"])

        # --- PESTAÑA 1: LOGIN ---
        with tab_login:
            with st.form("login_form"):
                st.markdown("### 🔐 Acceso Docente")
                email = st.text_input("Correo Electrónico", key="login_email", placeholder="ejemplo@escuela.edu.pe")
                password = st.text_input("Contraseña", type="password", key="login_password", placeholder="Ingresa tu contraseña")
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
                        if 'registro_exitoso' in st.session_state: del st.session_state['registro_exitoso']
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Error al iniciar sesión: {e}")

        # --- PESTAÑA 2: REGISTRO ---
        with tab_register:
            if 'form_reset_id' not in st.session_state:
                st.session_state['form_reset_id'] = 0
            reset_id = st.session_state['form_reset_id']

            if st.session_state.get('registro_exitoso', False):
                st.success("✅ ¡Cuenta creada con éxito!", icon="🎉")
                st.info("👈 Tus datos ya fueron registrados. Ve a la pestaña **'Iniciar Sesión'**.")
                
            with st.form("register_form"):
                st.markdown("### 📝 Nuevo Usuario")
                name = st.text_input("Nombre", key=f"reg_name_{reset_id}", placeholder="Tu nombre completo")
                email = st.text_input("Correo Electrónico", key=f"reg_email_{reset_id}", placeholder="tucorreo@email.com")
                password = st.text_input("Contraseña", type="password", key=f"reg_pass_{reset_id}", placeholder="Crea una contraseña")
                
                # Botón de Registrarme (Ahora se verá con borde rojo gracias al CSS)
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
                                    "data": { 'full_name': name }
                                }
                            })
                            st.session_state['form_reset_id'] += 1
                            st.session_state['registro_exitoso'] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error en el registro: {e}")

        st.divider()
        
        # BOTÓN DE CONTACTO (SÓLIDO Y ATRACTIVO)
        url_netlify = "https://chrisgonzalesllu1920-collab.github.io/aulametrics-landing/" 
        
        st.markdown(f"""
        <a href="{url_netlify}" target="_blank" style="
            display: inline-block;
            width: 100%;
            padding: 15px 0;
            background-color: #00C853; /* Verde WhatsApp / Éxito para invitar al clic */
            color: white;
            text-align: center;
            text-decoration: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 800;
            box-shadow: 0 4px 15px rgba(0, 200, 83, 0.4);
            transition: all 0.3s;
            border: none;
        ">
            💬 ¿Dudas? Contáctanos
        </a>
        """, unsafe_allow_html=True)
        
# =========================================================================
# === 5. FUNCIONES AUXILIARES ===
# =========================================================================
ISOTIPO_PATH = "assets/isotipo.png"
RUTA_ESTANDARES = "assets/Estandares de aprendizaje.xlsx" 

@st.cache_data(ttl=3600)
def cargar_datos_pedagogicos():
    try:
        df_generalidades = pd.read_excel(RUTA_ESTANDARES, sheet_name="Generalidades")
        df_ciclos = pd.read_excel(RUTA_ESTANDARES, sheet_name="Cicloseducativos")
        df_desc_sec = pd.read_excel(RUTA_ESTANDARES, sheet_name="Descriptorsecundaria")
        df_desc_prim = pd.read_excel(RUTA_ESTANDARES, sheet_name="Descriptorprimaria")
        
        df_generalidades['NIVEL'] = df_generalidades['NIVEL'].ffill()
        df_ciclos['ciclo'] = df_ciclos['ciclo'].ffill()
        
        columna_estandar = "DESCRIPCIÓN DE LOS NIVELES DEL DESARROLLO DE LA COMPETENCIA"
        
        cols_to_fill_prim = ['Área', 'Competencia', 'Ciclo', columna_estandar]
        cols_to_fill_sec = ['Área', 'Competencia', 'Ciclo', columna_estandar]
        
        df_desc_prim[cols_to_fill_prim] = df_desc_prim[cols_to_fill_prim].ffill()
        df_desc_sec[cols_to_fill_sec] = df_desc_sec[cols_to_fill_sec].ffill()
        
        return df_generalidades, df_ciclos, df_desc_sec, df_desc_prim
    
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo en la ruta: {RUTA_ESTANDARES}")
        return None, None, None, None
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo Excel: {e}")
        return None, None, None, None

# --- FUNCIÓN (UPLOADER) - v3.0 MULTI-HOJA ---
def configurar_uploader():
    """
    Procesa el archivo Excel.
    AHORA GUARDA TODAS LAS HOJAS EN MEMORIA para el análisis integral.
    """
    uploaded_file = st.file_uploader(
        "Sube tu archivo de Excel aquí", 
        type=["xlsx", "xls"], 
        key="file_uploader"
    )

    if uploaded_file is not None:
        with st.spinner('Procesando todas las áreas...'):
            try:
                # 1. Leer el archivo Excel
                excel_file = pd.ExcelFile(uploaded_file)
                sheet_names = excel_file.sheet_names
                
                # 2. Filtrar hojas que no son áreas (Generalidades, etc.)
                IGNORE_SHEETS = [analysis_core.GENERAL_SHEET_NAME.lower(), 'parametros', 'generalidades']
                valid_sheets = [name for name in sheet_names if name.lower() not in IGNORE_SHEETS]

                # 3. Ejecutar análisis de frecuencias (Tab 1)
                results_dict = analysis_core.analyze_data(excel_file, valid_sheets)
                st.session_state.info_areas = results_dict
                st.session_state.df_cargado = True
                
                # --- 4. ¡LA CLAVE! LEER Y GUARDAR TODAS LAS HOJAS ---
                # Creamos un diccionario donde guardaremos: {'Matemática': df_mate, 'Arte': df_arte...}
                all_dataframes = {}
                
                for sheet in valid_sheets:
                    try:
                        # Leemos cada hoja individualmente
                        df_temp = pd.read_excel(uploaded_file, sheet_name=sheet, header=0)
                        all_dataframes[sheet] = df_temp
                    except:
                        pass # Si una hoja falla, la saltamos para no romper todo
                
                # Guardamos este "Tesoro" en la memoria de la App
                st.session_state.all_dataframes = all_dataframes

                # Mantenemos st.session_state.df solo para compatibilidad (usamos la primera hoja)
                if valid_sheets:
                    st.session_state.df = all_dataframes[valid_sheets[0]]
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")
                st.session_state.df_cargado = False

def mostrar_analisis_general(results):
    st.markdown("---")
    st.subheader("Resultados Consolidados por Área")

    first_sheet_key = next(iter(results), None)
    general_data = {}
    if first_sheet_key and 'generalidades' in results[first_sheet_key]:
        general_data = results[first_sheet_key]['generalidades']
        st.info(f"Datos del Grupo: Nivel: **{general_data.get('nivel', 'Desconocido')}** | Grado: **{general_data.get('grado', 'Desconocido')}**")
    
    st.sidebar.subheader("⚙️ Configuración del Gráfico")
    
    chart_options = ('Barras (Por Competencia)', 'Pastel (Proporción)')
    st.session_state.chart_type = st.sidebar.radio("Elige el tipo de visualización:", chart_options, key="chart_radio_premium")

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
            st.download_button(label=f"⬇️ Exportar Excel ({sheet_name})", data=excel_data, file_name=f'Frecuencias_{sheet_name}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key=f'download_excel_{sheet_name}')

            st.markdown("---")
            competencia_nombres_limpios = df_table.index.tolist()
            selected_comp = None 

            if st.session_state.chart_type == 'Barras (Por Competencia)':
                selected_comp = st.selectbox(f"Selecciona la competencia:", options=competencia_nombres_limpios, key=f'select_comp_bar_{sheet_name}')
                df_bar_data = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']].rename(index={'AD (Est.)': 'AD', 'A (Est.)': 'A', 'B (Est.)': 'B', 'C (Est.)': 'C'})
                df_bar = df_bar_data.reset_index()
                df_bar.columns = ['Nivel', 'Estudiantes']
                fig = px.bar(df_bar, x='Nivel', y='Estudiantes', title=f"Logros: {selected_comp}", color='Nivel', color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'})
                st.plotly_chart(fig, use_container_width=True)
            
            elif st.session_state.chart_type == 'Pastel (Proporción)':
                selected_comp = st.selectbox(f"Selecciona la competencia:", options=competencia_nombres_limpios, key=f'select_comp_pie_{sheet_name}')
                data_pie_data = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']]
                data_pie = data_pie_data.reset_index()
                data_pie.columns = ['Nivel', 'Estudiantes']
                fig = px.pie(data_pie, values='Estudiantes', names='Nivel', title=f"Proporción: {selected_comp}", color='Nivel', color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'})
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            if selected_comp:
                st.session_state[f'selected_comp_{sheet_name}'] = selected_comp
            selected_comp_key = f'selected_comp_{sheet_name}'
            
            if st.button(f"🎯 Propuestas de mejora", key=f"asistente_comp_{sheet_name}", type="primary"):
                if selected_comp_key in st.session_state and st.session_state[selected_comp_key]:
                    comp_name_limpio = st.session_state[selected_comp_key]
                    with st.expander(f"Ver Propuestas de mejora para: {comp_name_limpio}", expanded=True):
                        ai_report_text = pedagogical_assistant.generate_suggestions(results, sheet_name, comp_name_limpio)
                        st.markdown(ai_report_text, unsafe_allow_html=True)
                else:
                    st.warning("Selecciona una competencia en el desplegable de gráficos.")

# =========================================================================
# === FUNCIÓN (TAB 2: ANÁLISIS POR ESTUDIANTE) - v5.0 FINAL CON WORD ===
# =========================================================================
def mostrar_analisis_por_estudiante(df_first, df_config, info_areas):
    """
    Muestra el perfil INTEGRAL y permite descargar INFORME WORD.
    """
    st.markdown("---")
    st.header("🧑‍🎓 Perfil Integral del Estudiante")
    
    if 'all_dataframes' not in st.session_state or not st.session_state.all_dataframes:
        st.warning("⚠️ No se han cargado datos. Sube un archivo en la Pestaña 1.")
        return

    all_dfs = st.session_state.all_dataframes
    
    # 1. DETECCIÓN DE COLUMNA
    posibles_nombres = [
        "Estudiante", "ESTUDIANTE", "APELLIDOS Y NOMBRES", "Apellidos y Nombres", 
        "ALUMNO", "Alumno", "Nombres y Apellidos", "Nombre Completo", 
        "Nombres", "NOMBRES"
    ]
    
    first_sheet_name = next(iter(all_dfs))
    df_base = all_dfs[first_sheet_name]
    
    col_nombre = None
    for col in df_base.columns:
        if str(col).strip() in posibles_nombres:
            col_nombre = col
            break
    
    if not col_nombre:
        st.error(f"❌ No encontramos la columna de nombres en la hoja '{first_sheet_name}'.")
        return

    # 2. SELECTOR
    lista_estudiantes = df_base[col_nombre].dropna().unique()
    estudiante_sel = st.selectbox("🔍 Busca al estudiante:", options=lista_estudiantes, index=None, placeholder="Escribe nombre...")

    if estudiante_sel:
        st.divider()
        st.subheader(f"📊 Reporte Global: {estudiante_sel}")
        
        # --- 3. BARRIDO CON MEMORIA DE ÁREAS ---
        total_conteo = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        desglose_areas = {'AD': [], 'A': [], 'B': [], 'C': []}
        areas_analizadas = 0
        
        # Barra de progreso
        my_bar = st.progress(0, text="Analizando áreas...")
        total_sheets = len(all_dfs)
        
        for i, (area_name, df_area) in enumerate(all_dfs.items()):
            my_bar.progress((i + 1) / total_sheets, text=f"Revisando: {area_name}")
            
            c_name_local = None
            for c in df_area.columns:
                if str(c).strip() in posibles_nombres:
                    c_name_local = c
                    break
            
            if c_name_local:
                fila = df_area[df_area[c_name_local] == estudiante_sel]
                if not fila.empty:
                    areas_analizadas += 1
                    vals = [str(v).upper().strip() for v in fila.iloc[0].values]
                    
                    c_ad = vals.count('AD')
                    c_a = vals.count('A')
                    c_b = vals.count('B')
                    c_c = vals.count('C')
                    
                    total_conteo['AD'] += c_ad
                    total_conteo['A'] += c_a
                    total_conteo['B'] += c_b
                    total_conteo['C'] += c_c
                    
                    if c_ad > 0: desglose_areas['AD'].append(f"{area_name} ({c_ad})")
                    if c_a > 0: desglose_areas['A'].append(f"{area_name} ({c_a})")
                    if c_b > 0: desglose_areas['B'].append(f"{area_name} ({c_b})")
                    if c_c > 0: desglose_areas['C'].append(f"{area_name} ({c_c})")

        my_bar.empty()
        
        # --- 4. MOSTRAR RESULTADOS CON DETALLE ---
        suma_total = sum(total_conteo.values())
        
        col_izq, col_der = st.columns([1, 1.5])
        
        with col_izq:
            st.markdown("#### 📈 Detalle por Nivel")
            st.caption(f"Se analizaron {areas_analizadas} áreas en total.")
            
            # AD
            if total_conteo['AD'] > 0:
                with st.expander(f"🏆 Logro Destacado (AD): {total_conteo['AD']}", expanded=False):
                    for area in desglose_areas['AD']: st.markdown(f"- {area}")
            else:
                st.markdown(f"🏆 **AD:** 0")

            # A
            if total_conteo['A'] > 0:
                with st.expander(f"✅ Logro Esperado (A): {total_conteo['A']}", expanded=False):
                    for area in desglose_areas['A']: st.markdown(f"- {area}")
            else:
                st.markdown(f"✅ **A:** 0")

            # B
            if total_conteo['B'] > 0:
                with st.expander(f"⚠️ En Proceso (B): {total_conteo['B']}", expanded=True):
                    st.markdown("**:orange[Áreas a reforzar:]**")
                    for area in desglose_areas['B']: st.markdown(f"- {area}")
            else:
                st.markdown(f"⚠️ **B:** 0")

            # C
            if total_conteo['C'] > 0:
                with st.expander(f"🛑 En Inicio (C): {total_conteo['C']}", expanded=True):
                    st.markdown("**:red[Requiere atención urgente en:]**")
                    for area in desglose_areas['C']: st.markdown(f"- {area}")
            else:
                st.markdown(f"🛑 **C:** 0")

        with col_der:
            if suma_total > 0:
                df_chart = pd.DataFrame({'Nivel': list(total_conteo.keys()), 'Cantidad': list(total_conteo.values())})
                df_chart = df_chart[df_chart['Cantidad'] > 0]
                fig = px.pie(
                    df_chart, values='Cantidad', names='Nivel', 
                    title=f"Mapa de Calor Académico",
                    color='Nivel',
                    color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'},
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin registros de notas.")

        # --- 5. BOTÓN DE DESCARGA DE INFORME (NUEVO) ---
        st.write("---")
        st.write("#### 📥 Opciones de Exportación")
        
        if suma_total > 0:
            # Llamamos a la función que creamos en pedagogical_assistant.py
            # Asumimos que lo tienes importado como 'pedagogical_assistant'
            import pedagogical_assistant # Importación local por seguridad
            
            with st.spinner("Generando informe en Word..."):
                doc_buffer = pedagogical_assistant.generar_reporte_estudiante(
                    estudiante_sel, 
                    total_conteo, 
                    desglose_areas
                )
            
# 1. INSERTAMOS EL ESTILO AZUL (CSS)
            st.markdown("""
                <style>
                div.stDownloadButton > button:first-child {
                    background-color: #0056b3; /* Azul Profesional */
                    color: white;
                    border-radius: 8px;
                    border: 1px solid #004494;
                }
                div.stDownloadButton > button:first-child:hover {
                    background-color: #004494; /* Azul más oscuro al pasar el mouse */
                    color: white;
                    border-color: #002a5c;
                }
                </style>
            """, unsafe_allow_html=True)

            # 2. EL BOTÓN (Sin type="primary")
            st.download_button(
                label="📄 Descargar Informe de Progreso (Word)",
                data=doc_buffer,
                file_name=f"Informe_Progreso_{estudiante_sel}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
                # Nota: He borrado la línea 'type="primary"' para que el azul funcione
            )

# --- FUNCIÓN (Conversión a Excel) - MEJORADA (Colores y Anchos) ---
@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    """
    Convierte DataFrame a formato Excel (xlsx) con formato profesional:
    - Columna de Competencias ancha.
    - Encabezados de colores (AD=Verde, B=Naranja, C=Rojo).
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 1. Escribir las hojas
        workbook = writer.book
        
        # --- Hoja Generalidades ---
        info_sheet = workbook.add_worksheet("Generalidades")
        bold_fmt = workbook.add_format({'bold': True})
        info_sheet.write('A1', 'Área:', bold_fmt)
        info_sheet.write('B1', area_name)
        info_sheet.write('A2', 'Nivel:', bold_fmt)
        info_sheet.write('B2', general_info.get('nivel', 'N/A'))
        info_sheet.write('A3', 'Grado:', bold_fmt)
        info_sheet.write('B3', general_info.get('grado', 'N/A'))
        
        # --- Hoja Frecuencias (Aquí está la magia) ---
        df.to_excel(writer, sheet_name='Frecuencias', startrow=0, startcol=0, index=True)
        worksheet = writer.sheets['Frecuencias']

        # 2. Definir Formatos de Colores (Estilo Pastel Profesional)
        # AD y A (Verdes)
        fmt_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # B (Naranja/Amarillo)
        fmt_orange = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # C (Rojo)
        fmt_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # Cabecera Genérica (Gris)
        fmt_header = workbook.add_format({'bg_color': '#D3D3D3', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # Texto normal (Alineado a la izquierda para competencias)
        fmt_text = workbook.add_format({'text_wrap': True, 'valign': 'vcenter'})

        # 3. Ajustar Ancho de Columnas
        # Columna A (Índice/Competencia): Muy ancha (60) para que entre todo el texto
        worksheet.set_column('A:A', 60, fmt_text)

        # 👇 CAMBIO FINAL: Ancho 9 (Equilibrio perfecto) 👇
        # Aplica a todas las columnas de datos (AD, A, B, C, Porcentajes...)
        worksheet.set_column('B:Z', 9)

        # 4. Pintar los Encabezados con Lógica
        # (Sobrescribimos la fila 0 con los colores correctos)
        
        # Primero pintamos la celda A1 (El título "Competencia")
        worksheet.write(0, 0, "Competencia", fmt_header)

        # Ahora recorremos las columnas de datos (AD, % AD, etc.)
        # df.columns son los nombres. enumerate nos da (0, 'AD'), (1, '% AD')...
        for col_num, value in enumerate(df.columns.values):
            val_str = str(value).upper() # Convertimos a mayúsculas para comparar
            
            # Elegimos el color según la letra
            if "AD" in val_str or ("A" in val_str and "% A" in val_str) or "A (EST.)" in val_str:
                cell_format = fmt_green
            elif "B" in val_str:
                cell_format = fmt_orange
            elif "C" in val_str:
                cell_format = fmt_red
            else:
                cell_format = fmt_header # Por defecto (ej: Total)

            # Escribimos en la fila 0, columna (col_num + 1 porque la A es el índice)
            worksheet.write(0, col_num + 1, value, cell_format)

    return output.getvalue()

# --- FUNCIÓN AUXILIAR: BARRA LATERAL DE NAVEGACIÓN (V3 - CON LOGOUT) ---
def mostrar_sidebar():
    """
    Muestra el menú lateral. Detecta el contexto para mostrar herramientas.
    """
    with st.sidebar:
        # 1. BOTÓN VOLVER (Siempre visible si no estamos en Inicio)
        if st.session_state.get('pagina_actual') != 'Inicio':
            st.divider()
            if st.button("🏠 Volver al Menú Principal", use_container_width=True):
                navegar_a("Inicio")
                st.rerun()

        # 2. BOTÓN DE CARGA DE ARCHIVO (Solo visible en Evaluación)
        if st.session_state.get('pagina_actual') == 'Sistema de Evaluación':
            st.divider()
            if st.button("📂 Subir Nuevo Archivo", use_container_width=True):
                # Limpieza total de datos para permitir nueva carga
                st.session_state.df_cargado = False
                st.session_state.info_areas = None
                st.session_state.all_dataframes = None
                st.session_state.df = None
                # Truco para limpiar el widget de carga
                if 'file_uploader' in st.session_state:
                    del st.session_state['file_uploader']
                st.rerun()

        # 3. BOTÓN CERRAR SESIÓN (NUEVO)
        st.write("") # Espacio vertical
        st.write("") 
        
        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            st.session_state.clear() # Borra toda la memoria
            st.rerun() # Reinicia la app (te llevará al Login)

        # 4. PIE DE PÁGINA
        st.divider()
        if st.session_state.get('pagina_actual') == 'Inicio':
            st.info("👋 Selecciona una herramienta del panel.")
        else:
            st.caption(f"📍 Sección: {st.session_state.get('pagina_actual')}")
        
        st.caption("🏫 AulaMetrics v3.0 Beta")

# =========================================================================
# === 5.5. SUB-VISTA: PORTADA (V7.1 - HORA PERÚ CORREGIDA) ===
# =========================================================================
def mostrar_home():
    """Dibuja la parrilla de tarjetas con Saludo Contextual (Hora Perú)."""
    
    # --- A. LÓGICA DE TIEMPO Y FECHA (AJUSTE PERÚ) ---
    from datetime import datetime, timedelta
    
    # Obtenemos la hora del servidor y restamos 5 horas (UTC-5)
    ahora_servidor = datetime.now()
    ahora = ahora_servidor - timedelta(hours=5)
    
    hora = ahora.hour
    
    # 1. Determinar el Saludo
    if 5 <= hora < 12:
        saludo = "Buenos días"
        emoji_saludo = "☀️"
    elif 12 <= hora < 19:
        saludo = "Buenas tardes"
        emoji_saludo = "🌤️"
    else:
        saludo = "Buenas noches"
        emoji_saludo = "🌙"
        
    # 2. Formatear la Fecha en Español
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    dia_nombre = dias_semana[ahora.weekday()]
    dia_numero = ahora.day
    mes_nombre = meses[ahora.month - 1]
    
    fecha_texto = f"{dia_nombre}, {dia_numero} de {mes_nombre}"

    # --- B. ESTILOS CSS (EXACTAMENTE TU CÓDIGO V6.1) ---
    st.markdown("""
        <style>
        /* --- 1. ELIMINAR MÁRGENES DE STREAMLIT --- */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* Ocultamos el header */
        header { visibility: hidden !important; }
        [data-testid="stHeader"] { display: none !important; }

        /* --- 2. BARRA LATERAL (INTOCABLE) --- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a237e 0%, #283593 100%) !important;
            border-right: 1px solid #1a237e;
        }
        section[data-testid="stSidebar"] * { color: white !important; }
        section[data-testid="stSidebar"] div.stButton > button {
            background-color: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }

        /* --- 3. FONDO PRINCIPAL (MORADO ÉPICO) --- */
        [data-testid="stAppViewContainer"] {
            background-color: #4A148C !important;
            background: 
                radial-gradient(circle at 85% 5%, rgba(255, 109, 0, 0.60) 0%, transparent 60%),
                radial-gradient(circle at 0% 100%, rgba(0, 229, 255, 0.3) 0%, transparent 50%),
                linear-gradient(135deg, #311B92 0%, #4A148C 100%) !important;
        }

        /* --- 4. TARJETAS GEOMÉTRICAS --- */
        section[data-testid="stMain"] div.stButton > button {
            width: 100%;
            min-height: 240px !important; 
            height: 100% !important;
            
            background-color: #FFFFFF !important;
            border: none !important;
            border-left: 8px solid #FFD600 !important;
            border-radius: 24px !important;
            
            box-shadow: 0 15px 35px rgba(0,0,0,0.2) !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 30px !important;
            text-align: center !important;
        }

        section[data-testid="stMain"] div.stButton > button:hover {
            transform: translateY(-8px) scale(1.03);
            box-shadow: 0 30px 60px rgba(0,0,0,0.5) !important;
            z-index: 10;
        }

        section[data-testid="stMain"] div.stButton > button p {
            font-size: 24px !important;
            font-weight: 800 !important;
            color: #263238 !important;
            margin-top: 15px !important;
        }
        
        section[data-testid="stMain"] div.stButton > button small {
            font-size: 16px !important;
            color: #78909C !important;
        }

        .card-icon {
            font-size: 60px;
            margin-bottom: 0px; 
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.15));
        }
        </style>
    """, unsafe_allow_html=True)

    # --- C. ENCABEZADO DINÁMICO (AQUÍ USAMOS LAS VARIABLES) ---
    st.markdown(f"""
        <div style="margin-bottom: 30px; padding-top: 10px; text-align: center;">
            <h1 style="color: #FFFFFF; font-size: 52px; margin-bottom: 5px; font-weight: 900; text-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                ¡{saludo}, Docente! {emoji_saludo}
            </h1>
            <p style="color: #FFD54F; font-size: 20px; font-weight: 500; letter-spacing: 1px; text-transform: uppercase;">
                📅 {fecha_texto}
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- D. PARRILLA GEOMÉTRICA (Igual que antes) ---
    c1, c2 = st.columns(2, gap="large")
    
    with c1:
        st.markdown('<div class="card-icon" style="text-align: center; margin-bottom: -80px; position: relative; z-index: 5; pointer-events: none;">📊</div>', unsafe_allow_html=True)
        if st.button("\n\n\nSistema de Evaluación", key="card_eval"):
            navegar_a("Sistema de Evaluación")
            st.rerun()

    with c2:
        st.markdown('<div class="card-icon" style="text-align: center; margin-bottom: -80px; position: relative; z-index: 5; pointer-events: none;">🧠</div>', unsafe_allow_html=True)
        if st.button("\n\n\nAsistente Pedagógico", key="card_ia"):
            navegar_a("Asistente Pedagógico")
            st.rerun()

    st.write("") 

    c3, c4 = st.columns(2, gap="large")
    
    with c3:
        st.markdown('<div class="card-icon" style="text-align: center; margin-bottom: -80px; position: relative; z-index: 5; pointer-events: none;">🎮</div>', unsafe_allow_html=True)
        if st.button("\n\n\nZona de Gamificación", key="card_games"):
            navegar_a("Gamificación")
            st.rerun()

    with c4:
        st.markdown('<div class="card-icon" style="text-align: center; margin-bottom: -80px; position: relative; z-index: 5; pointer-events: none;">📚</div>', unsafe_allow_html=True)
        if st.button("\n\n\nBanco de Recursos", key="card_resources"):
            navegar_a("Recursos")
            st.rerun()
            
    st.markdown("<br><br>", unsafe_allow_html=True)

# =========================================================================
# === 6. FUNCIÓN PRINCIPAL `home_page` (EL DASHBOARD) v5.0 ===
# =========================================================================
def home_page():
    
    # 1. Mensaje de Bienvenida (Mantenemos tu lógica)
    if st.session_state.show_welcome_message:
        user_name = "Profe"
        if hasattr(st.session_state, 'user') and st.session_state.user:
             user_name = st.session_state.user.user_metadata.get('full_name', 'Profe')
        st.toast(f"¡Hola, {user_name}!", icon="👋")
        st.session_state.show_welcome_message = False

    # 2. Inicialización de Variables
    if 'sesion_generada' not in st.session_state: st.session_state.sesion_generada = None
    if 'docx_bytes' not in st.session_state: st.session_state.docx_bytes = None
    if 'tema_sesion' not in st.session_state: st.session_state.tema_sesion = ""

    # 3. ACTIVAR BARRA LATERAL (La función de la Sección 5)
    mostrar_sidebar()

    # 4. CONTROLADOR DE PÁGINAS (GPS)
    pagina = st.session_state['pagina_actual']

# --- ESCENARIO A: ESTAMOS EN EL LOBBY (INICIO) ---
    if pagina == 'Inicio':
            
        # DIBUJAMOS LAS TARJETAS DEL MENÚ
        mostrar_home()

        # (Nota: El código de Yape/Logout del sidebar antiguo desaparece aquí momentáneamente
        # para limpiar la interfaz. Lo podemos reintegrar luego en mostrar_sidebar si lo deseas).

# --- ESCENARIO B: HERRAMIENTAS (CONEXIÓN LÓGICA) ---

    # 1. SISTEMA DE EVALUACIÓN (UNIFICADO: CARGA + VISTAS)
    if pagina == "Sistema de Evaluación":
        
        # A) Si NO hay datos cargados, mostramos el cargador
        if not st.session_state.df_cargado:
            st.header("📊 Sistema de Evaluación")
            st.info("Para comenzar, sube tu registro de notas (Excel).")
            # Llamamos a tu función de carga existente
            configurar_uploader()
            
        # B) Si YA hay datos, mostramos el panel con pestañas internas
        else:
            # Creamos pestañas internas solo para esta herramienta
            tab_global, tab_individual = st.tabs(["🌎 Vista Global", "👤 Vista por Estudiante"])
            
            with tab_global:
                st.subheader("Panorama General del Aula")
                info_areas = st.session_state.info_areas
                mostrar_analisis_general(info_areas)
                
            with tab_individual:
                st.subheader("Libreta Individual")
                df = st.session_state.df
                df_config = st.session_state.df_config
                info_areas = st.session_state.info_areas
                mostrar_analisis_por_estudiante(df, df_config, info_areas)

    # 3. ASISTENTE PEDAGÓGICO
    elif pagina == "Asistente Pedagógico":
        st.header("🧠 Asistente Pedagógico")

        # Función de limpieza local
        def limpiar_resultados():
            keys_to_clear = ['sesion_generada', 'docx_bytes', 'doc_buffer']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]

        tipo_herramienta = st.radio(
            "01. Selecciona la herramienta que deseas usar:",
            options=["Sesión de aprendizaje", "Unidad de aprendizaje", "Planificación Anual"],
            index=0, 
            horizontal=True, 
            key="asistente_tipo_herramienta",
            on_change=limpiar_resultados
        )
        st.markdown("---")

        if st.session_state.asistente_tipo_herramienta == "Sesión de aprendizaje":
            st.subheader("Generador de Sesión de Aprendizaje")
            df_gen, df_cic, df_desc_sec, df_desc_prim = cargar_datos_pedagogicos()
            
            if df_gen is None:
                st.error("Error crítico: No se pudieron cargar los estándares.")
            else:
                st.subheader("Paso 1: Selecciona el Nivel")
                niveles = df_gen['NIVEL'].dropna().unique()
                
                nivel_sel = st.selectbox(
                    "Nivel", 
                    options=niveles, 
                    index=None, 
                    placeholder="Elige una opción...", 
                    key="asistente_nivel_sel", 
                    label_visibility="collapsed",
                    on_change=limpiar_resultados
                )
                
                st.subheader("Paso 2: Selecciona el Grado")
                grados_options = []
                if st.session_state.asistente_nivel_sel:
                    grados_options = df_gen[df_gen['NIVEL'] == st.session_state.asistente_nivel_sel]['GRADO CORRESPONDIENTE'].dropna().unique()
                
                grado_sel = st.selectbox(
                    "Grado", 
                    options=grados_options, 
                    index=None, 
                    placeholder="Elige un Nivel primero...", 
                    disabled=(not st.session_state.asistente_nivel_sel), 
                    key="asistente_grado_sel", 
                    label_visibility="collapsed",
                    on_change=limpiar_resultados
                )
                
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

                st.subheader("Paso 4: Selecciona la(s) Competencia(s)")
                competencias_options = []
                if st.session_state.asistente_area_sel and (df_hoja_descriptor is not None):
                    competencias_options = df_hoja_descriptor[
                        df_hoja_descriptor['Área'] == st.session_state.asistente_area_sel
                    ]['Competencia'].dropna().unique()
                competencias_sel = st.multiselect("Competencia(s)", options=competencias_options, placeholder="Elige un Área primero...", disabled=(not st.session_state.asistente_area_sel), key="asistente_competencias_sel", label_visibility="collapsed")
                
                form_disabled = not st.session_state.asistente_competencias_sel

                st.markdown("---")
                st.subheader("Paso 5: Contextualización (Opcional)")
                contexto_toggle = st.toggle("¿Desea contextualizar su sesión?", key="asistente_contexto", disabled=form_disabled)

                with st.form(key="session_form"):
                    if st.session_state.asistente_contexto:
                        st.info("La IA usará estos datos para generar ejemplos y situaciones relevantes.")
                        region_sel = st.text_input("Región de su I.E.", placeholder="Ej: Lambayeque", disabled=form_disabled)
                        provincia_sel = st.text_input("Provincia de su I.E.", placeholder="Ej: Chiclayo", disabled=form_disabled)
                        distrito_sel = st.text_input("Distrito de su I.E.", placeholder="Ej: Monsefú", disabled=form_disabled)
                    else:
                        region_sel = None; provincia_sel = None; distrito_sel = None
                    
                    st.markdown("---")
                    st.subheader("Paso 6: Instrucciones Adicionales (Opcional)")
                    instrucciones_sel = st.text_area("Indica un enfoque específico para la IA", placeholder="Ej: Quiero reforzar el cálculo de porcentajes...", max_chars=500, disabled=form_disabled)

                    st.markdown("---")
                    st.subheader("Paso 7: Detalles de la Sesión")
                    tema_sel = st.text_input("Escribe el tema o temática a tratar", placeholder="Ej: El sistema solar...", disabled=form_disabled)
                    tiempo_sel = st.selectbox("Selecciona la duración de la sesión", options=["90 minutos", "180 minutos"], index=None, placeholder="Elige una opción...", disabled=form_disabled)
                    
                    submitted = st.form_submit_button("Generar Sesión de Aprendizaje", disabled=form_disabled)
                    
                    if submitted:
                        if not tema_sel or not tiempo_sel:
                            st.error("Por favor, completa los campos del Paso 7.")
                            st.session_state.sesion_generada = None
                            st.session_state.docx_bytes = None
                        else:
                            with st.spinner("🤖 Generando tu sesión de aprendizaje..."):
                                try:
                                    nivel = st.session_state.asistente_nivel_sel
                                    grado = st.session_state.asistente_grado_sel
                                    area = st.session_state.asistente_area_sel
                                    competencias = st.session_state.asistente_competencias_sel 
                                    tema = tema_sel
                                    tiempo = tiempo_sel
                                    
                                    ciclo_float = df_cic[df_cic['grados que corresponde'] == grado]['ciclo'].iloc[0]
                                    ciclo_encontrado = int(ciclo_float) 
                                    datos_filtrados = df_hoja_descriptor[(df_hoja_descriptor['Área'] == area) & (df_hoja_descriptor['Competencia'].isin(competencias))]
                                    capacidades_lista = datos_filtrados['capacidad'].dropna().unique().tolist()
                                    columna_estandar_correcta = "DESCRIPCIÓN DE LOS NIVELES DEL DESARROLLO DE LA COMPETENCIA"
                                    estandares_lista = datos_filtrados[columna_estandar_correcta].dropna().unique().tolist()
                                    estandar_texto_completo = "\n\n".join(estandares_lista)

                                    sesion_generada = pedagogical_assistant.generar_sesion_aprendizaje(
                                        nivel=nivel, grado=grado, ciclo=str(ciclo_encontrado), area=area,
                                        competencias_lista=competencias, capacidades_lista=capacidades_lista,
                                        estandar_texto=estandar_texto_completo, tematica=tema, tiempo=tiempo,
                                        region=region_sel, provincia=provincia_sel, distrito=distrito_sel,
                                        instrucciones_docente=instrucciones_sel 
                                    )
                                    docx_bytes = pedagogical_assistant.generar_docx_sesion(sesion_markdown_text=sesion_generada, area_docente=area)
                                    
                                    st.session_state.sesion_generada = sesion_generada
                                    st.session_state.docx_bytes = docx_bytes
                                    st.session_state.tema_sesion = tema_sel
                                    st.success("¡Sesión generada!")

                                except Exception as e:
                                    st.error(f"Error: {e}")
                                    st.session_state.sesion_generada = None
                
            # MOSTRAR RESULTADOS
            if st.session_state.sesion_generada:
                st.markdown("---")
                st.subheader("Resultado")
                st.markdown(st.session_state.sesion_generada)
                
                st.success("¡Sesión generada con éxito!")
                
                # ZONA DE DESCARGA
                if st.session_state.get('docx_bytes'):
                    st.download_button(
                        label="📄 Descargar Sesión en Word",
                        data=st.session_state.docx_bytes, 
                        file_name="Sesion_Aprendizaje.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ El archivo expiró. Por favor genera la sesión de nuevo.")

        elif st.session_state.asistente_tipo_herramienta == "Unidad de aprendizaje":
            st.info("Función de Unidades de Aprendizaje (Próximamente).")
        
        elif st.session_state.asistente_tipo_herramienta == "Planificación Anual":
            st.info("Función de Planificación Anual (Próximamente).")

    # 4. RECURSOS
    elif pagina == "Recursos":
        st.header("📂 Banco de Recursos Pedagógicos")
        st.markdown("Descarga formatos, plantillas y guías útiles para tu labor docente.")
        st.divider()

        col_formatos, col_guias = st.columns(2)

        with col_formatos:
            st.subheader("📝 Formatos Editables")
            st.info("Plantillas en Word y Excel listas para usar.")
            
            # RECURSO 1: SECUNDARIA
            ruta_archivo_1 = "recursos/Registro automatizado nivel secundario.xlsm" 
            if os.path.exists(ruta_archivo_1):
                with open(ruta_archivo_1, "rb") as file:
                    st.download_button(
                        label="📥 Descargar Registro Automatizado - Secundaria (Excel)",
                        data=file,
                        file_name="Registro_Secundaria.xlsm",
                        mime="application/vnd.ms-excel.sheet.macroEnabled.12", 
                        use_container_width=True
                    )
            else:
                st.caption(f"❌ Archivo no encontrado: {ruta_archivo_1}")

            st.write("")
            
            # RECURSO 2: PRIMARIA
            ruta_archivo_2 = "recursos/Registro automatizado nivel primario.xlsm" 
            if os.path.exists(ruta_archivo_2):
                with open(ruta_archivo_2, "rb") as file:
                    st.download_button(
                        label="📥 Descargar Registro Automatizado - Primaria (Excel)",
                        data=file,
                        file_name="Registro_Primaria.xlsm",
                        mime="application/vnd.ms-excel.sheet.macroEnabled.12", 
                        use_container_width=True
                    )
            else:
                st.caption(f"❌ Archivo no encontrado: {ruta_archivo_2}")

            st.write("")
            
            # RECURSO 3: CALENDARIO
            ruta_archivo_3 = "recursos/calendario_2025.pdf" 
            if os.path.exists(ruta_archivo_3):
                with open(ruta_archivo_3, "rb") as file:
                    st.download_button("📥 Descargar Calendario Cívico (PDF)", file, "Calendario_Civico_2025.pdf", "application/pdf", use_container_width=True)
            else:
                st.caption("❌ Archivo 'calendario_2025.pdf' no disponible.")

# 5. GAMIFICACIÓN (VERSIÓN LIMPIA V3)
    elif pagina == "Gamificación":
        
        # --- A. GESTIÓN DE ESTADO ---
        if 'juego_actual' not in st.session_state:
            st.session_state['juego_actual'] = None 

        def volver_menu_juegos():
            st.session_state['juego_actual'] = None
            st.rerun()

# --- B. DEFINICIÓN DEL MENÚ (ESTILO C: GAME CARTRIDGE - ALTO CONTRASTE) ---
        def mostrar_menu_juegos():
            # 1. CSS VIBRANTE (SOLO ZONA PRINCIPAL)
            st.markdown("""
            <style>
                /* Selector específico para la zona principal (NO Sidebar) */
                section[data-testid="stMain"] div.stButton > button {
                    /* FONDO: Degradado Intenso (Indigo a Morado) para contrastar con el gris */
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                    
                    /* Borde y Forma */
                    border: none !important;
                    border-radius: 20px !important; /* Muy redondeado */
                    
                    /* Texto */
                    color: white !important;
                    font-family: 'Verdana', sans-serif !important;
                    text-transform: uppercase !important;
                    letter-spacing: 1px !important;
                    
                    /* Sombra de "Tarjeta Flotante" */
                    box-shadow: 0 10px 20px rgba(118, 75, 162, 0.3) !important;
                    
                    /* Geometría */
                    height: auto !important;
                    padding: 25px 15px !important;
                    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
                }

                /* Hover: Se eleva y brilla */
                section[data-testid="stMain"] div.stButton > button:hover {
                    transform: translateY(-6px) scale(1.02);
                    box-shadow: 0 15px 30px rgba(118, 75, 162, 0.5) !important;
                    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important; /* Invierte degradado */
                }

                /* Texto del Título e Icono */
                section[data-testid="stMain"] div.stButton > button p {
                    font-size: 19px !important;
                    font-weight: 800 !important;
                    margin: 0 !important;
                    line-height: 1.4 !important;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }
            </style>
            """, unsafe_allow_html=True)

            # TÍTULO (Ajustado a color oscuro para que se lea en el gris)
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #4A148C; font-size: 38px; font-weight: 900; letter-spacing: -1px;">🎮 ARCADE PEDAGÓGICO</h2>
                <p style="color: #616161; font-size: 18px; font-weight: 500;">Selecciona tu desafío</p>
            </div>
            """, unsafe_allow_html=True)

            # --- PARRILLA DE JUEGOS ---
            col1, col2 = st.columns(2, gap="large")
            
            with col1:
                # TRIVIA
                if st.button("🧠 TRIVIA\n\n¿Cuánto sabes?", key="btn_card_trivia", use_container_width=True):
                    st.session_state['juego_actual'] = 'trivia'
                    st.rerun()

            with col2:
                # PUPILETRAS
                if st.button("🔤 PUPILETRAS\n\nAgudeza Visual", key="btn_card_pupi", use_container_width=True):
                    st.session_state['juego_actual'] = 'pupiletras'
                    st.rerun()

            st.write("") 

            col3, col4 = st.columns(2, gap="large")
            
            with col3:
                # ROBOT
                if st.button("🤖 ROBOT\n\nLógica & Deducción", key="btn_card_robot", use_container_width=True):
                    st.session_state['juego_actual'] = 'ahorcado'
                    st.rerun()

            with col4:
                # CAMBIO: DE PIXEL ART A SORTEADOR
                st.markdown('<div class="card-icon" style="text-align: center; margin-bottom: -55px; position: relative; z-index: 5; pointer-events: none; font-size: 40px;">🎰</div>', unsafe_allow_html=True)
                # Nota: Cambiamos la key para limpiar el estado anterior
                if st.button("\n\nSorteador\n\nElegir participantes", key="btn_sorteo_v1", use_container_width=True):
                    st.session_state['juego_actual'] = 'sorteador' # Nueva ID interna
                    st.rerun()

        # ==========================================
        # === C. ROUTER (EL CEREBRO QUE DECIDE QUÉ MOSTRAR) ===
        # ==========================================
        
        # 1. SI NO HAY JUEGO SELECCIONADO -> MOSTRAR MENÚ
        if st.session_state['juego_actual'] is None:
            mostrar_menu_juegos()

        # 2. JUEGO TRIVIA (CORREGIDO: ERROR DE TIEMPO SOLUCIONADO)
        elif st.session_state['juego_actual'] == 'trivia':
            
            # Barra superior de retorno
            col_back, col_title = st.columns([1, 5])
            with col_back:
                if st.button("🔙 Menú", use_container_width=True): 
                    volver_menu_juegos()
            with col_title:
                st.subheader("Desafío Trivia")

            # --- CSS TRIVIA ---
            st.markdown("""
                <style>
                div.stButton > button[kind="primary"] {
                    background-color: #28a745 !important;
                    border-color: #28a745 !important;
                    color: white !important;
                    font-size: 24px !important;
                    font-weight: bold !important;
                    padding: 15px 30px !important;
                }
                .big-question {
                    font-size: 50px !important;
                    font-weight: 800;
                    color: #1e3a8a;
                    text-align: center;
                    background-color: #eff6ff;
                    padding: 40px;
                    border-radius: 25px;
                    border: 5px solid #3b82f6;
                    margin-bottom: 30px;
                    box-shadow: 0 6px 15px rgba(0,0,0,0.15);
                    line-height: 1.2;
                }
                section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] div.stButton > button:not([kind="primary"]) {
                    background-color: #fff9c4 !important;
                    border: 3px solid #fbc02d !important;
                    border-radius: 20px !important;
                    min-height: 120px !important;
                    height: auto !important;
                    white-space: normal !important;
                    padding: 15px !important;
                    margin-bottom: 15px !important;
                    box-shadow: 0 6px 0 #f9a825 !important;
                }
                section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] div.stButton > button:not([kind="primary"]) p {
                    font-size: 36px !important;
                    font-weight: 800 !important;
                    color: #333333 !important;
                    line-height: 1.1 !important;
                }
                section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] div.stButton > button:not([kind="primary"]):hover {
                    background-color: #fff59d !important;
                    transform: translateY(-3px);
                    border-color: #f57f17 !important;
                }
                </style>
            """, unsafe_allow_html=True)

            # --- MODO CINE ---
            col_header1, col_header2 = st.columns([3, 1])
            with col_header1:
                st.markdown("Genera un juego de preguntas interactivo.")
            with col_header2:
                modo_cine = st.checkbox("📺 Modo Cine", help="Oculta la barra lateral.")
            
            if modo_cine:
                st.markdown("""<style>[data-testid="stSidebar"], header, footer {display: none;}</style>""", unsafe_allow_html=True)

            # --- LÓGICA TRIVIA ---
            if 'juego_iniciado' not in st.session_state or not st.session_state['juego_iniciado']:
                col_game1, col_game2 = st.columns([2, 1])
                with col_game1:
                    tema_input = st.text_input("Tema:", placeholder="Ej: La Célula...")
                    lista_grados = ["1° Primaria", "2° Primaria", "3° Primaria", "4° Primaria", "5° Primaria", "6° Primaria", "1° Secundaria", "2° Secundaria", "3° Secundaria", "4° Secundaria", "5° Secundaria"]
                    grado_input = st.selectbox("Grado:", lista_grados, index=6)
                with col_game2:
                    num_input = st.slider("Preguntas:", 1, 10, 5)
                    modo_avance = st.radio("Modo de Juego:", ["Automático (Rápido)", "Guiado por Docente (Pausa)"])

                # BOTÓN GENERAR CON SISTEMA DE "AUTO-REPARACIÓN" (3 VIDAS)
                if st.button("🎲 Generar Juego", type="primary", use_container_width=True):
                    if not tema_input:
                        st.warning("⚠️ Escribe un tema.")
                    else:
                        # Variables de control de reintentos
                        intentos = 0
                        max_intentos = 3
                        exito = False
                        
                        # Espacio para mensajes temporales
                        placeholder_estado = st.empty()
                        
                        # Bucle de intentos (La magia de la resiliencia)
                        while intentos < max_intentos and not exito:
                            intentos += 1
                            try:
                                msg_intento = f"🧠 Creando desafíos..." if intentos == 1 else f"⚠️ Ajustando formato (Intento {intentos}/{max_intentos})..."
                                
                                with st.spinner(msg_intento):
                                    # 1. Llamada a la IA
                                    respuesta_json = pedagogical_assistant.generar_trivia_juego(tema_input, grado_input, "General", num_input)
                                    
                                    if respuesta_json:
                                        # 2. Limpieza agresiva del JSON
                                        clean_json = respuesta_json.replace('```json', '').replace('```', '').strip()
                                        
                                        # 3. Intento de conversión (Aquí es donde suele fallar)
                                        preguntas = json.loads(clean_json)
                                        
                                        # 4. Si pasa la línea anterior, ¡ÉXITO! Guardamos todo.
                                        st.session_state['juego_preguntas'] = preguntas
                                        st.session_state['juego_indice'] = 0
                                        st.session_state['juego_puntaje'] = 0
                                        st.session_state['juego_terminado'] = False
                                        st.session_state['tema_actual'] = tema_input
                                        st.session_state['modo_avance'] = "auto" if "Automático" in modo_avance else "guiado"
                                        st.session_state['fase_pregunta'] = "respondiendo"
                                        
                                        st.session_state['juego_en_lobby'] = True 
                                        st.session_state['juego_iniciado'] = True
                                        
                                        exito = True # Rompemos el bucle
                                        st.rerun()
                                    else:
                                        raise Exception("Respuesta vacía de la IA")

                            except json.JSONDecodeError:
                                # ¡Ajá! Aquí capturamos el error de la coma (Expecting , delimiter)
                                import time
                                time.sleep(1) # Esperamos un segundo para no saturar
                                continue # Volvemos a empezar el bucle while
                                
                            except Exception as e:
                                st.error(f"Error inesperado: {e}")
                                break # Si es otro error, paramos
                        
                        # Si después de 3 intentos sigue fallando...
                        if not exito:
                            st.error("❌ La IA está teniendo dificultades con este tema específico. Por favor, intenta cambiar ligeramente el nombre del tema.")
                st.divider()

            elif st.session_state.get('juego_en_lobby', False):
                tema_mostrar = st.session_state.get('tema_actual', 'Trivia')
                modo_mostrar = "Modo Automático" if st.session_state.get('modo_avance') == "auto" else "Modo Guiado (Pausa)"
                
                st.markdown(f"""
                <div style="text-align: center; padding: 40px; background-color: white; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <h1 style="font-size: 70px; color: #28a745; margin: 0;">🏆 TRIVIA TIME 🏆</h1>
                    <h2 style="color: #555; font-size: 30px; margin-top: 10px;">Tema: {tema_mostrar}</h2>
                    <p style="color: #888; font-weight: bold; font-size: 20px;">{modo_mostrar}</p>
                    <br>
                </div>
                """, unsafe_allow_html=True)
                st.write("") 
                col_spacer1, col_btn, col_spacer2 = st.columns([1, 2, 1])
                with col_btn:
                    if st.button("🚀 EMPEZAR AHORA", type="primary", use_container_width=True):
                        st.session_state['juego_en_lobby'] = False
                        st.rerun()

            elif not st.session_state.get('juego_terminado', False):
                idx = st.session_state['juego_indice']
                preguntas = st.session_state['juego_preguntas']
                current_score = int(st.session_state['juego_puntaje'])
                modo = st.session_state.get('modo_avance', 'auto')
                fase = st.session_state.get('fase_pregunta', 'respondiendo')

                if idx >= len(preguntas):
                    st.session_state['juego_terminado'] = True
                    st.rerun()

                pregunta_actual = preguntas[idx]
                
                col_info1, col_info2 = st.columns([3, 1])
                with col_info1:
                    st.caption(f"Pregunta {idx + 1} de {len(preguntas)}")
                    st.progress((idx + 1) / len(preguntas))
                with col_info2:
                    st.markdown(f"""<div style="text-align: right;"><span style="font-size: 45px; font-weight: 900; color: #28a745; background: #e6fffa; padding: 5px 20px; border-radius: 15px; border: 2px solid #28a745;">{current_score}</span></div>""", unsafe_allow_html=True)
                
                st.write("") 
                st.markdown(f"""<div class="big-question">{pregunta_actual['pregunta']}</div>""", unsafe_allow_html=True)
                
                if fase == 'respondiendo':
                    opciones = pregunta_actual['opciones']
                    col_opt1, col_opt2 = st.columns(2)
                    
                    # --- AQUÍ ESTABA EL ERROR ---
                    def responder(opcion_elegida):
                        import time # <--- ¡AGREGADO! Soluciona el error NameError
                        
                        correcta = pregunta_actual['respuesta_correcta']
                        puntos_por_pregunta = 100 / len(preguntas)
                        es_correcta = (opcion_elegida == correcta)
                        
                        if es_correcta:
                            st.session_state['juego_puntaje'] += puntos_por_pregunta
                            st.session_state['ultimo_feedback'] = f"correcta|{int(puntos_por_pregunta)}"
                        else:
                            st.session_state['ultimo_feedback'] = f"incorrecta|{correcta}"

                        if modo == 'auto':
                            feedback_container = st.empty()
                            if es_correcta:
                                feedback_container.markdown(f"""<div style="background-color: #d1e7dd; color: #0f5132; padding: 20px; border-radius: 10px; text-align: center; font-size: 30px; font-weight: bold;">🎉 ¡CORRECTO!</div>""", unsafe_allow_html=True)
                            else:
                                feedback_container.markdown(f"""<div style="background-color: #f8d7da; color: #842029; padding: 20px; border-radius: 10px; text-align: center; font-size: 30px; font-weight: bold;">❌ INCORRECTO. Era: {correcta}</div>""", unsafe_allow_html=True)
                            
                            time.sleep(2.0) # Ahora sí funcionará
                            
                            if st.session_state['juego_indice'] < len(preguntas) - 1:
                                st.session_state['juego_indice'] += 1
                            else:
                                st.session_state['juego_terminado'] = True
                            st.rerun()
                        else:
                            st.session_state['fase_pregunta'] = 'feedback'
                            st.rerun()

                    with col_opt1:
                        if st.button(f"A) {opciones[0]}", use_container_width=True, key=f"btn_a_{idx}"): responder(opciones[0])
                        if st.button(f"C) {opciones[2]}", use_container_width=True, key=f"btn_c_{idx}"): responder(opciones[2])
                    with col_opt2:
                        if st.button(f"B) {opciones[1]}", use_container_width=True, key=f"btn_b_{idx}"): responder(opciones[1])
                        if st.button(f"D) {opciones[3]}", use_container_width=True, key=f"btn_d_{idx}"): responder(opciones[3])
                
                elif fase == 'feedback':
                    tipo, valor = st.session_state['ultimo_feedback'].split("|")
                    if tipo == "correcta":
                        st.markdown(f"""<div style="background-color: #d1e7dd; color: #0f5132; padding: 40px; border-radius: 20px; text-align: center; font-size: 40px; font-weight: bold; border: 4px solid #badbcc; margin-bottom: 20px;">🎉 ¡CORRECTO! <br> <span style="font-size: 30px">Has ganado +{valor} puntos</span></div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<div style="background-color: #f8d7da; color: #842029; padding: 40px; border-radius: 20px; text-align: center; font-size: 40px; font-weight: bold; border: 4px solid #f5c2c7; margin-bottom: 20px;">❌ INCORRECTO <br> <span style="font-size: 30px; color: #333;">La respuesta era: {valor}</span></div>""", unsafe_allow_html=True)
                    
                    col_next1, col_next2, col_next3 = st.columns([1, 2, 1])
                    with col_next2:
                        if st.button("➡️ SIGUIENTE PREGUNTA", type="primary", use_container_width=True):
                            if st.session_state['juego_indice'] < len(preguntas) - 1:
                                st.session_state['juego_indice'] += 1
                                st.session_state['fase_pregunta'] = 'respondiendo'
                            else:
                                st.session_state['juego_terminado'] = True
                            st.rerun()

            elif st.session_state.get('juego_terminado', False):
                puntaje = int(st.session_state['juego_puntaje'])
                st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #2c3e50;'>PUNTAJE FINAL: {puntaje}</h1>", unsafe_allow_html=True)
                col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])
                with col_center:
                    if puntaje == 100:
                        st.balloons()
                        st.markdown("""<div style="text-align: center; font-size: 120px;">🏆</div>""", unsafe_allow_html=True)
                        st.success("¡MAESTRO TOTAL! 🌟")
                    elif puntaje >= 60:
                        st.snow()
                        st.markdown("""<div style="text-align: center; font-size: 120px;">😎</div>""", unsafe_allow_html=True)
                        st.info("¡Bien hecho! Aprobado.")
                    else:
                        st.markdown("""<div style="text-align: center; font-size: 120px;">📚</div>""", unsafe_allow_html=True)
                        st.warning("¡Buen intento! A repasar un poco más.")

                    if st.button("🔄 Nuevo Juego", type="primary", use_container_width=True):
                        st.session_state['juego_iniciado'] = False 
                        del st.session_state['juego_preguntas']
                        del st.session_state['juego_terminado']
                        st.rerun()

        # 3. JUEGO PUPILETRAS
        elif st.session_state['juego_actual'] == 'pupiletras':
            
            # --- BARRA SUPERIOR ---
            col_back, col_title = st.columns([1, 5])
            with col_back:
                if st.button("🔙 Menú", use_container_width=True, key="pupi_back"):
                    volver_menu_juegos()
            with col_title:
                st.subheader("🔎 Pupiletras: Buscador de Palabras")

            # --- CONFIGURACIÓN ---
            if 'pupi_grid' not in st.session_state:
                st.info("Configura tu sopa de letras:")
                
                col_conf1, col_conf2, col_conf3 = st.columns([2, 1, 1])
                with col_conf1:
                    tema_pupi = st.text_input("Tema:", placeholder="Ej: Héroes del Perú...")
                with col_conf2:
                    lista_grados_pupi = [
                        "1° Primaria", "2° Primaria", "3° Primaria", "4° Primaria", "5° Primaria", "6° Primaria",
                        "1° Secundaria", "2° Secundaria", "3° Secundaria", "4° Secundaria", "5° Secundaria"
                    ]
                    grado_pupi = st.selectbox("Grado:", lista_grados_pupi, index=5)
                with col_conf3:
                    cant_palabras = st.slider("Palabras:", 5, 12, 8) 

                if st.button("🧩 Generar Sopa de Letras", type="primary", use_container_width=True):
                    if not tema_pupi:
                        st.warning("⚠️ Escribe un tema.")
                    else:
                        with st.spinner("🤖 Diseñando ficha y juego interactivo..."):
                            # A) IA genera palabras
                            palabras = pedagogical_assistant.generar_palabras_pupiletras(tema_pupi, grado_pupi, cant_palabras)
                            
                            if palabras and len(palabras) > 0:
                                # B) Algoritmo crea la matriz
                                grid, colocados = pedagogical_assistant.crear_grid_pupiletras(palabras)
                                
                                # C) Generamos el Word
                                docx_buffer = pedagogical_assistant.generar_docx_pupiletras(grid, colocados, tema_pupi, grado_pupi)
                                
                                # Guardamos todo
                                st.session_state['pupi_grid'] = grid
                                st.session_state['pupi_data'] = colocados
                                st.session_state['pupi_found'] = set()
                                st.session_state['pupi_docx_bytes'] = docx_buffer.getvalue()
                                st.rerun()
                            else:
                                st.error("Error: La IA no pudo generar palabras. Intenta otro tema.")

            # --- ZONA DE JUEGO ---
            else:
                grid = st.session_state['pupi_grid']
                palabras_data = st.session_state['pupi_data']
                encontradas = st.session_state['pupi_found']

                col_tablero, col_panel = st.columns([3, 1])

                with col_tablero:
                    st.markdown("##### 📍 Tablero Interactivo")
                    
                    celdas_iluminadas = set()
                    for p_data in palabras_data:
                        if p_data['palabra'] in encontradas:
                            for coord in p_data['coords']:
                                celdas_iluminadas.add(coord)

                    html_grid = '<div style="display: flex; justify-content: center; overflow-x: auto;"><table style="border-collapse: collapse; margin: auto;">'
                    for r in range(len(grid)):
                        html_grid += "<tr>"
                        for c in range(len(grid[0])):
                            letra = grid[r][c]
                            bg = "#ffffff"
                            color = "#333"
                            border = "1px solid #ccc"
                            weight = "normal"
                            
                            if (r, c) in celdas_iluminadas:
                                bg = "#ffeb3b"
                                color = "#000"
                                border = "2px solid #fbc02d"
                                weight = "bold"
                            
                            html_grid += f'<td style="width: 45px; height: 45px; text-align: center; vertical-align: middle; font-family: monospace; font-size: 28px; font-weight: {weight}; background-color: {bg}; color: {color}; border: {border}; cursor: default;">{letra}</td>'
                        html_grid += "</tr>"
                    html_grid += "</table></div>"
                    
                    st.markdown(html_grid, unsafe_allow_html=True)

                with col_panel:
                    st.success("📄 Ficha Lista")
                    st.download_button(
                        label="📥 Descargar Word",
                        data=st.session_state['pupi_docx_bytes'],
                        file_name="Pupiletras_Clase.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                    
                    st.divider()
                    st.markdown("##### 📝 Encontrar:")
                    
                    progreso = len(encontradas) / len(palabras_data)
                    st.progress(progreso, text=f"{len(encontradas)} de {len(palabras_data)}")
                    
                    for i, p_item in enumerate(palabras_data):
                        palabra_texto = p_item['palabra']
                        if palabra_texto in encontradas:
                            label = f"✅ {palabra_texto}"
                            tipo = "primary"
                        else:
                            label = f"⬜ {palabra_texto}"
                            tipo = "secondary"
                        
                        if st.button(label, key=f"btn_pupi_{i}", type=tipo, use_container_width=True):
                            if palabra_texto in encontradas:
                                st.session_state['pupi_found'].remove(palabra_texto)
                            else:
                                st.session_state['pupi_found'].add(palabra_texto)
                            st.rerun()

                    st.write("")
                    if st.button("🔄 Reiniciar", type="secondary", use_container_width=True):
                        del st.session_state['pupi_grid']
                        st.rerun()

        # 4. JUEGO ROBOT (AHORCADO - VERSIÓN HÍBRIDA: CONFIGURACIÓN ORIGINAL + MEJORAS)
        elif st.session_state['juego_actual'] == 'ahorcado':
            
            # --- BARRA SUPERIOR ---
            col_back, col_title = st.columns([1, 5])
            with col_back:
                if st.button("🔙 Menú", use_container_width=True, key="robot_btn_back_top"):
                    keys_to_clear = ['robot_challenges', 'robot_level', 'robot_word']
                    for k in keys_to_clear:
                        if k in st.session_state: del st.session_state[k]
                    volver_menu_juegos()
            with col_title:
                st.subheader("🔋 Recarga al Robot: Misión en Cadena")

            # --- CSS ARCADE (MEJORADO PARA LETRAS GIGANTES) ---
            st.markdown("""
                <style>
                /* Botón del Teclado */
                section[data-testid="stMain"] div.stButton > button {
                    width: 100%;
                    height: 85px !important; /* Más alto para la letra gigante */
                    background-color: white !important;
                    border: 3px solid #1E88E5 !important; /* Borde Azul Fuerte */
                    border-radius: 15px !important;
                    margin-bottom: 10px !important;
                    padding: 0px !important;
                    box-shadow: 0 5px 0 #1565C0 !important; /* Sombra 3D */
                }
                
                /* FUERZA BRUTA PARA EL TEXTO (LETRA) */
                section[data-testid="stMain"] div.stButton > button p {
                    font-size: 45px !important; /* <--- AQUÍ ESTÁ EL CAMBIO (ANTES 36px) */
                    font-weight: 900 !important;
                    color: #0D47A1 !important; /* Azul Oscuro */
                    line-height: 1 !important;
                }

                /* Hover */
                section[data-testid="stMain"] div.stButton > button:hover:enabled {
                    transform: translateY(-2px);
                    background-color: #E3F2FD !important;
                }
                
                /* Click */
                section[data-testid="stMain"] div.stButton > button:active:enabled {
                    transform: translateY(4px);
                    box-shadow: none !important;
                }

                /* Botones de Navegación (Start, Next) - Texto Normal */
                div.stButton > button[kind="primary"] p { 
                    color: white !important; 
                    font-size: 20px !important; 
                }
                div.stButton > button[kind="primary"] {
                    background-color: #FF5722 !important;
                    border-color: #E64A19 !important;
                }
                
                /* Botones Deshabilitados (Letras usadas) */
                section[data-testid="stMain"] div.stButton > button:disabled {
                    background-color: #CFD8DC !important;
                    border-color: #B0BEC5 !important;
                    opacity: 0.6 !important;
                    box-shadow: none !important;
                    transform: translateY(4px);
                }
                
                /* ANTÍDOTO (Para no romper el menú de arriba) */
                section[data-testid="stMain"] [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"]:first-child div.stButton > button {
                    height: auto !important;
                    box-shadow: none !important;
                    border: 1px solid rgba(49, 51, 63, 0.2) !important;
                }
                section[data-testid="stMain"] [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"]:first-child div.stButton > button p {
                    font-size: 16px !important;
                    color: inherit !important;
                }
                </style>
            """, unsafe_allow_html=True)

            # --- CONFIGURACIÓN (MANTENIENDO TU ESTRUCTURA DE 3 COLUMNAS) ---
            if 'robot_challenges' not in st.session_state:
                st.info("Configura la misión de rescate:")
                
                col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
                with col_c1:
                    tema_robot = st.text_input("Tema del Reto:", placeholder="Ej: Sistema Solar, Verbos...")
                with col_c2:
                    lista_grados_robot = [
                        "1° Primaria", "2° Primaria", "3° Primaria", "4° Primaria", "5° Primaria", "6° Primaria",
                        "1° Secundaria", "2° Secundaria", "3° Secundaria", "4° Secundaria", "5° Secundaria"
                    ]
                    grado_robot = st.selectbox("Grado:", lista_grados_robot, index=5)
                with col_c3:
                    cant_robot = st.slider("Palabras:", 3, 10, 5)
                
                if st.button("🤖 Iniciar Misión", type="primary", use_container_width=True):
                    if not tema_robot:
                        st.warning("⚠️ Escribe un tema.")
                    else:
                        with st.spinner(f"⚡ Generando {cant_robot} niveles de seguridad..."):
                            retos = pedagogical_assistant.generar_reto_ahorcado(tema_robot, grado_robot, cant_robot)
                            if retos and len(retos) > 0:
                                st.session_state['robot_challenges'] = retos
                                st.session_state['robot_level'] = 0
                                st.session_state['robot_score'] = 0
                                st.session_state['robot_errors'] = 0
                                st.session_state['robot_max_errors'] = 6
                                
                                primer_reto = retos[0]
                                st.session_state['robot_word'] = primer_reto['palabra'].upper()
                                st.session_state['robot_hint'] = primer_reto['pista']
                                st.session_state['robot_guesses'] = set()
                                st.rerun()
                            else:
                                st.error("Error conectando con el servidor central (IA). Intenta de nuevo.")

            # --- ZONA DE JUEGO ---
            else:
                import time # Importamos time para los efectos
                alerta_placeholder = st.empty()
                contenedor_audio = st.empty() # Para sonido

                nivel_idx = st.session_state['robot_level']
                total_niveles = len(st.session_state['robot_challenges'])
                palabra = st.session_state['robot_word']
                errores = st.session_state['robot_errors']
                max_errores = st.session_state['robot_max_errors']
                letras_adivinadas = st.session_state['robot_guesses']
                
                # A) MONITOR
                progreso_mision = (nivel_idx) / total_niveles
                st.progress(progreso_mision, text=f"Nivel {nivel_idx + 1} de {total_niveles} | Puntaje: {st.session_state['robot_score']}")

                baterias_restantes = max_errores - errores
                emoji_bateria = "🔋" * baterias_restantes + "🪫" * errores
                
                col_hint, col_bat = st.columns([3, 1])
                with col_hint:
                    # Pista Grande
                    st.markdown(f"""
                    <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 6px solid #2196F3;">
                        <h3 style="margin:0; color: #0D47A1; font-size: 28px;">💡 {st.session_state['robot_hint']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                with col_bat:
                    st.markdown(f"<div style='font-size: 45px; text-align: right;'>{emoji_bateria}</div>", unsafe_allow_html=True)

                # B) PALABRA
                palabra_mostrar = ""
                ganado = True
                for letra in palabra:
                    if letra in letras_adivinadas:
                        palabra_mostrar += letra + " "
                    else:
                        palabra_mostrar += "_ "
                        ganado = False
                
                st.markdown(f"""
                <h1 style="text-align: center; font-size: 85px; font-family: monospace; color: #333; font-weight: 900; margin: 30px 0; letter-spacing: 10px;">
                    {palabra_mostrar}
                </h1>
                """, unsafe_allow_html=True)

                # C) CONTROL
                if ganado:
                    st.success(f"🎉 ¡CORRECTO! La palabra era: **{palabra}**")
                    if nivel_idx < total_niveles - 1:
                        if st.button("➡️ Siguiente Nivel", type="primary", use_container_width=True):
                            st.session_state['robot_score'] += 100
                            st.session_state['robot_level'] += 1
                            siguiente_reto = st.session_state['robot_challenges'][st.session_state['robot_level']]
                            st.session_state['robot_word'] = siguiente_reto['palabra'].upper()
                            st.session_state['robot_hint'] = siguiente_reto['pista']
                            st.session_state['robot_guesses'] = set()
                            # ⚠️ CORRECCIÓN APLICADA: NO REINICIAMOS ERRORES AQUÍ
                            # st.session_state['robot_errors'] = 0 <--- ELIMINADO
                            st.rerun()
                    else:
                        st.balloons()
                        st.markdown("""<div style="text-align: center; padding: 20px; background-color: #d4edda; border-radius: 20px;"><h1>🏆 ¡MISIÓN COMPLETADA!</h1></div>""", unsafe_allow_html=True)
                        if st.button("🔄 Nueva Misión", type="primary"):
                            del st.session_state['robot_challenges']
                            st.rerun()
                        
                elif errores >= max_errores:
                    st.error(f"💀 BATERÍA AGOTADA. La palabra era: **{palabra}**")
                    if st.button("⚡ Reintentar Nivel", type="secondary", use_container_width=True):
                        st.session_state['robot_guesses'] = set()
                        st.session_state['robot_errors'] = 0 # Aquí SÍ reseteamos porque murió
                        st.rerun()
                        
                else:
                    # D) TECLADO ARCADE
                    st.write("")
                    letras_teclado = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
                    cols = st.columns(9)
                    
                    for i, letra in enumerate(letras_teclado):
                        desactivado = letra in letras_adivinadas
                        type_btn = "secondary"
                        if desactivado and letra in palabra: 
                            type_btn = "primary"
                            
                        if cols[i % 9].button(letra, key=f"key_{letra}", disabled=desactivado, type=type_btn, use_container_width=True):
                            st.session_state['robot_guesses'].add(letra)
                            
                            # Lógica de Audio y Error
                            if letra in palabra:
                                # ACIERTO
                                t_stamp = time.time()
                                contenedor_audio.markdown(f"""<audio autoplay style="display:none;"><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3?t={t_stamp}"></audio>""", unsafe_allow_html=True)
                                time.sleep(0.2)
                            else:
                                # ERROR
                                st.session_state['robot_errors'] += 1
                                t_stamp = time.time()
                                contenedor_audio.markdown(f"""<audio autoplay style="display:none;"><source src="https://www.soundjay.com/buttons/sounds/button-10.mp3?t={t_stamp}"></audio>""", unsafe_allow_html=True)
                                alerta_placeholder.markdown("""
                                    <div style="background-color: #ffebee; border: 3px solid #ef5350; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                                        <h2 style="color: #b71c1c; margin:0; font-size: 30px;">💥 ¡CORTOCIRCUITO!</h2>
                                    </div>
                                """, unsafe_allow_html=True)
                                time.sleep(1.0)
                            
                            st.rerun()
                        
        # 5. JUEGO SORTEADOR (ETAPA 2: CARGA DE DATOS)
        elif st.session_state['juego_actual'] == 'sorteador':
            
            # --- BARRA SUPERIOR ---
            col_back, col_title = st.columns([1, 5])
            with col_back:
                if st.button("🔙 Menú", use_container_width=True, key="sorteo_back"): 
                    # Limpiamos variables al salir
                    if 'sorteo_lista' in st.session_state: del st.session_state['sorteo_lista']
                    volver_menu_juegos()
            with col_title:
                st.subheader("🎰 Sorteador Digital")

            # --- ESTADO INICIAL DEL SORTEO ---
            if 'sorteo_lista' not in st.session_state:
                st.session_state['sorteo_lista'] = [] # Lista vacía al inicio

            # Si la lista está vacía, mostramos la CONFIGURACIÓN
            if not st.session_state['sorteo_lista']:
                st.markdown("##### 1️⃣ Paso 1: Carga los participantes")
                
                # Usamos Pestañas para organizar las opciones
                tab_manual, tab_excel = st.tabs(["📝 Escribir Lista", "📂 Subir Excel"])
                
                lista_temporal = []

                # OPCIÓN A: MANUAL
                with tab_manual:
                    texto_input = st.text_area("Pega o escribe los nombres (uno por línea):", height=150, placeholder="Juan Perez\nMaria Lopez\nCarlos...")
                    if texto_input:
                        lista_temporal = [nombre.strip() for nombre in texto_input.split('\n') if nombre.strip()]

                # OPCIÓN B: EXCEL
                with tab_excel:
                    uploaded_file = st.file_uploader("Sube tu lista (Excel .xlsx)", type=['xlsx'])
                    if uploaded_file is not None:
                        try:
                            import pandas as pd
                            df = pd.read_excel(uploaded_file)
                            # Intentamos adivinar la columna de nombres (la primera que sea texto)
                            col_nombres = df.columns[0] # Por defecto la primera
                            lista_temporal = df[col_nombres].dropna().astype(str).tolist()
                            st.success(f"✅ Se encontraron {len(lista_temporal)} nombres en la columna '{col_nombres}'")
                        except Exception as e:
                            st.error(f"Error al leer el archivo: {e}")

                st.write("")
                st.markdown("##### 2️⃣ Paso 2: Configura el Sorteo")
                
                c1, c2 = st.columns([2, 1])
                with c1:
                    # Si hay datos cargados temporalmente, ajustamos el slider
                    max_val = len(lista_temporal) if lista_temporal else 10
                    cant_ganadores = st.slider("¿Cuántos estudiantes necesitas?", 1, max_val, 1)
                
                with c2:
                    st.write("") # Espacio para alinear botón
                    if st.button("💾 GUARDAR Y CONTINUAR", type="primary", use_container_width=True):
                        if len(lista_temporal) > 0:
                            if cant_ganadores > len(lista_temporal):
                                st.error("¡Pides más ganadores que participantes!")
                            else:
                                st.session_state['sorteo_lista'] = lista_temporal
                                st.session_state['sorteo_cantidad'] = cant_ganadores
                                st.session_state['sorteo_ganadores'] = [] # Aquí guardaremos los que salgan
                                st.rerun()
                        else:
                            st.warning("⚠️ La lista está vacía. Escribe nombres o sube un Excel.")

            # --- ZONA DE JUEGO (ETAPA FINAL - GANADOR GIGANTE 🎰) ---
            else:
                total_participantes = len(st.session_state['sorteo_lista'])
                total_ganadores = st.session_state.get('sorteo_cantidad', 1)
                
                # Diseño Cabecera Casino
                st.markdown(f"""
                <div style="background-color: #111; padding: 15px; border-radius: 10px; border: 2px solid #FFD700; text-align: center; margin-bottom: 20px; box-shadow: 0 0 15px rgba(255, 215, 0, 0.3);">
                    <p style="color: #FFD700; font-family: monospace; font-size: 18px; margin: 0;">🎰 CASINO AULAMETRICS 🎰</p>
                    <p style="color: #FFF; margin: 0;">Participantes: <b>{total_participantes}</b> | Premios: <b>{total_ganadores}</b></p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🎲 GIRAR LA SUERTE", type="primary", use_container_width=True):
                    
                    import random
                    import time
                    
                    lista_candidatos = st.session_state['sorteo_lista'].copy()
                    ganadores_ronda = []
                    
                    # Contenedores vacíos
                    contenedor_audio_giro = st.empty()
                    contenedor_animacion = st.empty()
                    contenedor_audio_win = st.empty()
                    
                    # 1. ACTIVAR SONIDO MECÁNICO (Latido)
                    t_stamp = time.time()
                    audio_html_giro = f"""
                        <audio autoplay loop>
                        <source src="https://cdn.pixabay.com/audio/2022/03/10/audio_c8c8a73467.mp3?t={t_stamp}" type="audio/mp3">
                        </audio>
                    """
                    contenedor_audio_giro.markdown(audio_html_giro, unsafe_allow_html=True)
                    
                    # Pausa técnica para carga de audio
                    time.sleep(0.5) 
                    
                    # Bucle de ganadores
                    for i in range(total_ganadores):
                        
                        # A) ANIMACIÓN VISUAL (Giro)
                        velocidad = 0.05
                        ciclos = 25 
                        
                        for paso in range(ciclos): 
                            nombre_random = random.choice(lista_candidatos)
                            
                            color_texto = "#FFF"
                            if paso % 2 == 0: color_texto = "#FFD700"
                            
                            contenedor_animacion.markdown(f"""
                            <div style="
                                text-align: center; padding: 40px; 
                                background: linear-gradient(180deg, #000 0%, #333 50%, #000 100%); 
                                border: 5px solid #FFD700; border-radius: 15px; 
                                box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
                                font-family: 'Courier New', monospace; overflow: hidden;
                            ">
                                <h3 style="color: #555; margin:0; font-size: 20px;">🎰 GIRANDO...</h3>
                                <h1 style="color: {color_texto}; font-size: 55px; margin: 10px 0; text-shadow: 0 0 10px {color_texto};">
                                    {nombre_random}
                                </h1>
                                <div style="height: 5px; background: #FFD700; width: 100%; margin-top: 20px; box-shadow: 0 0 10px #FFD700;"></div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if paso > ciclos - 8: velocidad += 0.04 
                            time.sleep(velocidad)
                        
                        # B) ELEGIR GANADOR
                        if lista_candidatos:
                            ganador = random.choice(lista_candidatos)
                            lista_candidatos.remove(ganador)
                            ganadores_ronda.append(ganador)
                            
                            # 2. SONIDO VICTORIA (Ding!)
                            t_stamp_win = time.time()
                            audio_html_win = f"""
                                <audio autoplay>
                                <source src="https://cdn.pixabay.com/audio/2021/08/04/audio_0625c1539c.mp3?t={t_stamp_win}" type="audio/mp3">
                                </audio>
                            """
                            contenedor_audio_win.markdown(audio_html_win, unsafe_allow_html=True)
                            
                            # Pausar el ruido mecánico
                            contenedor_audio_giro.empty() 
                            
                            # C) PANTALLA GANADOR (TAMAÑO JUMBO)
                            # Cambios aquí: padding reducido, font-size aumentado a 90px
                            contenedor_animacion.markdown(f"""
                            <div style="
                                text-align: center; padding: 20px; 
                                background: radial-gradient(circle, rgba(255,215,0,1) 0%, rgba(255,140,0,1) 100%); 
                                border: 5px solid #FFF; border-radius: 15px; 
                                box-shadow: 0 0 60px #FF8C00; animation: pulse 0.5s infinite;
                            ">
                                <h3 style="color: #FFF; margin:0; text-shadow: 1px 1px 2px black;">🏆 GANADOR #{i+1}</h3>
                                <h1 style="color: #FFF; font-size: 90px; margin: 5px 0; font-weight: 900; text-shadow: 4px 4px 0px #000; line-height: 1;">
                                    {ganador}
                                </h1>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.balloons()
                            time.sleep(4) 
                            
                            contenedor_audio_win.empty() 
                            
                            # Si faltan ganadores, reactivamos sonido mecánico
                            if i < total_ganadores - 1:
                                t_stamp_loop = time.time()
                                audio_html_loop = f"""
                                    <audio autoplay loop>
                                    <source src="https://cdn.pixabay.com/audio/2022/03/10/audio_c8c8a73467.mp3?t={t_stamp_loop}" type="audio/mp3">
                                    </audio>
                                """
                                contenedor_audio_giro.markdown(audio_html_loop, unsafe_allow_html=True)
                                time.sleep(0.5) 
                                
                        else:
                            st.warning("¡Se acabaron los participantes!")
                            break
                    
                    # D) LIMPIEZA FINAL
                    contenedor_audio_giro.empty()
                    contenedor_animacion.empty()
                    st.session_state['sorteo_ganadores'] = ganadores_ronda

                # --- RESULTADOS FINALES ---
                if 'sorteo_ganadores' in st.session_state and st.session_state['sorteo_ganadores']:
                    st.divider()
                    st.markdown("### 🌟 Ganadores Oficiales:")
                    
                    for idx, nombre in enumerate(st.session_state['sorteo_ganadores']):
                        st.markdown(f"""
                        <div style="
                            padding: 15px; margin-bottom: 10px; background: white; 
                            border-left: 10px solid #FFD700; border-radius: 10px; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                            display: flex; align-items: center; justify-content: space-between;
                        ">
                            <div style="display:flex; align-items:center;">
                                <div style="background:#FFD700; color:black; width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; margin-right:15px;">{idx + 1}</div>
                                <div style="font-size: 24px; font-weight: bold; color: #333;">{nombre}</div>
                            </div>
                            <div style="font-size: 24px;">🎉</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.write("")
                if st.button("🔄 Reiniciar Sorteo", type="secondary"):
                    del st.session_state['sorteo_lista']
                    if 'sorteo_ganadores' in st.session_state: del st.session_state['sorteo_ganadores']
                    st.rerun()
    
    
# =========================================================================
# === 7. EJECUCIÓN PRINCIPAL ===
# =========================================================================
query_params = st.query_params
auth_code = query_params.get("code")

if auth_code and not st.session_state.logged_in:
    try:
        session_data = supabase.auth.exchange_code_for_session(auth_code)
        if session_data.session:
            st.session_state.logged_in = True
            st.session_state.user = session_data.session.user
            st.session_state.show_welcome_message = True
            st.query_params.clear() 
            st.rerun()
    except Exception:
        st.query_params.clear() 
        pass 
    
if not st.session_state.logged_in:
    login_page()
else:
    home_page()


















