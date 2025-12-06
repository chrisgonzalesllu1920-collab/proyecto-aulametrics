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
import asyncio # Necesario para manejar tareas asíncronas

# --- NUEVAS IMPORTACIONES DE GAMIFICACIÓN ---
from gamification import config as gm_config
from gamification import core as gm_core
from gamification import views as gm_views
# ---------------------------------------------

# --- FUNCIÓN PARA CARGAR ROBOTS (LOTTIE) ---
def cargar_lottie(filepath):
    """Carga un archivo Lottie de la ruta especificada."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None # Devuelve None si el archivo no existe

# =========================================================================
# === 1. CONFIGURACIÓN INICIAL Y SUPABASE ===
# =========================================================================

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
  page_title="AulaMetrics",
  page_icon="assets/isotipo.png", # Asegúrate de que este archivo exista
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

    html, body, [class*="css"], .st-bc, .st-bb, .st-bd, .st-be, .st-bf, .st-bi, .st-bj, .st-bk {
        font-family: 'Roboto', sans-serif;
    }

    /* Ajuste de título para la sección de gamificación */
    .gamification-header {
        color: #007bff; /* Color primario de ejemplo */
        font-weight: 700;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 3px solid #ff4b4b; /* Color secundario de ejemplo */
    }

    /* Limpieza de espacio superior */
    div.stToolbar {
        height: 0;
        visibility: hidden;
        display: none;
    }

    /* Ajuste general de contenedores */
    .stApp {
        background-color: #f7f9fc; /* Fondo muy claro */
    }

    .main .block-container {
        padding-top: 35px;
        padding-right: 35px;
        padding-left: 35px;
        padding-bottom: 35px;
    }

    /* Estilo del sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff; /* Sidebar blanco */
        border-right: 1px solid #e0e0e0;
    }

    /* Botones de menú en el sidebar */
    [data-testid="stSidebarNav"] li a {
        font-weight: 500;
        color: #333333;
        border-radius: 8px;
        margin: 5px 0;
        padding: 10px 15px;
    }

    [data-testid="stSidebarNav"] li a:hover {
        background-color: #e6f7ff; /* Hover suave */
        color: #007bff;
    }

    /* Estilo para el botón de sesión y bienvenida */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    </style>
    """, unsafe_allow_html=True)


# --- INICIALIZACIÓN DE SUPABASE ---
# Las variables de entorno deben estar configuradas en Streamlit Secrets o en el entorno
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.error("Error de configuración: Las variables de entorno de Supabase (URL y KEY) no están configuradas.")
    supabase = None # Asegurarse de que Supabase sea None si falla la configuración

# --- INICIALIZACIÓN DE ESTADO DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'dataframe' not in st.session_state:
    st.session_state.dataframe = None
if 'show_welcome_message' not in st.session_state:
    st.session_state.show_welcome_message = False

# =========================================================================
# === 2. FUNCIONES DE AUTENTICACIÓN ===
# =========================================================================

def handle_login(email: str):
    """Maneja el inicio de sesión por correo electrónico (Magic Link)."""
    if not supabase: return
    try:
        # Nota: Asume que st.secrets["redirect_url"] está configurado
        supabase.auth.sign_in_with_otp({
            "email": email,
            "options": {
                "email_redirect_to": st.secrets.get("redirect_url", "https://app-url-placeholder.com")
            }
        })
        st.success("¡Enlace mágico enviado! Revisa tu correo electrónico para iniciar sesión.")
    except Exception as e:
        st.error(f"Error al enviar el enlace: {e}")

def handle_logout():
    """Cierra la sesión del usuario."""
    if not supabase: return
    try:
        # Asegurarse de que solo se llame a sign_out si hay una sesión activa
        if st.session_state.user:
             supabase.auth.sign_out()
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = 'home'
        st.session_state.show_welcome_message = False
        st.session_state.dataframe = None # Limpiar datos al cerrar sesión
        st.rerun()
    except Exception as e:
        st.error(f"Error al cerrar la sesión: {e}")


