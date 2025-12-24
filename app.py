import json
import time
import random
from streamlit_lottie import st_lottie
import streamlit as st
import pandas as pd
import pedagogical_assistant
import io
import os
import base64
import modules.database as db
import modules.recursos as recursos
import modules.gamificacion as gamificacion
import modules.evaluacion as evaluacion
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
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    /* Títulos */
    h1, h2, h3 { 
        font-weight: 900 !important; 
        letter-spacing: -0.5px;
        color: #1A237E; 
    }
    
    /* Texto general */
    p, div, label, span { 
        font-weight: 400;
        font-size: 16px; 
    }

    /* =========================================
       B. LIMPIEZA DE INTERFAZ
    ========================================= */
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }
    [data-testid="stHeaderActionElements"] { display: none !important; }
    footer { visibility: hidden; }
    
    /* HEADER TRANSPARENTE GLOBAL */
    [data-testid="stHeader"] { 
        background-color: rgba(0,0,0,0) !important; 
        z-index: 999 !important; 
    }
    
    /* NOTA: Eliminamos la regla de color forzado aquí para evitar conflictos */
    
    .block-container {
        padding-top: 3rem !important; 
        padding-bottom: 0rem !important;
    }

    /* =========================================
       C. BARRA LATERAL GLOBAL (AZUL PROFUNDO)
    ========================================= */
    /* AHORA SÍ ESTÁ DENTRO DE LAS COMILLAS */
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
        font-weight: 500 !important; 
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
# === 1.C. PANTALLA DE INICIO (V11 - COMPACTA, MODERNA Y PROPORCIONAL) ===
# =========================================================================

