import json
import time
import random
import os
import base64
import io

import streamlit as st
from streamlit import _gather_metrics
import pandas as pd
import xlsxwriter
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
from streamlit.components.v1 import html
from streamlit_lottie import st_lottie
from supabase import create_client, Client

# Importación de módulos personalizados
import pptx_generator
import pedagogical_assistant
import analysis_core
import modules.database as db
import modules.recursos as recursos
import modules.gamificacion as gamificacion

# --- CONSOLIDACIÓN DEL MÓDULO DE EVALUACIÓN ---
# Importamos el módulo completo y las funciones específicas en un solo bloque
try:
    import modules.evaluacion as evaluacion
    
    from modules.evaluacion import (
        convert_df_to_excel,
        mostrar_analisis_por_estudiante,
        mostrar_comparacion_entre_periodos,    # coma aquí
    )
except ImportError as e:
    st.error(f"Error crítico de importación en 'modules/evaluacion.py': {e}")

# --- UTILIDADES ---
def cargar_lottie(filepath):
    """Carga archivos JSON para animaciones Lottie."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

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

    # === NUEVO: Listener para detectar automáticamente el modo de recuperación ===
    def on_auth_state_change(event: str, session):
        """
        Esta función se ejecuta cada vez que cambia el estado de autenticación en Supabase.
        Cuando el usuario hace clic en el enlace de recuperación del correo, Supabase
        emite el evento "PASSWORD_RECOVERY" y crea una sesión temporal.
        """
        if event == "PASSWORD_RECOVERY":
            st.session_state.in_recovery_mode = True
            # Forzamos recarga para mostrar inmediatamente el formulario de nueva contraseña
            st.rerun()

    # Registramos el listener (esto es clave)
    supabase.auth.on_auth_state_change(on_auth_state_change)

except KeyError:
    st.error("Error: Faltan las claves de Supabase en 'secrets.toml'.")
    st.stop()
except Exception as e:
    st.error(f"Error al conectar con Supabase: {e}")
    st.stop()

# Inicialización de variables de sesión (se mantiene igual)
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

# === NUEVO: Aseguramos que el estado de recuperación exista ===
if 'in_recovery_mode' not in st.session_state:
    st.session_state.in_recovery_mode = False

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


from streamlit.components.v1 import html  # Si lo usas en otro lugar, mantenlo; aquí ya no es necesario para esto

# =========================================================================
# === 4. PÁGINA DE LOGIN (RECUPERACIÓN DE CONTRASEÑA AUTOMÁTICA - VERSIÓN FINAL Y ESTABLE) ===
# =========================================================================
def login_page():
    # --- ESTILO VISUAL MINIMALISTA CENTRADO (OPCIÓN 1) ---
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');
        html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

        /* Fondo degradado limpio */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #FF006E 0%, #8338EC 50%, #FB5607 100%);
            background-attachment: fixed;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        /* Ondas fluidas sutiles (opcional - si no te gusta, comenta la línea) */
        [data-testid="stAppViewContainer"]::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: url('https://svgshare.com/i/11rF.svg') no-repeat center center/cover;
            opacity: 0.2;
            z-index: -1;
        }

        /* Limpieza total */
        header, footer, [data-testid="stHeaderActionElements"] { display: none !important; }

        /* Tarjeta única centrada */
        .glass-card {
            background: rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 50px 40px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.4);
            width: 100%;
            max-width: 460px;
            text-align: center;
        }

        /* Logo con sombra para resaltar */
        .logo-img {
            max-width: 260px;
            margin: 0 auto 30px;
            display: block;
            filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.5));
        }

        /* Títulos y textos en blanco */
        h2 {
            color: white !important;
            font-size: 2rem;
            margin: 0 0 10px 0;
        }
        p {
            color: rgba(255,255,255,0.9) !important;
            font-size: 1.1rem;
            margin: 0 0 40px 0;
        }
        h3 {
            color: white !important;
            text-align: center;
            margin: 30px 0 20px 0;
        }

        /* Tabs grandes y limpios */
        [data-baseweb="tab-list"] {
            justify-content: center !important;
            margin: 30px 0;
        }
        button[data-baseweb="tab"] {
            background: rgba(255,255,255,0.25) !important;
            color: white !important;
            border-radius: 12px !important;
            padding: 12px 28px !important;
            font-size: 1.1rem !important;
            margin: 0 8px !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: white !important;
            color: #FB5607 !important;
        }

        /* Inputs con fondo blanco y texto negro */
        .stTextInput > div > div > input {
            background-color: white !important;
            color: black !important;
            border-radius: 12px !important;
            padding: 14px !important;
            font-size: 1rem !important;
        }

        /* Botón principal naranja */
        .stForm button[kind="primary"] {
            background-color: #FB5607 !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 14px !important;
            font-size: 1.1rem !important;
            font-weight: bold !important;
            width: 100%;
        }

        /* Link "¿Olvidaste?" sutil */
        .forgot-link {
            text-align: center;
            margin: 20px 0;
        }
        .forgot-link button {
            background: none !important;
            border: none !important;
            color: white !important;
            text-decoration: underline;
            font-size: 1rem;
            padding: 0;
            cursor: pointer;
        }

        /* Botón contacto verde */
        .contact-btn {
            margin-top: 30px;
            text-align: center;
        }
        .contact-btn a {
            display: block;
            padding: 16px;
            background-color: #00C853;
            color: white;
            text-align: center;
            border-radius: 12px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1rem;
        }

        /* RESPONSIVE */
        @media (max-width: 640px) {
            .glass-card { padding: 40px 25px; border-radius: 20px; }
            .logo-img { max-width: 220px; }
            h2 { font-size: 1.8rem; }
            button[data-baseweb="tab"] { padding: 10px 20px; font-size: 1rem; }
        }
    </style>
    """, unsafe_allow_html=True)

    # --- TARJETA ÚNICA CENTRADA ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    # --- LOGO RESALTADO CON SOMBRA ---
    st.image("assets/logotipo-aulametrics.png", class_="logo-img")

    # --- TÍTULO Y SUBTÍTULO ---
    st.markdown("<h2>Bienvenido a AulaMetrics</h2>", unsafe_allow_html=True)
    st.markdown("<p>Tu asistente pedagógico y analista de datos.</p>", unsafe_allow_html=True)

    # --- TABS ---
    tab_login, tab_register = st.tabs([" Iniciar Sesión ", " Registrarme "])

    # --- PESTAÑA LOGIN ---
    with tab_login:
        with st.form("login_form"):
            st.markdown("### 🔐 Acceso Docente")
            email = st.text_input("Correo Electrónico", key="login_email", placeholder="ejemplo@escuela.edu.pe")
            password = st.text_input("Contraseña", type="password", key="login_password", placeholder="Ingresa tu contraseña")
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)

            if submitted:
                try:
                    session = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.logged_in = True
                    st.session_state.user = session.user
                    st.session_state.show_welcome_message = True
                    if 'registro_exitoso' in st.session_state:
                        del st.session_state['registro_exitoso']
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al iniciar sesión: {e}")

        # Olvidaste contraseña
        st.markdown('<div class="forgot-link">', unsafe_allow_html=True)
        if st.button("¿Olvidaste tu contraseña?", type="secondary"):
            st.session_state.show_forgot_form = True
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.get("show_forgot_form", False):
            st.markdown("### 🔄 Recuperar acceso")
            with st.form("forgot_password_form"):
                forgot_email = st.text_input("Ingresa tu correo electrónico", placeholder="ejemplo@escuela.edu.pe")
                sent = st.form_submit_button("Enviar enlace de recuperación", type="primary")

                if sent:
                    if not forgot_email:
                        st.error("Por favor ingresa tu correo.")
                    else:
                        try:
                            redirect_url = "https://aulametrics.streamlit.app/"
                            supabase.auth.reset_password_for_email(
                                forgot_email,
                                options={"redirect_to": redirect_url}
                            )
                            st.success("¡Enlace de recuperación enviado! Revisa tu bandeja de entrada (y spam).")
                            st.session_state.show_forgot_form = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al enviar el enlace: {e}")

            if st.button("← Volver al inicio de sesión"):
                st.session_state.show_forgot_form = False
                st.rerun()

    # --- PESTAÑA REGISTRO ---
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

    # --- BOTÓN CONTACTO ---
    st.markdown('<div class="contact-btn">', unsafe_allow_html=True)
    url_netlify = "https://chrisgonzalesllu1920-collab.github.io/aulametrics-landing/"
    st.markdown(f"""
    <a href="{url_netlify}" target="_blank">
        💬 ¿Dudas? Contáctanos/TikTok
    </a>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # Cierra glass-card
       
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
    Punto de entrada en la aplicación principal.
    Llama a la función centralizada en el módulo de evaluación.
    """
    evaluacion.configurar_uploader()

def mostrar_analisis_general(info_areas):
    """
    Punto de entrada en la aplicación principal.
    Llama a la función centralizada en el módulo de evaluación para mostrar estadísticas y gráficos.
    """
    evaluacion.mostrar_analisis_general(info_areas)

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

    # 1. SISTEMA DE EVALUACIÓN (UNIFICADO: CARGA + VISTAS)
    if pagina == "Sistema de Evaluación":
        st.header("📊 Sistema de Evaluación")
    
        # Uploader principal SOLO si NO hay datos cargados (arriba, fuera de pestañas)
        if not st.session_state.df_cargado:
            st.info("Carga un archivo Excel para activar Vista Global y Perfil por Estudiante.")
            configurar_uploader()  # ← ÚNICO llamado aquí
    
        # Siempre mostramos las 3 pestañas
        tab_global, tab_individual, tab_comparar = st.tabs([
            "🌎 VISTA GLOBAL DEL AULA",
            "👤 PERFIL POR ESTUDIANTE",
            "📈 COMPARAR PERÍODOS"
        ])
    
        with tab_global:
            if st.session_state.df_cargado:
                info_areas = st.session_state.get('info_areas', {})
                mostrar_analisis_general(info_areas)
            else:
                st.info("Carga un archivo arriba para ver el análisis global del aula.")
    
        with tab_individual:
            if st.session_state.df_cargado:
                df_first = st.session_state.get('df')
                df_config = st.session_state.get('df_config')
                info_areas = st.session_state.get('info_areas')
                mostrar_analisis_por_estudiante(df_first, df_config, info_areas)
            else:
                st.info("Carga un archivo arriba para analizar perfiles individuales.")
    
        with tab_comparar:
            mostrar_comparacion_entre_periodos()

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

