def show_auth_ui():
    """Muestra la interfaz de usuario para el inicio de sesión."""
    st.sidebar.title("🔑 Acceso Docente")
    email = st.sidebar.text_input("Correo Electrónico (Docente)")
    if st.sidebar.button("📧 Enviar Enlace de Acceso"):
        if email:
            handle_login(email)
        else:
            st.sidebar.warning("Por favor, ingresa tu correo electrónico.")

# =========================================================================
# === 3. FUNCIONES DE VISTAS (PÁGINAS) ===
# =========================================================================

def show_home():
    """Muestra la página de inicio o bienvenida."""
    st.title("👋 ¡Bienvenido/a a AulaMetrics!")
    st.markdown("---")

    col1, col2 = st.columns([3, 2])

    with col1:
        st.header("Tu Asistente de Análisis de Datos Educativos 📊")
        st.markdown("""
            AulaMetrics te permite transformar tus datos de notas y asistencia en información pedagógica valiosa,
            generar informes de desempeño, presentaciones automáticas y **dinámicas de clase interactivas** con el nuevo
            módulo de **Gamificación**.

            #### Características Clave:
            * **Análisis Descriptivo:** Visualiza el rendimiento de tu clase con gráficos automáticos.
            * **Asistente Pedagógico (IA):** Obtén retroalimentación y sugerencias para estudiantes.
            * **Generador de Presentaciones:** Crea presentaciones de PowerPoint listas para usar.
            * **🎉 Sorteos y Dinámicas:** Usa la nueva sección de **Gamificación** para seleccionar estudiantes al azar, crear equipos o gestionar puntos de clase.

            **¡Comienza cargando tu archivo de datos en la sección 'Carga de Datos' para desbloquear todas las herramientas!**
        """)
        if st.session_state.dataframe is None:
             st.info("💡 Consejo: Navega a **Carga de Datos** para empezar a trabajar con tus archivos.")

    with col2:
        # Lottie para la vista de inicio
        lottie_home = cargar_lottie("assets/home_robot.json")
        if lottie_home:
            st_lottie(lottie_home, height=300, key="home_lottie")
        else:
            st.image("https://placehold.co/400x300/F0F2F6/333333?text=Robot+Lottie+Placeholder", caption="Ilustración de Bienvenida")

    st.markdown("---")
    st.subheader("🚀 ¿Qué quieres hacer hoy?")
    cols = st.columns(4)

    if cols[0].button("1. Cargar Datos", use_container_width=True):
        st.session_state.page = 'carga_datos'
        st.rerun()
    if cols[1].button("2. Analizar Rendimiento", use_container_width=True):
        st.session_state.page = 'analisis_descriptivo'
        st.rerun()
    if cols[2].button("3. Asistente IA", use_container_width=True):
        st.session_state.page = 'asistente_pedagogico'
        st.rerun()
    if cols[3].button("4. Sorteos y Dinámicas 🎉", type="primary", use_container_width=True):
        st.session_state.page = 'sorteo_dinamicas'
        st.rerun()


def show_carga_datos():
    """Permite al usuario cargar un archivo Excel para el análisis."""
    st.header("📤 Carga de Datos y Configuración")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Sube tu archivo de notas o asistencia (formato .xlsx)",
        type=['xlsx'],
        help="El archivo debe contener al menos una columna con 'Nombres' y otras columnas con 'Notas' o 'Puntajes'."
    )

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.session_state.dataframe = df
            st.success("¡Archivo cargado y listo para analizar!")
            st.caption("Primeras 5 filas del archivo:")
            st.dataframe(df.head(), use_container_width=True)

            # Intento de inferir la columna de nombres
            name_cols = [col for col in df.columns if 'nombre' in col.lower() or 'estudiante' in col.lower()]
            if name_cols:
                st.session_state.name_column = name_cols[0]
            else:
                st.session_state.name_column = st.selectbox(
                    "Por favor, selecciona la columna que contiene los nombres de los estudiantes:",
                    df.columns
                )

        except Exception as e:
            st.error(f"Error al leer el archivo: Asegúrate de que es un archivo Excel válido. Detalles del error: {e}")

    elif st.session_state.dataframe is not None:
        st.success("Hay un archivo cargado en la sesión. Puedes proceder con el análisis.")
        st.dataframe(st.session_state.dataframe.head(), use_container_width=True)
        st.markdown(f"Columna de Nombres seleccionada: **{st.session_state.name_column if 'name_column' in st.session_state else 'No seleccionada'}**")

    else:
        lottie_upload = cargar_lottie("assets/upload_data.json")
        if lottie_upload:
            st_lottie(lottie_upload, height=200, key="upload_lottie")
        st.info("Esperando la carga de un archivo para comenzar el análisis.")