def mostrar_home():
    
    # --- A. LÓGICA DE FECHA ---
    from datetime import datetime, timedelta
    ahora = datetime.now() - timedelta(hours=5)
    hora = ahora.hour
    
    if 5 <= hora < 12: saludo, emoji = "Buenos días", "☀️"
    elif 12 <= hora < 19: saludo, emoji = "Buenas tardes", "🌤️"
    else: saludo, emoji = "Buenas noches", "🌙"
        
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    fecha = f"{dias[ahora.weekday()]}, {ahora.day} de {meses[ahora.month - 1]}"

    # --- B. ESTILOS CSS (REESCALADOS PARA ENCAJAR) ---
    st.markdown("""
        <style>
        /* 1. FLECHA BLANCA */
        [data-testid="stHeader"] button, 
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            display: block !important;
            visibility: visible !important;
        }
        [data-testid="stHeader"] button svg,
        [data-testid="collapsedControl"] svg,
        [data-testid="stSidebarCollapsedControl"] svg {
            fill: #FFFFFF !important;
            stroke: #FFFFFF !important;
        }
        header[data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* 2. FONDO DEGRADADO */
        [data-testid="stAppViewContainer"] {
            background-color: #4A148C !important;
            background: 
                radial-gradient(circle at 10% 10%, rgba(255, 109, 0, 0.50) 0%, transparent 50%),
                radial-gradient(circle at 90% 90%, rgba(0, 229, 255, 0.30) 0%, transparent 50%),
                linear-gradient(135deg, #311B92 0%, #4A148C 100%) !important;
            background-attachment: fixed;
        }

        /* 3. TARJETAS DE CRISTAL (TAMAÑO COMPACTO) */
        section[data-testid="stMain"] div.stButton > button {
            width: 100%;
            /* REDUCCIÓN: De 320px a 200px para que quepan */
            min-height: 200px !important; 
            
            background: rgba(255, 255, 255, 0.08) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 20px !important;
            border-left: 6px solid #FFD600 !important;
            
            color: #FFFFFF !important;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 15px !important; /* Menos padding */
            transition: all 0.3s ease;
        }

        section[data-testid="stMain"] div.stButton > button:hover {
            transform: translateY(-5px) scale(1.01);
            background: rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 10px 30px rgba(255, 109, 0, 0.25);
            border-color: #FFFFFF !important;
        }

        /* 4. TEXTO PROPORCIONAL (MÁS PEQUEÑO PERO LEGIBLE) */
        section[data-testid="stMain"] div.stButton > button p {
            font-size: 20px !important; /* REDUCCIÓN: De 30px a 20px */
            font-weight: 800 !important;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-top: 10px !important;
            line-height: 1.1 !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        /* Ajuste márgenes */
        .block-container { padding-top: 2rem !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # --- C. ENCABEZADO (MÁS COMPACTO) ---
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 30px; padding-top: 10px;">
            <h1 style="color: #FFFFFF; font-size: 42px; margin-bottom: 0px; text-shadow: 0 0 20px rgba(255,109,0,0.6);">
                {emoji} {saludo}, Docente
            </h1>
            <p style="color: #FFD54F; font-size: 18px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase;">
                📅 {fecha}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # --- D. PARRILLA COMPACTA (ICONOS DE 80px) ---
    
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        # Tarjeta 1
        # REDUCCIÓN: Icono de 120px a 80px
        st.markdown("""
        <div style="pointer-events: none; text-align: center;">
            <img src="https://img.icons8.com/fluency/240/bullish.png" style="width: 80px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">
        </div>
        """, unsafe_allow_html=True)
        # REDUCCIÓN: Menos saltos de línea (\n) para reducir altura del botón
        if st.button("\n\n\nSISTEMA DE\nEVALUACIÓN", key="btn_eval", use_container_width=True):
            navegar_a("Sistema de Evaluación")
            st.rerun()

    with col2:
        # Tarjeta 2
        st.markdown("""
        <div style="pointer-events: none; text-align: center;">
            <img src="https://img.icons8.com/fluency/240/artificial-intelligence.png" style="width: 80px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">
        </div>
        """, unsafe_allow_html=True)
        if st.button("\n\n\nASISTENTE\nPEDAGÓGICO", key="btn_asist", use_container_width=True):
            navegar_a("Asistente Pedagógico")
            st.rerun()

    st.write("") # Espacio pequeño

    col3, col4 = st.columns(2, gap="medium")
    
    with col3:
        # Tarjeta 3
        st.markdown("""
        <div style="pointer-events: none; text-align: center;">
            <img src="https://img.icons8.com/fluency/240/folder-invoices.png" style="width: 80px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">
        </div>
        """, unsafe_allow_html=True)
        if st.button("\n\n\nBANCO DE\nRECURSOS", key="btn_rec", use_container_width=True):
            navegar_a("Recursos")
            st.rerun()

    with col4:
        # Tarjeta 4
        st.markdown("""
        <div style="pointer-events: none; text-align: center;">
            <img src="https://img.icons8.com/fluency/240/controller.png" style="width: 80px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">
        </div>
        """, unsafe_allow_html=True)
        if st.button("\n\n\nZONA DE\nGAMIFICACIÓN", key="btn_game", use_container_width=True):
            navegar_a("Gamificación")
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)

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
        
        /* 9. CORRECCIÓN OLVIDASTE CONTRASEÑA (NUEVAS REGLAS) */
        /* Texto del botón (st.button) a negro */
        div[data-testid="stVerticalBlock"] button[kind="secondary"] p {
            color: #1a1a1a !important;
            text-shadow: none !important;
        }
        
        /* 🚩 CORRECCIÓN CRÍTICA: Texto dentro del mensaje de st.info a negro. */
        /* Usamos selectores más específicos para anular el estilo global que lo ponía blanco. */
        div[data-testid="stNotification"] p,
        div[data-testid="stNotification"] div[data-testid="stMarkdownContainer"] p {
            color: #1a1a1a !important;
            text-shadow: none !important;
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

            # INICIO DE LA INSERCIÓN DEL NUEVO CÓDIGO
            # Botón y mensaje para "¿Olvidaste tu contraseña?"
            if st.button("¿Olvidaste tu contraseña?", key="forgot_pass_btn", help="Haz clic para ver las instrucciones de recuperación."):
                st.info("Para recuperar tu contraseña, por favor, ponte en contacto con el administrador escribiendo al siguiente correo electrónico: **aulametricsia@gmail.com**")
            # FIN DE LA INSERCIÓN DEL NUEVO CÓDIGO

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
            💬 ¿Dudas? Contáctanos/TikTok
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
        
        # [AÑADIENDO LA FECHA DE LANZAMIENTO AQUÍ]
        # Usamos st.info para destacarlo, o st.markdown para un estilo fuerte.
        st.markdown(
            "🚀 **Lanzamiento oficial de Aulametrics:** 01/03/2026", 
            help="Fecha de lanzamiento oficial de la nueva versión de AulaMetrics."
        )
        # También podrías usar: st.text("Fecha de lanzamiento de Aulametrics 01/03/2026")
        
        if st.session_state.get('pagina_actual') == 'Inicio':
            st.info("👋 Selecciona una herramienta del panel.")
        else:
            st.caption(f"📍 Sección: {st.session_state.get('pagina_actual')}")
        
        st.caption("🏫 AulaMetrics v2.0 Beta")


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

    # 1. SISTEMA DE EVALUACIÓN
    if pagina == "Sistema de Evaluación":
        evaluacion.evaluacion_page()

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

    # 4. RECURSOS (Llamando al nuevo módulo)
    elif pagina == "Recursos":
        recursos.recursos_page()

    # 5. GAMIFICACIÓN (Llamando al nuevo módulo)
    elif pagina == "Gamificación":
        gamificacion.gamificacion()


    
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