def show_analisis_descriptivo():
    """Muestra el análisis descriptivo y gráficos."""
    st.header("📈 Análisis Descriptivo de Rendimiento")
    st.markdown("---")

    df = st.session_state.dataframe

    if df is None:
        st.warning("⚠️ Debes cargar un archivo en la sección 'Carga de Datos' primero.")
        return

    # Llamada a la función principal de análisis del módulo 'analysis_core'
    # Esta función debe existir en tu módulo 'analysis_core.py'
    try:
        analysis_core.generate_descriptive_analysis(df)
    except NameError:
        st.error("Error: El módulo 'analysis_core' o su función 'generate_descriptive_analysis' no está disponible o no se ha definido correctamente.")
        st.stop()


def show_asistente_pedagogico():
    """Muestra la interfaz del asistente de IA."""
    st.header("🤖 Asistente Pedagógico (IA)")
    st.markdown("---")

    df = st.session_state.dataframe

    if df is None:
        st.warning("⚠️ Debes cargar un archivo en la sección 'Carga de Datos' primero.")
        return

    # Llamada a la función principal del módulo 'pedagogical_assistant'
    # Esta función debe existir en tu módulo 'pedagogical_assistant.py'
    try:
        pedagogical_assistant.show_assistant_interface(df)
    except NameError:
        st.error("Error: El módulo 'pedagogical_assistant' o su función 'show_assistant_interface' no está disponible o no se ha definido correctamente.")
        st.stop()


def show_generador_pptx():
    """Muestra la interfaz para generar presentaciones PPTX."""
    st.header("🖼️ Generador de Presentaciones PPTX")
    st.markdown("---")

    df = st.session_state.dataframe

    if df is None:
        st.warning("⚠️ Debes cargar un archivo en la sección 'Carga de Datos' primero.")
        return

    # Llamada a la función principal del módulo 'pptx_generator'
    # Esta función debe existir en tu módulo 'pptx_generator.py'
    try:
        pptx_generator.show_pptx_generator(df)
    except NameError:
        st.error("Error: El módulo 'pptx_generator' o su función 'show_pptx_generator' no está disponible o no se ha definido correctamente.")
        st.stop()


# =========================================================================
# === 4. FUNCIÓN DE VISTA DE GAMIFICACIÓN (MODIFICADA) ===
# =========================================================================

def show_sorteo_y_dinamicas():
    """
    Muestra la aplicación completa de gamificación usando el nuevo módulo.

    Esta función ha sido modificada para delegar la vista
    al nuevo módulo 'gamification/views.py', eliminando la lógica antigua
    del sorteo rápido.
    """
    st.header("🎉 Módulo de Gamificación y Dinámicas de Clase")
    st.markdown("---")

    # ---------------------------------------------------------------------
    # --- LÓGICA DE GAMIFICACIÓN (USANDO EL NUEVO MÓDULO) ---
    # ---------------------------------------------------------------------

    # Se asume que el nuevo módulo necesita el DataFrame si existe,
    # aunque la gestión de datos persistentes la hará con Supabase.
    df = st.session_state.dataframe

    if df is None:
        st.info("Para algunas dinámicas, puedes cargar primero tu lista de estudiantes en 'Carga de Datos'.")

    # Delegación de la renderización a gamification/views.py
    # Esta función debe existir en tu módulo 'gamification/views.py'
    try:
        gm_views.show_gamification_app()
    except NameError:
        st.error("Error: El módulo 'gamification.views' o su función 'show_gamification_app' no está disponible. Asegúrate de que los archivos de gamificación estén definidos.")
        st.stop()


# =========================================================================
# === 5. ESTRUCTURA DE LA APLICACIÓN ===
# =========================================================================

def show_sidebar_menu():
    """Muestra el menú de navegación en la barra lateral."""
    st.sidebar.markdown("### 🛠️ Herramientas")
    menu_options = {
        'home': '🏠 Inicio',
        'carga_datos': '📤 Carga de Datos',
        'analisis_descriptivo': '📈 Análisis Descriptivo',
        'asistente_pedagogico': '🤖 Asistente Pedagógico (IA)',
        'generador_pptx': '🖼️ Generador PPTX',
        'sorteo_dinamicas': '🎉 Sorteos y Dinámicas'
    }

    selected_page = st.sidebar.radio(
        "Navegación",
        options=list(menu_options.keys()),
        format_func=lambda x: menu_options[x],
        key="sidebar_page_select"
    )

    if selected_page:
        st.session_state.page = selected_page

    st.sidebar.markdown("---")

    if st.session_state.logged_in:
        # Mostrar información del usuario logueado
        user_info = st.session_state.user.get('user_metadata', {})
        email = st.session_state.user.get('email', 'N/A')
        st.sidebar.caption(f"**Usuario:** {email}")
        st.sidebar.caption(f"**ID:** {st.session_state.user.get('id', 'N/A')[:8]}...")
        if st.sidebar.button("🚪 Cerrar Sesión", type="secondary"):
            handle_logout()
    else:
        # Si no está logueado, mostrar la UI de autenticación
        show_auth_ui()


def show_main_content():
    """Renderiza el contenido principal basado en la página seleccionada."""

    if st.session_state.page == 'home':
        show_home()
    elif st.session_state.page == 'carga_datos':
        show_carga_datos()
    elif st.session_state.page == 'analisis_descriptivo':
        show_analisis_descriptivo()
    elif st.session_state.page == 'asistente_pedagogico':
        show_asistente_pedagogico()
    elif st.session_state.page == 'generador_pptx':
        show_generador_pptx()
    elif st.session_state.page == 'sorteo_dinamicas':
        show_sorteo_y_dinamicas()
    else:
        # Fallback por si la página no se encuentra
        st.session_state.page = 'home'
        show_home()

# =========================================================================
# === 6. FUNCIÓN DE BIENVENIDA (POST-LOGIN) ===
# =========================================================================

def show_welcome_message():
    """Muestra un mensaje de bienvenida emergente solo una vez tras el login exitoso."""
    if st.session_state.show_welcome_message and st.session_state.logged_in:
        st.balloons()
        st.toast("¡Inicio de sesión exitoso! Bienvenido/a a AulaMetrics.", icon="🎉")
        # Desactivar para que no se muestre en cada rerun
        st.session_state.show_welcome_message = False

# =========================================================================
# === 7. EJECUCIÓN PRINCIPAL ===
# =========================================================================

# --- MANEJO DEL ENLACE MÁGICO DE SUPABASE ---
query_params = st.query_params
auth_code = query_params.get("code")

if auth_code and not st.session_state.logged_in and supabase:
    # Este bloque se ejecuta cuando el usuario hace clic en el Magic Link
    try:
        # Intercambiar el código por una sesión
        session_data = supabase.auth.exchange_code_for_session(auth_code)
        if session_data.session:
            st.session_state.logged_in = True
            st.session_state.user = session_data.session.user
            st.session_state.show_welcome_message = True
            # Limpiar el parámetro 'code' de la URL para evitar re-ejecuciones
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        # Manejo de errores durante el intercambio (código expirado, etc.)
        st.error(f"Error en la autenticación. Por favor, intenta iniciar sesión de nuevo. Detalle: {e}")
        # Limpiar el parámetro 'code' para evitar loops
        st.query_params.clear()
        st.rerun()

# --- ARRANQUE DE LA APLICACIÓN ---

# 1. Mostrar el mensaje de bienvenida (si aplica)
show_welcome_message()

# 2. Mostrar la barra lateral
show_sidebar_menu()

# 3. Mostrar el contenido principal de la página
# Solo mostrar el contenido real si está logueado, sino, mostrar un mensaje.
if st.session_state.logged_in:
    show_main_content()
else:
    # Contenido para usuarios no logueados (página pública o de landing)
    show_home() # Usamos la misma función de inicio para la landing pública


