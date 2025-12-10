import streamlit as st
import json
import os
import time
import random
import pandas as pd
import pedagogical_assistant
import base64
from datetime import datetime
from types import SimpleNamespace


# --- IMPORTS DE FIREBASE (Necesarios para el SDK Admin) ---
# Se necesita para la lógica de inicialización y las funciones de DB
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth, initialize_app
except ImportError:
    # Esto solo debería fallar si la librería no está instalada
    st.error("Error: La librería 'firebase-admin' no está instalada.")

# --- ACCESO SEGURO A VARIABLES GLOBALES DE CANVAS ---
# En Canvas, las variables se inyectan como globales de Python, NO como env vars.
# Usamos try/except NameError para manejar entornos de desarrollo locales.
try:
    # Intenta acceder a las variables globales de Canvas
    APP_ID = __app_id
    FIREBASE_CONFIG_JSON = __firebase_config
    INITIAL_AUTH_TOKEN = __initial_auth_token
except NameError:
    # Fallback para desarrollo local (puedes cargar un archivo de secrets.json aquí)
    APP_ID = "default-app-id"
    FIREBASE_CONFIG_JSON = "{}"
    INITIAL_AUTH_TOKEN = None

# ============================================================
#   MÓDULO DE GAMIFICACIÓN – VERSIÓN ORGANIZADA
# ============================================================

# ============================================================
#   A. CONFIGURACIÓN E INICIALIZACIÓN DE FIREBASE/AUTH
# ============================================================

def initialize_firebase():
    """Inicializa Firebase, Firestore y autentica al usuario (usando el SDK Admin)."""
    
    # Solo ejecutar la inicialización una vez
    if st.session_state.get('is_auth_ready', False):
        return
        
    st.session_state['is_auth_ready'] = False # Estado inicial: no listo

    # Si no hay configuración de Firebase, asumimos modo offline/local.
    if not FIREBASE_CONFIG_JSON or FIREBASE_CONFIG_JSON == "{}":
        st.session_state['db'] = None
        st.session_state['auth'] = None
        st.session_state['appId'] = APP_ID
        st.session_state['userId'] = 'offline-user-id'
        st.session_state['is_auth_ready'] = True
        st.session_state['is_authenticated'] = False
        st.warning("⚠️ Ejecutando sin conexión a Firebase. Los datos no se guardarán.")
        return

    try:
        # 1. Parsear configuración y credenciales
        firebase_config = json.loads(FIREBASE_CONFIG_JSON)
        cred = credentials.Certificate(firebase_config)
        
        # 2. Inicializar la app (solo si no está ya inicializada)
        # Usamos el APP_ID como nombre para evitar conflictos si hay múltiples inicializaciones
        if not firebase_admin._apps or APP_ID not in firebase_admin._apps:
            app = initialize_app(cred, name=APP_ID)
        else:
            app = firebase_admin.get_app(APP_ID)
            
        db = firestore.client(app)
        firebase_auth = auth
        
        # 3. Autenticación y obtención del UserID
        user_id = None
        if INITIAL_AUTH_TOKEN:
            try:
                # Verifica el token seguro y obtiene el ID de usuario (UID)
                decoded_token = firebase_auth.verify_id_token(INITIAL_AUTH_TOKEN)
                user_id = decoded_token['uid']
                st.session_state['is_authenticated'] = True
            except Exception as e:
                # Token inválido o expirado
                st.warning(f"Error de autenticación, usando ID anónimo. Detalle: {e}")
                pass
                
        # 4. Fallback si no hay token o falló la verificación (Usuario Anónimo)
        if user_id is None:
            # Genera un ID de usuario único para sesiones no autenticadas (anónimas)
            # Usar 'uuid4().hex' es más seguro que os.urandom(16).hex() para este propósito.
            import uuid
            user_id = "anonymous_" + uuid.uuid4().hex
            st.session_state['is_authenticated'] = False

        # 5. Guardar el estado de sesión y marcar como listo
        st.session_state['db'] = db
        st.session_state['auth'] = firebase_auth
        st.session_state['appId'] = APP_ID
        st.session_state['userId'] = user_id
        st.session_state['is_auth_ready'] = True
        
        # Opcional: print(f"Firebase Inicializado. UserId: {st.session_state.userId}, AppId: {APP_ID}")

    except Exception as e:
        st.error(f"FALLO CRÍTICO DE FIREBASE/AUTH: No se pudo conectar la DB. {e}")
        st.session_state['is_auth_ready'] = False
        st.session_state['db'] = None

# ============================================================
#   MÓDULO DE GAMIFICACIÓN – VERSIÓN ORGANIZADA
# ============================================================

# ============================================================
#   A. CONFIGURACIÓN E INICIALIZACIÓN DE FIREBASE/AUTH
# ============================================================

def initialize_firebase():
    """Inicializa Firebase, Firestore y autentica al usuario (usando el SDK Admin)."""
    
    # Solo ejecutar la inicialización una vez
    if st.session_state.get('is_auth_ready', False):
        return
        
    st.session_state['is_auth_ready'] = False # Estado inicial: no listo

    # Si no hay configuración de Firebase, asumimos modo offline/local.
    if not FIREBASE_CONFIG_JSON or FIREBASE_CONFIG_JSON == "{}":
        st.session_state['db'] = None
        st.session_state['auth'] = None
        st.session_state['appId'] = APP_ID
        st.session_state['userId'] = 'offline-user-id'
        st.session_state['is_auth_ready'] = True
        st.session_state['is_authenticated'] = False
        st.warning("⚠️ Ejecutando sin conexión a Firebase. Los datos no se guardarán.")
        return

    try:
        # 1. Parsear configuración y credenciales
        firebase_config = json.loads(FIREBASE_CONFIG_JSON)
        cred = credentials.Certificate(firebase_config)
        
        # 2. Inicializar la app (solo si no está ya inicializada)
        # Usamos el APP_ID como nombre para evitar conflictos si hay múltiples inicializaciones
        if not firebase_admin._apps or APP_ID not in firebase_admin._apps:
            app = initialize_app(cred, name=APP_ID)
        else:
            app = firebase_admin.get_app(APP_ID)
            
        db = firestore.client(app)
        firebase_auth = auth
        
        # 3. Autenticación y obtención del UserID
        user_id = None
        if INITIAL_AUTH_TOKEN:
            try:
                # Verifica el token seguro y obtiene el ID de usuario (UID)
                decoded_token = firebase_auth.verify_id_token(INITIAL_AUTH_TOKEN)
                user_id = decoded_token['uid']
                st.session_state['is_authenticated'] = True
            except Exception as e:
                # Token inválido o expirado
                st.warning(f"Error de autenticación, usando ID anónimo. Detalle: {e}")
                pass
                
        # 4. Fallback si no hay token o falló la verificación (Usuario Anónimo)
        if user_id is None:
            # Genera un ID de usuario único para sesiones no autenticadas (anónimas)
            # Usar 'uuid4().hex' es más seguro que os.urandom(16).hex() para este propósito.
            import uuid
            user_id = "anonymous_" + uuid.uuid4().hex
            st.session_state['is_authenticated'] = False

        # 5. Guardar el estado de sesión y marcar como listo
        st.session_state['db'] = db
        st.session_state['auth'] = firebase_auth
        st.session_state['appId'] = APP_ID
        st.session_state['userId'] = user_id
        st.session_state['is_auth_ready'] = True
        
        # Opcional: print(f"Firebase Inicializado. UserId: {st.session_state.userId}, AppId: {APP_ID}")

    except Exception as e:
        st.error(f"FALLO CRÍTICO DE FIREBASE/AUTH: No se pudo conectar la DB. {e}")
        st.session_state['is_auth_ready'] = False
        st.session_state['db'] = None

# ============================================================
#    B. GESTIÓN DE ESTADO Y UTILIDADES DE FIREBASE (ACTUALIZADO)
# ============================================================

# --- UTILIDADES DE SIMULACIÓN NECESARIAS ---
# Nota: Estas utilidades deben estar definidas antes de esta sección.
# firestore = SimpleNamespace(SERVER_TIMESTAMP='SERVER_TIMESTAMP_SIM') # Asumimos que ya está definido arriba

# --- DATOS SIMULADOS PARA LA LECTURA (onSnapshot) ---
# Usamos una estructura simple que simula lo que devolvería doc.to_dict()
# Esta lista será modificada por 'guardar_juego_trivia' y 'eliminar_juego_trivia'
simulated_firestore_games = [
    {'doc_id': 'game_a', 'titulo': 'La Célula y sus Organelos', 'created_at': time.time() - 3600*24, 'configuracion': {'grado': '6° Primaria', 'area': 'Ciencias', 'num_preguntas': 4, 'origen': 'Manual'}, 'is_public': False, 'preguntas': [{'pregunta': 'Simulada 1', 'respuesta_correcta': 'X'}]},
    {'doc_id': 'game_b', 'titulo': 'Batalla de Gettysburg (1863)', 'created_at': time.time() - 3600*12, 'configuracion': {'grado': '5° Secundaria', 'area': 'Historia', 'num_preguntas': 10, 'origen': 'IA-Tutor'}, 'is_public': True, 'preguntas': [{'pregunta': 'Simulada 2', 'respuesta_correcta': 'Y'}]},
    {'doc_id': 'game_c', 'titulo': 'Introducción al Álgebra Lineal', 'created_at': time.time(), 'configuracion': {'grado': 'Universidad', 'area': 'Matemáticas', 'num_preguntas': 5, 'origen': 'IA-Tutor'}, 'is_public': False, 'preguntas': [{'pregunta': 'Simulada 3', 'respuesta_correcta': 'Z'}]},
]
# ----------------------------------------------------


# Define las rutas de Firestore (Trivia Games)
def get_personal_collection_ref(collection_name="trivia_games"):
    """Retorna la referencia a la colección privada del usuario (o la ruta simulada)."""
    if not st.session_state.get('is_auth_ready'): return None 
    appId = st.session_state.get('appId', 'default-app-id')
    userId = st.session_state.get('userId', 'offline-user-id')
    
    # En la simulación, retornamos la ruta de string si no hay DB real
    if not st.session_state.get('db') or st.session_state.get('db') == 'SIM_DB':
        return f"artifacts/{appId}/users/{userId}/{collection_name}"
        
    # Ruta real (si usamos el SDK real)
    # return st.session_state.db.collection(f"artifacts").document(appId).collection("users").document(userId).collection(collection_name)
    # Usamos la ruta simulada por ahora.
    return f"artifacts/{appId}/users/{userId}/{collection_name}"


def get_global_collection_ref(collection_name="trivia_games"):
    """Retorna la referencia a la colección pública global (o la ruta simulada)."""
    if not st.session_state.get('is_auth_ready'): return None
    appId = st.session_state.get('appId', 'default-app-id')
    
    # En la simulación, retornamos la ruta de string si no hay DB real
    if not st.session_state.get('db') or st.session_state.get('db') == 'SIM_DB':
        return f"artifacts/{appId}/public/data/{collection_name}"
        
    # Ruta real
    # return st.session_state.db.collection(f"artifacts").document(appId).collection("public").document("data").collection(collection_name)
    # Usamos la ruta simulada por ahora.
    return f"artifacts/{appId}/public/data/{collection_name}"


def guardar_juego_trivia(game_data: dict, is_public: bool = False, doc_id: str = None):
    """
    Guarda el juego de trivia en Firestore en la colección personal o global.
    [IMPLEMENTACIÓN SIMULADA]
    """
    global simulated_firestore_games # Asegura que podemos modificar la lista simulada
    
    if not st.session_state.get('is_auth_ready'):
        print("Error: No se puede guardar: Firebase no está inicializado o la autenticación falló.")
        return False

    # Usar la ruta de colección simulada (o referencia real)
    collection_path = get_global_collection_ref() if is_public else get_personal_collection_ref()
    
    if collection_path is None:
        print("Error al obtener la referencia de la colección.")
        return False
        
    try:
        # Añade metadatos antes de guardar
        # Simular la generación de ID
        doc_id = doc_id if doc_id else f"sim_doc_{int(time.time() * 1000)}_{len(simulated_firestore_games)}"
        game_data['creator_id'] = st.session_state.get('userId', 'anonymous')
        game_data['created_at'] = time.time() # Usamos timestamp real para la simulación de ordenamiento
        game_data['is_public'] = is_public
        
        # --- SIMULACIÓN DE GUARDADO ---
        # 1. Borrar cualquier juego existente con el mismo ID (para simular .set)
        global simulated_firestore_games
        simulated_firestore_games = [g for g in simulated_firestore_games if g.get('doc_id') != doc_id]
        
        # 2. Añadir el nuevo/actualizado juego
        new_game = {'doc_id': doc_id, **game_data}
        simulated_firestore_games.append(new_game)
        
        # Forzar recarga de la biblioteca al guardar un nuevo juego
        st.session_state['juegos_biblioteca'] = None
        
        st.toast(f"💾 Juego '{game_data.get('titulo', 'Sin Título')}' Guardado!", icon='✅')
        return doc_id
            
    except Exception as e:
        print(f"Error al guardar el juego: {e}")
        return False


def eliminar_juego_trivia(doc_id: str):
    """
    Elimina permanentemente un juego de trivia de la colección personal del usuario.
    [IMPLEMENTACIÓN SIMULADA]
    """
    global simulated_firestore_games
    
    if not st.session_state.get('is_auth_ready'):
        print("Error: No se puede eliminar: Firebase no está inicializado o la autenticación falló.")
        st.toast("🚫 Error de autenticación. No se pudo eliminar.", icon='❌')
        return False

    # Obtenemos la referencia (real o simulada) a la colección
    collection_ref = get_personal_collection_ref()
    
    if collection_ref is None:
        print("Error al obtener la referencia de la colección.")
        return False
        
    try:
        # --- SIMULACIÓN DE ELIMINACIÓN ---
        initial_length = len(simulated_firestore_games)
        
        # Filtrar el juego a eliminar (solo si no es público) y guardar los restantes
        # El juego solo se elimina si su doc_id coincide Y NO es público.
        simulated_firestore_games = [
            g for g in simulated_firestore_games 
            if g.get('doc_id') != doc_id or g.get('is_public') == True
        ]

        if len(simulated_firestore_games) < initial_length:
            # Forzar recarga de la biblioteca al eliminar un juego
            st.session_state['juegos_biblioteca'] = None
            st.toast(f"🗑️ Juego eliminado de la biblioteca privada.", icon='✅')
            return True
        else:
            # Este mensaje puede indicar que el doc_id no existía o que era público.
            st.toast(f"🚫 Error: El juego no se pudo eliminar (no encontrado o es público).", icon='❌')
            return False
            
    except Exception as e:
        print(f"Error al eliminar el juego: {e}")
        st.toast(f"🚫 Error al eliminar el juego: {e}", icon='❌')
        return False


def obtener_juegos_trivia_usuario():
    """
    NUEVA FUNCIÓN. Simula la obtención de juegos de Trivia del usuario desde Firestore
    usando un onSnapshot listener y almacena los resultados en el estado.
    """
    global simulated_firestore_games
    
    if 'juegos_biblioteca' not in st.session_state:
        st.session_state['juegos_biblioteca'] = None
        st.session_state['is_loading_library'] = False
    
    # Asegurar que la autenticación esté lista antes de intentar "cargar"
    if not st.session_state.get('is_auth_ready'):
        return

    # Evitar llamadas repetidas si ya está cargando o ya se cargó
    if st.session_state['juegos_biblioteca'] is not None or st.session_state['is_loading_library']:
        return

    # Iniciamos la carga simulada
    st.session_state['is_loading_library'] = True
    print("Iniciando simulación de carga de juegos privados...")
    
    collection_path = get_personal_collection_ref()
    if collection_path is None:
        st.session_state['is_loading_library'] = False
        return
        
    try:
        # SIMULACIÓN DE LA CONEXIÓN Y onSnapshot
        time.sleep(0.5) # Simular latencia de carga
        
        # Filtrar los juegos que pertenecerían a la colección privada del usuario
        # Solo incluimos juegos que NO son públicos (is_public=False)
        juegos_cargados = []
        for doc in simulated_firestore_games:
            # En una aplicación real, se filtrarían por userId en el Query.
            # Aquí, solo filtramos los NO públicos.
            if not doc.get('is_public', False):
                # Asegúrate de que el juego pertenezca al usuario, aunque es implícito en la simulación
                # con 'is_public': False, lo hacemos explícito para mayor claridad.
                if doc.get('creator_id', 'anonymous') == st.session_state.get('userId', 'anonymous'):
                    juegos_cargados.append(doc)
                # Si el creator_id no coincide, asumimos que no es un juego del usuario
                # (aunque la simulación es imperfecta, sigue el espíritu del filtro de seguridad).

        # Almacenar la lista de juegos en el estado, ordenados por fecha de creación descendente
        st.session_state['juegos_biblioteca'] = sorted(
            juegos_cargados, 
            key=lambda x: x.get('created_at', 0), 
            reverse=True
        )
        print(f"Cargados {len(st.session_state['juegos_biblioteca'])} juegos privados simulados.")

    except Exception as e:
        print(f"Error simulado al cargar juegos: {e}")
        st.session_state['juegos_biblioteca'] = [] # Vacío en caso de error
        
    finally:
        st.session_state['is_loading_library'] = False

def navegar_a(pagina):
    """Cambia la página actual y fuerza un nuevo renderizado."""
    st.session_state['pagina_actual'] = pagina
    st.rerun()

# ============================================================
# C. GESTIÓN DE ESTADO GENERAL Y MENÚS DE NAVEGACIÓN
# ============================================================

def volver_menu_juegos():
    """
    Reinicia el estado para volver a mostrar el menú principal de juegos.
    Limpia todos los estados específicos de los juegos (Trivia, Preguntas Manuales, etc.).
    """
    st.session_state['juego_actual'] = None

    # Lista de estados de Trivia y submenús que deben ser borrados
    keys_to_delete = [
        'trivia_source',
        'juego_iniciado',
        'preguntas_manuales',
        'juego_preguntas',
        'pregunta_actual',

        # NUEVAS VARIABLES DE CONFIGURACIÓN DEL FORMULARIO MANUAL
        'num_preguntas_manual',
        'num_opciones_manual',
        'orden_manual'
    ]

    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()

def volver_menu_fuentes_trivia():
    """
    Vuelve al menú de selección de fuentes de Trivia ('trivia_fuentes').
    Limpia los datos de generación actual (texto IA o preguntas manuales) para un nuevo inicio.
    """
    st.session_state['juego_actual'] = 'trivia_fuentes'

    # Limpiamos el progreso de generación
    keys_to_clean = [
        'trivia_source',
        'juego_iniciado',
        'preguntas_manuales',

        # NUEVAS VARIABLES DE CONFIGURACIÓN DEL FORMULARIO MANUAL
        'num_preguntas_manual',
        'num_opciones_manual',
        'orden_manual'
    ]

    for key in keys_to_clean:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()

# ------------------------------------------------------------
# D. MENÚ PRINCIPAL DE JUEGOS (COMPLETAMENTE CORREGIDO Y ESTILIZADO)
# ------------------------------------------------------------
def mostrar_menu_juegos():

    # 1. CSS INYECCIÓN (Selector de Biblioteca corregido para máxima especificidad)
    st.markdown("""
    <style>
        /* Estilos generales para todos los botones del menú de juegos (PÚRPURA/AZUL) */
        section[data-testid="stMain"] div.stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: none !important;
            border-radius: 20px !important;
            color: white !important;
            font-family: 'Verdana', sans-serif !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            box-shadow: 0 10px 20px rgba(118, 75, 162, 0.3) !important;
            height: auto !important;
            padding: 25px 15px !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            width: 100%; /* Asegura que los botones tomen todo el ancho de la columna */
            min-height: 120px; /* Altura mínima para el texto */
        }

        section[data-testid="stMain"] div.stButton > button:hover {
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 15px 30px rgba(118, 75, 162, 0.5) !important;
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        }

        section[data-testid="stMain"] div.stButton > button p {
            font-size: 19px !important;
            font-weight: 800 !important;
            margin: 0 !important;
            line-height: 1.4 !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            text-align: center;
        }

        /* 🏆 DISEÑO CORREGIDO Y FORZADO: Biblioteca (NARANJA VIBRANTE) */
        /* Combinamos el selector de la llave (key) con la clase de Streamlit (stButton) */
        section[data-testid="stMain"] div[key="btn_card_biblioteca"] div.stButton > button {
            background: linear-gradient(135deg, #FF6F00 0%, #FFB300 100%) !important; /* NARANJA VIVO */
            box-shadow: 0 10px 20px rgba(255, 111, 0, 0.5) !important;
        }

        section[data-testid="stMain"] div[key="btn_card_biblioteca"] div.stButton > button:hover {
            background: linear-gradient(135deg, #FFB300 0%, #FF6F00 100%) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 2. Título
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h2 style="color: #4A148C; font-size: 38px; font-weight: 900; letter-spacing: -1px;">🎮 ARCADE PEDAGÓGICO</h2>
        <p style="color: #616161; font-size: 18px; font-weight: 500;">Selecciona tu desafío</p>
    </div>
    """, unsafe_allow_html=True)

    # 3. Botones - Layout con 3 columnas en la primera fila
    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        # Redirige al sub-menú de fuentes de Trivia
        if st.button("🧠 TRIVIA\n\n¿Cuánto sabes?", key="btn_card_trivia", use_container_width=True):
            st.session_state['juego_actual'] = 'trivia_fuentes'
            st.rerun()

    with col2:
        if st.button("🔤 PUPILETRAS\n\nAgudeza Visual", key="btn_card_pupi", use_container_width=True):
            st.session_state['juego_actual'] = 'pupiletras'
            st.rerun()

    with col3:
        # BOTÓN BIBLIOTECA - Usará el nuevo estilo NARANJA VIBRANTE
        if st.button("📚 BIBLIOTECA\n\nGuardar y Compartir", key="btn_card_biblioteca", use_container_width=True):
            st.session_state['juego_actual'] = 'biblioteca'
            st.rerun()

    st.write("")

    col4, col5, col_spacer = st.columns(3, gap="large")

    with col4:
        if st.button("🤖 ROBOT\n\nLógica & Deducción", key="btn_card_robot", use_container_width=True):
            st.session_state['juego_actual'] = 'robot'
            st.rerun()

    with col5:
        # Botón Sorteador (Manteniendo el mismo estilo visual)
        if st.button("🎰 SORTEADOR\n\nElegir participantes", key="btn_sorteo_v1", use_container_width=True):
            st.session_state['juego_actual'] = 'sorteador'
            st.rerun()

# ------------------------------------------------------------
# E. MENÚ DE SELECCIÓN DE FUENTES DE TRIVIA
# ------------------------------------------------------------
def mostrar_menu_fuentes_trivia():
    """Muestra el menú para seleccionar la fuente de contenido para la Trivia."""

    # 1. CSS específico para este sub-menú
    st.markdown("""
    <style>
        /* Estilos para los botones de fuente (diferentes al menú principal) */
        .source-button {
            background-color: #e8f5e9 !important; /* Verde muy claro */
            color: #1b5e20 !important; /* Verde oscuro */
            border: 3px solid #4caf50 !important; /* Verde primario */
            border-radius: 15px !important;
            font-weight: 800 !important;
            font-size: 18px !important;
            padding: 30px 15px !important;
            transition: all 0.3s;
            box-shadow: 0 4px 0 #388e3c; /* Sombra */
            text-align: center;
        }
        .source-button:hover {
            background-color: #d4edda !important;
            transform: translateY(-2px);
            box-shadow: 0 6px 0 #388e3c;
        }
        .source-button p {
            margin: 0 !important;
            line-height: 1.2;
        }
    </style>
    """, unsafe_allow_html=True)

    # 2. Barra superior
    col_back, col_title = st.columns([1, 5])
    with col_back:
        # Usamos la función de la Sección C
        if st.button("🔙 Menú Juegos", use_container_width=True, key="btn_volver_menu_fuentes"):
            volver_menu_juegos()

    with col_title:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #4CAF50; font-size: 32px; font-weight: 900;">🧠 SELECCIONA LA FUENTE DE TRIVIA</h2>
            <p style="color: #616161; font-size: 16px;">¿Cómo quieres generar el juego de preguntas?</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 3. Opciones de Fuente (En columnas para mejor layout)
    col1, col2, col3 = st.columns(3, gap="medium")

    # Eliminamos la función set_source_and_continue, la lógica va dentro del botón.

    with col1:
        # **MODIFICACIÓN CLAVE: Elaboración manual**
        if st.button("📝 Elaboración manual\n\n(Crea tus preguntas)", use_container_width=True, key="source_manual", help="Introduce directamente las preguntas y respuestas para crear el juego a partir de ellas."):
            # CAMBIO CLAVE: Cambiamos el estado de destino.
            # Ahora vamos al menú de CONFIGURACIÓN MANUAL antes de ir al formulario.
            st.session_state['juego_actual'] = 'trivia_configuracion_manual'
            st.rerun()

    with col2:
        # Archivo PDF/TXT - DESHABILITADO
        if st.button("📁 Archivo PDF/TXT\n\n(Próximamente)", use_container_width=True, key="source_archivo", disabled=True, help="Sube un documento y la IA lo analizará."):
            pass

    with col3:
        # **MODIFICACIÓN CLAVE: Uso de IA-Tutor**
        if st.button("🌐 Uso de IA-Tutor\n\n(Crea preguntas con IA)", use_container_width=True, key="source_ia_tutor", help="Deja que la IA busque un tema general en Internet y genere un juego educativo automáticamente."):
            st.session_state['juego_actual'] = 'trivia_ia_tutor'
            st.rerun()

    # Aplicamos el estilo a los botones recién creados
    st.markdown("""
    <script>
        document.querySelectorAll('button[key^="source_"]').forEach(function(button) {
            button.classList.add('source-button');
        });
    </script>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# F. JUEGO 1: TRIVIA (Generación y Lógica Principal)
# ------------------------------------------------------------
import json
# Importamos time, aunque su uso en 'mostrar_juego_trivia' ha sido refactorizado
# para evitar bloqueos en Streamlit, lo mantenemos por si el usuario lo necesita
# en futuras funciones asíncronas.
import time
import streamlit as st

# Importaciones de Firebase (Asumiendo que se usan en el entorno principal,
# pero se definen aquí si este bloque fuera el script completo)
# NOTA: En un script Streamlit normal, estas serían importaciones de la librería
# python de Firebase o de las funciones wrapper. Aquí, solo incluimos la función
# de guardado.

# NOTA: Se asume que las funciones 'volver_menu_juegos' y 'volver_menu_fuentes_trivia'
# de la Sección C, y la función 'pedagogical_assistant.generar_trivia_juego'
# están definidas o importadas en el script principal.

# --- CONFIGURACIONES GLOBALES REUTILIZABLES ---
lista_grados_global = ["1° Primaria", "2° Primaria", "3° Primaria", "4° Primaria", "5° Primaria", "6° Primaria", "1° Secundaria", "2° Secundaria", "3° Secundaria", "4° Secundaria", "5° Secundaria"]
lista_areas_global = ["Ciencia y Ambiente", "Matemáticas", "Tecnología", "Comunicación y Lenguaje", "Historia", "Geografía", "Educación Física", "Arte y Cultura", "Inglés", "Otro"]
lista_num_preguntas_global = list(range(2, 21)) # De 2 a 20 preguntas

def mostrar_generador_ia_tutor():
    """Interfaz para generar juegos de trivia con la IA."""
    st.title("🌟 Generador IA Tutor")
    
    # ... [Código de Configuración (Selectbox, Text_input)] ...

    # Botón de Generar
    if st.button("🚀 Generar Preguntas", disabled=st.session_state.get('is_generating') or not tema_input, use_container_width=True):
        # ... [Lógica de llamada a la IA y rerender] ...
        
    # ---------------------------------------------------------------
    # 💥 INICIO DEL CAMBIO DEL PASO 3
    # Este bloque solo se muestra si el juego ya fue generado.
    # ---------------------------------------------------------------
    if st.session_state.get('juego_iniciado'):
        st.markdown("---")
        st.subheader("✅ Trivia Generada - Opciones de Gestión")
        
        col_guardar, col_jugar = st.columns(2)
        
        with col_guardar:
            if st.button("💾 Guardar en mi Historial", use_container_width=True):
                # Lógica de guardado...
                st.toast("¡Juego Guardado!", icon='🎉')
                
        with col_jugar:
            if st.button("🕹️ Jugar esta Trivia Ahora", use_container_width=True, type='primary'):
                navegar_a('juego') # O la función de navegación correspondiente

        st.markdown("---")
        # Mostrar las preguntas generadas para revisión
        st.subheader("🔍 Preguntas para Revisión")
        # ... [Lógica de mostrar preguntas] ...

    elif st.session_state.get('is_generating'):
        st.info("Generando preguntas... por favor espera.")
        
    else:
        st.info("Ingresa un tema específico y haz clic en 'Generar Preguntas' para comenzar.")

def mostrar_formulario_manual():
    """Muestra el formulario para que el usuario ingrese las preguntas manualmente."""
    
    # 1. Barra superior
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("🔙 Fuentes", use_container_width=True, key="btn_manual_back"):
            # Llama a la función de la Sección C para cambiar de vista
            if 'volver_menu_fuentes_trivia' in globals():
                volver_menu_fuentes_trivia()
            else:
                st.session_state['vista_actual'] = 'menu_fuentes_trivia'
                st.rerun()
            
    with col_title:
        st.subheader("📝 Elaboración Manual de Trivia")
        st.caption("Introduce tus propias preguntas, opciones y la respuesta correcta.")

    st.divider()
    
    # --- CONFIGURACIÓN DE NÚMERO DE PREGUNTAS (Fuera del form para actualización dinámica) ---
    st.markdown("**Configuración del Juego**")
    
    # Inicializar el número de preguntas si no está en estado, y actualizar su valor
    if 'manual_num_select' not in st.session_state:
        st.session_state['manual_num_select'] = 5

    col_config1, col_config2, col_config3 = st.columns(3)

    with col_config1:
        # 3. Nivel Educativo (Grado) - AGREGADO AL FORMULARIO MANUAL
        grado_input = st.selectbox("Nivel Educativo:", lista_grados_global, index=6, key='manual_grado_select')
        
    with col_config2:
        # 2. Área/Materia - NUEVO
        area_input = st.selectbox("Área/Materia:", lista_areas_global, index=0, key='manual_area_select')
        
    with col_config3:
        # 1. Número de Preguntas (2 a 20) - ACTUALIZADO A SELECTBOX DINÁMICO
        # Guardamos la selección directamente en el estado
        num_input_selected = st.selectbox(
            "Número de Preguntas:", 
            lista_num_preguntas_global, 
            index=lista_num_preguntas_global.index(st.session_state['manual_num_select']) if st.session_state['manual_num_select'] in lista_num_preguntas_global else 3,
            key='manual_num_select' # Vincula el valor a este estado
        )

    # Lógica para manejar el número de preguntas seleccionado
    num_preguntas_actual = st.session_state['manual_num_select']
    
    # Inicializar o redimensionar la lista de preguntas manuales según el valor seleccionado
    default_q = {'pregunta': '', 'opcion_A': '', 'opcion_B': '', 'opcion_C': '', 'opcion_D': '', 'correcta': 'A'}
    if 'preguntas_manuales' not in st.session_state or len(st.session_state['preguntas_manuales']) != num_preguntas_actual:
        if 'preguntas_manuales' in st.session_state:
            old_list = st.session_state['preguntas_manuales']
            new_list = [old_list[i] if i < len(old_list) else default_q.copy() for i in range(num_preguntas_actual)]
        else:
            new_list = [default_q.copy() for _ in range(num_preguntas_actual)]

        st.session_state['preguntas_manuales'] = new_list


    # --- FORMULARIO DE ENTRADA MANUAL ---
    with st.form("manual_trivia_form", clear_on_submit=False):
        
        tema_input = st.text_input("Tema del Desafío:", placeholder="Ej: Las Leyes de Newton", max_chars=100)
        
        # Configuración de modo (Modo de juego permanece igual)
        col_mode1, col_mode2 = st.columns([2, 1])
        with col_mode1:
            modo_avance = st.radio("Modo de Juego:", ["Automático (Rápido)", "Guiado por Docente (Pausa)"], key='manual_mode_radio')
        with col_mode2:
            st.markdown(f"<p style='margin-top: 30px;'><strong>Preguntas: {num_preguntas_actual}</strong></p>", unsafe_allow_html=True) 

        
        st.markdown("---")
        st.markdown(f"### **Ingreso de Preguntas ({num_preguntas_actual} Requeridas)**")

        preguntas_form_data = []
        
        # El bucle ahora se adapta al número seleccionado
        for i in range(num_preguntas_actual): 
            st.markdown(f"#### Pregunta {i+1}")
            
            # Los valores de los inputs se vinculan al session_state
            p = st.text_area(f"Texto de la Pregunta {i+1}:", key=f'q_text_{i}', 
                             value=st.session_state['preguntas_manuales'][i]['pregunta'], height=50)
            
            col_a, col_b = st.columns(2)
            with col_a:
                a = st.text_input("Opción A:", key=f'q_opt_a_{i}', value=st.session_state['preguntas_manuales'][i]['opcion_A'])
            with col_b:
                b = st.text_input("Opción B:", key=f'q_opt_b_{i}', value=st.session_state['preguntas_manuales'][i]['opcion_B'])
                
            col_c, col_d = st.columns(2)
            with col_c:
                c = st.text_input("Opción C:", key=f'q_opt_c_{i}', value=st.session_state['preguntas_manuales'][i]['opcion_C'])
            with col_d:
                d = st.text_input("Opción D:", key=f'q_opt_d_{i}', value=st.session_state['preguntas_manuales'][i]['opcion_D'])
            
            correcta_radio_options = ['A', 'B', 'C', 'D']
            current_correcta_index = correcta_radio_options.index(st.session_state['preguntas_manuales'][i]['correcta'])
            correcta = st.radio(f"Respuesta Correcta para Pregunta {i+1}:", correcta_radio_options, key=f'q_correct_{i}', 
                                 index=current_correcta_index, horizontal=True)
            
            # Guardar el estado actual en session_state para persistir los cambios al escribir
            st.session_state['preguntas_manuales'][i].update({
                'pregunta': p, 'opcion_A': a, 'opcion_B': b, 'opcion_C': c, 'opcion_D': d, 'correcta': correcta
            })
            
            # Almacenar los datos para la validación/formateo en el submit
            preguntas_form_data.append({
                'pregunta': p,
                'opcion_A': a,
                'opcion_B': b,
                'opcion_C': c,
                'opcion_D': d,
                'correcta_key': correcta
            })
            
            st.markdown("---")
            
        submitted = st.form_submit_button("🚀 Iniciar Desafío Manual", type="primary", use_container_width=True)

        if submitted:
            # 1. Validación de entradas
            if not tema_input.strip():
                st.error("⚠️ Por favor, ingresa un Tema para el Desafío.")
                return
                
            valid_submission = True
            preguntas_finales = []
            
            for i, q_data in enumerate(preguntas_form_data):
                
                # Chequear si todos los campos están llenos
                if not q_data['pregunta'].strip() or \
                   not q_data['opcion_A'].strip() or \
                   not q_data['opcion_B'].strip() or \
                   not q_data['opcion_C'].strip() or \
                   not q_data['opcion_D'].strip():
                    st.error(f"⚠️ La Pregunta {i+1} o alguna de sus opciones está vacía. Por favor, rellena todos los campos.")
                    valid_submission = False
                    break
                    
                # 2. Formateo a la estructura de juego (el mismo JSON que genera la IA)
                # Obtenemos el texto de la respuesta correcta basándonos en la clave (A, B, C, D)
                key_map = {'A': 'opcion_A', 'B': 'opcion_B', 'C': 'opcion_C', 'D': 'opcion_D'}
                correcta_texto = q_data[key_map[q_data["correcta_key"]]]

                
                pregunta_formateada = {
                    "pregunta": q_data['pregunta'].strip(),
                    "opciones": [
                        q_data['opcion_A'].strip(),
                        q_data['opcion_B'].strip(),
                        q_data['opcion_C'].strip(),
                        q_data['opcion_D'].strip(),
                    ],
                    "respuesta_correcta": correcta_texto.strip()
                }
                preguntas_finales.append(pregunta_formateada)
            # 3. Guardar estado e iniciar juego
            if valid_submission:
                st.session_state['juego_preguntas'] = preguntas_finales
                st.session_state['juego_indice'] = 0
                st.session_state['juego_puntaje'] = 0.0 # Usar float
                st.session_state['juego_terminado'] = False
                st.session_state['tema_actual'] = tema_input
                st.session_state['modo_avance'] = "auto" if "Automático" in modo_avance else "guiado"
                st.session_state['fase_pregunta'] = "respondiendo"
                st.session_state['juego_en_lobby'] = True 
                st.session_state['juego_iniciado'] = True 
                st.session_state['trivia_source'] = 'Elaboración manual' # Establecer la fuente
                
                # Guardamos los nuevos datos de configuración, aunque solo se usan en la UI
                st.session_state['manual_grado'] = grado_input
                st.session_state['manual_area'] = area_input
                
                st.session_state['juego_actual'] = 'trivia_jugar' # Cambia la vista al juego
                st.rerun()

def mostrar_juego_trivia():
    """Muestra el lobby, el juego activo y la pantalla final de la Trivia."""
    
    # 1. CSS (Optimizado y mejorado)
    st.markdown("""
        <style>
        /* Estilos generales para el modo cine */
        .cinema-mode {
            background-color: #0d1117; /* Fondo oscuro */
            padding: 20px;
            border-radius: 10px;
        }

        /* CSS para el botón de volver en la barra superior */
        button[data-testid*="baseButton-default"][key="btn_volver_menu_juego"] {
            background-color: #fff59d !important;
            color: #1e3a8a !important;
            border: 2px solid #fbc02d !important;
            font-size: 14px !important;
            padding: 4px 10px !important;
            border-radius: 10px !important;
            box-shadow: 0px 3px 0px #f9a825 !important;
        }

        button[data-testid*="baseButton-default"][key="btn_volver_menu_juego"]:hover {
            background-color: #fff176 !important;
            transform: translateY(-2px);
            box-shadow: 0px 5px 0px #f9a825 !important;
        }
        
        /* Estilos de botones de opción (Genérico para columnas) */
        section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] div.stButton > button {
            background-color: #fff9c4 !important;
            border: 3px solid #fbc02d !important;
            border-radius: 20px !important;
            min-height: 100px !important; /* Ligeramente más pequeños para mejor responsividad */
            height: auto !important;
            white-space: normal !important;
            padding: 15px !important;
            margin-bottom: 15px !important;
            box-shadow: 0 6px 0 #f9a825 !important;
            transition: all 0.1s ease;
        }

        section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] div.stButton > button p {
            font-size: 24px !important; /* Reducido para mejor ajuste en móvil */
            font-weight: 800 !important;
            color: #333333 !important;
            line-height: 1.2 !important;
        }

        section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
            background-color: #fff59d !important;
            transform: translateY(-3px);
            border-color: #f57f17 !important;
            box-shadow: 0 9px 0 #f9a825 !important;
        }

        /* Estilos de la pregunta grande */
        .big-question {
            font-size: 40px !important; /* Adaptado para mejor lectura */
            font-weight: 800;
            color: #1e3a8a;
            text-align: center;
            background-color: #eff6ff;
            padding: 30px;
            border-radius: 25px;
            border: 5px solid #3b82f6;
            margin-bottom: 30px;
            box-shadow: 0 6px 15px rgba(0,0,0,0.15);
            line-height: 1.2;
        }
        
        /* Estilos de Botón Principal/Siguiente Pregunta */
        div.stButton > button[kind="primary"] {
            background-color: #28a745 !important;
            border-color: #1e7e34 !important;
            border: 3px solid #1e7e34 !important;
            color: white !important;
            font-size: 20px !important;
            font-weight: bold !important;
            padding: 10px 20px !important;
            box-shadow: 0 4px 0 #1e7e34 !important;
            border-radius: 15px !important;
            transition: all 0.1s ease;
        }
        
        div.stButton > button[kind="primary"]:hover {
            background-color: #1e7e34 !important;
            transform: translateY(-2px);
            box-shadow: 0 6px 0 #1c7430 !important;
        }
        
        /* Estilos de Retroalimentación */
        .feedback-correct {
            background-color: #d1e7dd; 
            color: #0f5132; 
            padding: 40px; 
            border-radius: 20px; 
            text-align: center; 
            font-size: 40px; 
            font-weight: bold; 
            border: 4px solid #badbcc; 
            margin-bottom: 20px;
        }
        .feedback-incorrect {
            background-color: #f8d7da; 
            color: #842029; 
            padding: 40px; 
            border-radius: 20px; 
            text-align: center; 
            font-size: 40px; 
            font-weight: bold; 
            border: 4px solid #f5c2c7; 
            margin-bottom: 20px;
        }

        </style>
    """, unsafe_allow_html=True)
    
    # Manejo de estado básico: si no hay juego cargado, volvemos a fuentes.
    if 'juego_preguntas' not in st.session_state:
        st.warning("No hay un juego de Trivia cargado. Volviendo al menú de fuentes.")
        if 'volver_menu_fuentes_trivia' in globals():
            volver_menu_fuentes_trivia()
        else:
            st.session_state['vista_actual'] = 'menu_fuentes_trivia'
            st.rerun()
        return

    # 2. Barra superior
    col_back, col_title = st.columns([1, 5])
    
    trivia_source = st.session_state.get('trivia_source', 'Trivia')
    
    with col_back:
        # Si el juego terminó, el botón vuelve al menú principal de juegos.
        if st.session_state.get('juego_terminado', False):
             if st.button("🔙 Menú Juegos", use_container_width=True, key="btn_volver_menu_juego"):
                 if 'volver_menu_juegos' in globals():
                     volver_menu_juegos()
                 else:
                     st.session_state['vista_actual'] = 'menu_juegos'
                     st.rerun()
        else:
            # Si el juego está en lobby o activo, el botón vuelve a la selección de fuente.
            if st.button("🔙 Fuentes", use_container_width=True, key="btn_volver_menu_juego"):
                 if 'volver_menu_fuentes_trivia' in globals():
                     volver_menu_fuentes_trivia()
                 else:
                     st.session_state['vista_actual'] = 'menu_fuentes_trivia'
                     st.rerun()
            
    with col_title:
        st.subheader(f"Desafío Trivia: {trivia_source}")

    # --- MODO CINE (Ocultar sidebar) ---
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.markdown("Genera un juego de preguntas interactivo.")
    with col_header2:
        modo_cine = st.checkbox("📺 Modo Cine", help="Oculta la barra lateral.")
    
    if modo_cine:
        st.markdown("""<style>[data-testid="stSidebar"], header, footer {display: none;}</style>""", unsafe_allow_html=True)

    st.divider()

    # --- LÓGICA TRIVIA: FASE DE LOBBY / JUEGO ACTIVO / TERMINADO ---
    
    if st.session_state.get('juego_en_lobby', False):
        # LÓGICA DE LOBBY
        tema_mostrar = st.session_state.get('tema_actual', 'Trivia')
        modo_mostrar = "Modo Automático (Rápido)" if st.session_state.get('modo_avance') == "auto" else "Modo Guiado (Pausa)"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 40px; background-color: white; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h1 style="font-size: 70px; color: #28a745; margin: 0;">🏆 TRIVIA TIME 🏆</h1>
            <h2 style="color: #555; font-size: 30px; margin-top: 10px;">Tema: {tema_mostrar[:50]}{'...' if len(tema_mostrar) > 50 else ''}</h2>
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
        # LÓGICA DE JUEGO ACTIVO
        idx = st.session_state['juego_indice']
        preguntas = st.session_state['juego_preguntas']
        current_score = st.session_state['juego_puntaje']
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
            st.markdown(f"""<div style="text-align: right;"><span style="font-size: 45px; font-weight: 900; color: #28a745; background: #e6fffa; padding: 5px 20px; border-radius: 15px; border: 2px solid #28a745;">{int(current_score)}</span></div>""", unsafe_allow_html=True)
        
        st.write("")
        st.markdown(f"""<div class="big-question">{pregunta_actual['pregunta']}</div>""", unsafe_allow_html=True)
        
        if fase == 'respondiendo':
            opciones = pregunta_actual['opciones']
            col_opt1, col_opt2 = st.columns(2)
            
            # --- Respuesta Handler ---
            def responder(opcion_elegida):
                # La respuesta correcta es el texto de la opción
                correcta = pregunta_actual['respuesta_correcta']
                # Puntos base para el cálculo (asegura que el total sea 100)
                puntos_por_pregunta = 100.0 / len(st.session_state['juego_preguntas'])
                es_correcta = (opcion_elegida == correcta)
                
                if es_correcta:
                    st.session_state['juego_puntaje'] += puntos_por_pregunta
                    st.session_state['ultimo_feedback'] = f"correcta|{int(puntos_por_pregunta)}"
                else:
                    st.session_state['ultimo_feedback'] = f"incorrecta|{correcta}"

                if modo == 'auto':
                    # MODO AUTOMÁTICO: No podemos usar time.sleep(), avanzamos inmediatamente
                    # El feedback se muestra muy brevemente antes del rerender.
                    if st.session_state['juego_indice'] < len(st.session_state['juego_preguntas']) - 1:
                        st.session_state['juego_indice'] += 1
                        st.session_state['fase_pregunta'] = 'respondiendo'
                    else:
                        st.session_state['juego_terminado'] = True
                    st.rerun()
                else:
                    # MODO GUIADO: entra en fase de feedback
                    st.session_state['fase_pregunta'] = 'feedback'
                    st.rerun()
            # --- End Respuesta Handler ---

            # Mapeo de opciones a botones
            opcion_letras = ['A', 'B', 'C', 'D']
            cols = [col_opt1, col_opt2]
            
            for i in range(len(opciones)):
                col = cols[i % 2]
                with col:
                    # Usamos el texto de la opción completa como clave para el botón
                    if st.button(f"{opcion_letras[i]}) {opciones[i]}", use_container_width=True, key=f"btn_opt_{i}_{idx}"): 
                        responder(opciones[i])
        
        elif fase == 'feedback':
            # LÓGICA DE FEEDBACK (Solo para modo Guiado)
            tipo, valor = st.session_state['ultimo_feedback'].split("|")
            
            # Contenedor de feedback
            if tipo == "correcta":
                feedback_html = f"""
                    <div class="feedback-correct">
                        🎉 ¡CORRECTO! <br> 
                        <span style="font-size: 30px">Has ganado +{valor} puntos</span>
                    </div>
                """
            else:
                feedback_html = f"""
                    <div class="feedback-incorrect">
                        ❌ INCORRECTO <br> 
                        <span style="font-size: 30px; color: #333;">La respuesta era: {valor}</span>
                    </div>
                """
            st.markdown(feedback_html, unsafe_allow_html=True)
            
            # Botón Siguiente Pregunta
            col_next1, col_next2, col_next3 = st.columns([1, 2, 1])
            with col_next2:
                if st.button("➡️ SIGUIENTE PREGUNTA", type="primary", use_container_width=True, key="btn_next_q"):
                    if st.session_state['juego_indice'] < len(preguntas) - 1:
                        st.session_state['juego_indice'] += 1
                        st.session_state['fase_pregunta'] = 'respondiendo'
                    else:
                        st.session_state['juego_terminado'] = True
                    st.rerun()

    elif st.session_state.get('juego_terminado', False):
        # LÓGICA DE PANTALLA FINAL
        puntaje = int(st.session_state['juego_puntaje'])
        
        # Intentamos guardar el resultado del juego en Firestore
        # NOTA: Llamamos a la función de guardado aquí, inmediatamente después de que se confirma el juego_terminado
        if st.session_state.get('juego_guardado', False) is False:
             # Necesitamos que la función guardar_juego_trivia sea definida y esté disponible
             # Asumiendo la disponibilidad global:
             if 'guardar_juego_trivia' in globals():
                 try:
                     # El resultado del guardado se maneja dentro de la función
                     guardar_juego_trivia(puntaje)
                     st.session_state['juego_guardado'] = True
                 except Exception as e:
                     st.error(f"Error al intentar guardar el juego: {e}")
             else:
                 st.warning("Función de guardado no disponible. El resultado no se guardará.")
        
        st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #2c3e50;'>PUNTAJE FINAL: {puntaje}</h1>", unsafe_allow_html=True)
        col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])
        with col_center:
            if puntaje == 100:
                st.balloons()
                st.markdown("""<div style="text-align: center; font-size: 120px;">🏆</div>""", unsafe_allow_html=True)
                st.success("¡MAESTRO TOTAL! 🌟")
                st.markdown("<p style='text-align: center; font-size: 20px;'>¡Respondiste todas las preguntas correctamente!</p>", unsafe_allow_html=True)
            elif puntaje >= 60:
                st.snow()
                st.markdown("""<div style="text-align: center; font-size: 120px;">😎</div>""", unsafe_allow_html=True)
                st.info("¡Bien hecho! Aprobado. Un poco más de práctica y serás un experto.")
            else:
                st.markdown("""<div style="text-align: center; font-size: 120px;">📚</div>""", unsafe_allow_html=True)
                st.warning("¡Buen intento! A repasar un poco más el tema. Siempre puedes generar otro juego.")

            # Botón Nuevo Juego vuelve al menú de fuentes
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Nuevo Juego", type="primary", use_container_width=True):
                # Limpiamos todos los estados de juego y volvemos al menú de fuentes
                for key in ['juego_preguntas', 'juego_terminado', 'juego_indice', 'juego_puntaje', 'juego_en_lobby', 'tema_actual', 'modo_avance', 'fase_pregunta', 'trivia_source', 'preguntas_manuales', 'ultimo_feedback', 'manual_num_select', 'manual_grado_select', 'manual_area_select', 'juego_guardado']:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Volvemos al menú de fuentes
                if 'volver_menu_fuentes_trivia' in globals():
                    volver_menu_fuentes_trivia()
                else:
                    st.session_state['vista_actual'] = 'menu_fuentes_trivia'
                    st.rerun()

# ------------------------------------------------------------
# F.1. FUNCIÓN DE GUARDADO FIREBASE/FIRESTORE (NUEVO CÓDIGO)
# ------------------------------------------------------------
def guardar_juego_trivia(puntaje_final):
    """Guarda el resultado del juego de Trivia en Firestore."""
    
    # Simulación de la inicialización de Firebase y Auth
    # En un entorno real de Streamlit, estas variables (db, auth, appId, userId)
    # deberían estar disponibles globalmente o ser pasadas como argumentos.
    # Aquí asumimos que las funciones y variables están disponibles para la simulación
    # del entorno Canvas (aunque se use Streamlit).

    # **Asunción Clave:** Las funciones de Firebase wrapper (db, auth) están disponibles.
    # Por seguridad, no simularemos aquí la lógica completa de Firebase/Auth en Python,
    # sino el punto de llamada para el guardado de datos.
    
    # Las variables de sesión ya contienen la información necesaria:
    tema = st.session_state.get('tema_actual', 'Tema Desconocido')
    source = st.session_state.get('trivia_source', 'Fuente Desconocida')
    num_preguntas = len(st.session_state.get('juego_preguntas', []))
    
    # Si el origen fue manual, usamos los datos de Grado y Área guardados
    if source == 'Elaboración manual':
        grado = st.session_state.get('manual_grado', 'N/A')
        area = st.session_state.get('manual_area', 'N/A')
    # Si el origen fue IA-Tutor, asumimos que están implícitos en el tema/prompt
    # En un caso ideal, se guardarían en session_state['ia_grado'] y ['ia_area']
    else:
        # Aquí usaríamos el valor por defecto o el último seleccionado
        # Para evitar errores, simplemente se usaría la información disponible
        grado = st.session_state.get('manual_grado_select', 'N/A') # Si viene de IA, usamos el valor del selector de IA (que no se guarda aquí)
        area = st.session_state.get('manual_area_select', 'N/A') # Mismo caso que arriba

    # Estructura del documento a guardar
    datos_juego = {
        'timestamp': time.time(), # Marca de tiempo para el orden
        'tema': tema,
        'puntaje_final': puntaje_final,
        'num_preguntas': num_preguntas,
        'origen': source,
        'modo_avance': st.session_state.get('modo_avance', 'auto'),
        'grado': grado,
        'area': area,
        'es_trivia': True # Marcador de tipo de juego
    }

    # --- SIMULACIÓN DE LLAMADA A FIRESTORE ---
    # En un entorno Streamlit con acceso a Firebase (como el que estamos simulando en Canvas),
    # la llamada sería a una función wrapper:
    
    # st.session_state['db'].collection('artifacts').document(appId).collection('users').document(userId).collection('trivia_scores').add(datos_juego)
    
    # Dado que no tenemos el SDK real aquí, simulamos el mensaje de éxito en la consola
    print(f"✅ [FIRESTORE SIMULACIÓN] Guardado exitoso. Puntaje: {puntaje_final}. Tema: {tema}")
    # Nota: No mostramos un mensaje de éxito en la UI para no interrumpir la pantalla final.
    # El estado 'juego_guardado' evita reintentos.

# Nota: La función 'guardar_juego_trivia' no necesita retornar nada.
# Se activa en la lógica de 'mostrar_juego_trivia' cuando 'juego_terminado' es True.

# ------------------------------------------------------------
# G. PÁGINA: BIBLIOTECA DE JUEGOS (IMPLEMENTACIÓN COMPLETA)
# ------------------------------------------------------------
def mostrar_biblioteca():
    """Muestra el historial y la biblioteca de juegos personales y globales."""
    
    # Encabezado con estilo
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("🔙 Inicio", use_container_width=True, key="btn_volver_menu_biblioteca"):
            # navegar_a('home') # Asumimos esta función existe
            st.session_state['pagina_actual'] = 'home'
            st.rerun()
            
    with col_title:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #FF8F00; font-size: 32px; font-weight: 900;">📚 BIBLIOTECA DE JUEGOS</h2>
            <p style="color: #616161; font-size: 16px;">Carga o comparte juegos de Trivia con tus compañeros.</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # --- 1. COLECCIÓN PERSONAL ---
    st.subheader("👤 Mi Colección Personal")
    
    # Llama a la utilidad de carga (inicia el onSnapshot simulado)
    obtener_juegos_trivia_usuario() 
    
    # Manejo del estado de carga
    is_loading = st.session_state.get('is_loading_library', False)
    juegos = st.session_state.get('juegos_biblioteca')
    
    if is_loading or juegos is None:
        st.info("Cargando tu historial de juegos...", icon="⏳")
        if is_loading:
             # st.progress(50) # Si quisiéramos mostrar una barra de progreso
             pass
             
    elif not juegos:
        st.warning("Aún no tienes juegos de Trivia guardados. ¡Ve al 'Generador IA' para crear el primero!")
        if st.button("Crear Nueva Trivia", key="btn_crear_desde_biblioteca"):
            # navegar_a('generador_ia') # Asumimos esta función existe
            st.session_state['pagina_actual'] = 'generador_ia'
            st.rerun()
            
    else:
        # 3. Mostrar la lista de juegos personales cargados
        st.markdown(f"**{len(juegos)}** Juegos guardados.")
        st.markdown("---")
        
        for game in juegos:
            doc_id = game.get('doc_id', 'N/A')
            titulo = game.get('titulo', 'Sin Título')
            config = game.get('configuracion', {})
            num_preguntas = config.get('num_preguntas', '??')
            area = config.get('area', 'General')
            
            # Formatear el timestamp simulado (que es un float)
            try:
                created_at = time.strftime('%d/%m/%Y %H:%M', time.localtime(game.get('created_at', 0)))
            except Exception:
                created_at = "Fecha N/A"

            # Layout con columnas para la presentación del juego
            col_title, col_details, col_action = st.columns([4, 3, 2])
            
            with col_title:
                st.markdown(f"**{titulo}**")
                st.caption(f"Grado: {config.get('grado', 'N/A')}")
            
            with col_details:
                st.markdown(f"**{num_preguntas}** preguntas")
                st.caption(f"Área: {area} | Creado: {created_at}")

            with col_action:
                # Botón de acción principal
                if st.button("🕹️ Jugar", key=f"play_personal_{doc_id}", use_container_width=True, type='primary'):
                    # Cargamos el juego en el estado de sesión y navegamos a la pantalla de juego
                    st.session_state['juego_preguntas'] = game.get('preguntas', [])
                    st.session_state['tema_actual'] = titulo
                    st.session_state['juego_iniciado'] = True
                    st.session_state['juego_en_lobby'] = True # Aseguramos que inicie en lobby
                    st.session_state['juego_indice'] = 0
                    st.session_state['juego_puntaje'] = 0.0
                    st.session_state['juego_terminado'] = False
                    # navegar_a('juego')
                    st.session_state['pagina_actual'] = 'juego'
                    st.rerun()
            
            st.markdown("---")

    # --- 2. COLECCIÓN GLOBAL (IMPLEMENTACIÓN ACTUALIZADA) ---
    st.subheader("🌎 Juegos Compartidos (Global)")
    
    # Llama a la utilidad de carga de juegos globales (onSnapshot simulado)
    obtener_juegos_trivia_globales() 
    
    # Manejo del estado de carga global
    is_loading_global = st.session_state.get('is_loading_library_global', False)
    juegos_globales = st.session_state.get('juegos_biblioteca_global')
    
    if is_loading_global or juegos_globales is None:
        st.info("Cargando juegos compartidos por la comunidad...", icon="⏳")
             
    elif not juegos_globales:
        st.info("Aún no hay juegos compartidos en la biblioteca global. ¡Sé el primero en compartir uno!")
            
    else:
        # Mostrar la lista de juegos globales cargados
        st.markdown(f"**{len(juegos_globales)}** Juegos compartidos disponibles.")
        st.markdown("---")
        
        for game in juegos_globales:
            doc_id = game.get('doc_id', 'N/A')
            titulo = game.get('titulo', 'Sin Título')
            config = game.get('configuracion', {})
            num_preguntas = config.get('num_preguntas', '??')
            area = config.get('area', 'General')
            
            # Formatear el timestamp
            try:
                created_at = time.strftime('%d/%m/%Y %H:%M', time.localtime(game.get('created_at', 0)))
            except Exception:
                created_at = "Fecha N/A"

            # Layout con columnas para la presentación del juego
            col_title, col_details, col_action = st.columns([4, 3, 2])
            
            with col_title:
                # Muestra el título y un fragmento del ID del creador
                creator_id_snippet = game.get('creator_id', 'Desconocido')[:8]
                st.markdown(f"**{titulo}**")
                st.caption(f"Creador: {creator_id_snippet}... | Grado: {config.get('grado', 'N/A')}")
            
            with col_details:
                st.markdown(f"**{num_preguntas}** preguntas")
                st.caption(f"Área: {area} | Creado: {created_at}")

            with col_action:
                # Botón de acción principal para juegos globales (color secundario)
                if st.button("🕹️ Jugar", key=f"play_global_{doc_id}", use_container_width=True, type='secondary'):
                    # Cargamos el juego en el estado de sesión y navegamos a la pantalla de juego
                    st.session_state['juego_preguntas'] = game.get('preguntas', [])
                    st.session_state['tema_actual'] = titulo
                    st.session_state['juego_iniciado'] = True
                    st.session_state['juego_en_lobby'] = True 
                    st.session_state['juego_indice'] = 0
                    st.session_state['juego_puntaje'] = 0.0
                    st.session_state['juego_terminado'] = False
                    # navegar_a('juego')
                    st.session_state['pagina_actual'] = 'juego'
                    st.rerun()
            
            st.markdown("---")
            
    # Muestra el ID de usuario para referencia de debug/compartir
    st.caption(f"ID de Usuario (para Firestore): **{st.session_state.get('userId', 'No Autenticado')}**")


# ============================================================
# === 3. JUEGO AHORCADO (ROBOT)
# ============================================================

def juego_ahorcado(volver_menu_juegos):

    import streamlit as st
    import time
    import pedagogical_assistant  # Import correcto, ya confirmado

    # 4. JUEGO ROBOT (AHORCADO - VERSIÓN HÍBRIDA: CONFIGURACIÓN ORIGINAL + MEJORAS)
    if st.session_state['juego_actual'] == 'ahorcado':
        
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
            section[data-testid="stMain"] div.stButton > button {
                width: 100%;
                height: 85px !important;
                background-color: white !important;
                border: 3px solid #1E88E5 !important;
                border-radius: 15px !important;
                margin-bottom: 10px !important;
                padding: 0px !important;
                box-shadow: 0 5px 0 #1565C0 !important;
            }

            section[data-testid="stMain"] div.stButton > button p {
                font-size: 45px !important;
                font-weight: 900 !important;
                color: #0D47A1 !important;
                line-height: 1 !important;
            }

            section[data-testid="stMain"] div.stButton > button:hover:enabled {
                transform: translateY(-2px);
                background-color: #E3F2FD !important;
            }
            
            section[data-testid="stMain"] div.stButton > button:active:enabled {
                transform: translateY(4px);
                box-shadow: none !important;
            }

            div.stButton > button[kind="primary"] p { 
                color: white !important; 
                font-size: 20px !important; 
            }
            div.stButton > button[kind="primary"] {
                background-color: #FF5722 !important;
                border-color: #E64A19 !important;
            }

            section[data-testid="stMain"] div.stButton > button:disabled {
                background-color: #CFD8DC !important;
                border-color: #B0BEC5 !important;
                opacity: 0.6 !important;
                box-shadow: none !important;
                transform: translateY(4px);
            }

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

        # --- CONFIGURACIÓN ---
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
            alerta_placeholder = st.empty()
            contenedor_audio = st.empty()

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
                    st.session_state['robot_errors'] = 0
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
                        
                        if letra in palabra:
                            t_stamp = time.time()
                            contenedor_audio.markdown(f"""<audio autoplay style="display:none;"><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3?t={t_stamp}"></audio>""", unsafe_allow_html=True)
                            time.sleep(0.2)
                        else:
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

def juego_sorteador(volver_menu_juegos):
    import streamlit as st

    # 5. JUEGO SORTEADOR (ETAPA 2: CARGA DE DATOS)
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


# ------------------------------------------------------------
# H. FUNCIONES STUB para otros juegos
# ------------------------------------------------------------
def juego_pupiletras(volver_menu_juegos):
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("🔙 Menú", use_container_width=True): volver_menu_juegos()
    st.title("🔤 Pupiletras (Pendiente)")
    st.info("Aquí iría la lógica del Pupiletras.")

def juego_ahorcado(volver_menu_juegos):
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("🔙 Menú", use_container_width=True): volver_menu_juegos()
    st.title("🤖 Robot - Ahorcado (Pendiente)")
    st.info("Aquí iría la lógica del Ahorcado/Robot.")

def juego_sorteador(volver_menu_juegos):
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("🔙 Menú", use_container_width=True): volver_menu_juegos()
    st.title("🎰 Sorteador (Pendiente)")
    st.info("Aquí iría la lógica del Sorteador.")

# ============================================================
# I. FUNCIÓN PRINCIPAL: ROUTER
# ============================================================

def gamificacion():
    """
    Función principal que gestiona el enrutamiento (routing) de las diferentes vistas del arcade.
    """
    
    # 1. GESTIÓN DE ESTADO (Asegurando el estado inicial)
    if 'juego_actual' not in st.session_state:
        # Inicializa a None para mostrar el menú principal
        st.session_state['juego_actual'] = None    
    
    # 2. RENDERIZADO DE VISTAS
    if st.session_state['juego_actual'] is None:
        # Menú principal de juegos (D)
        mostrar_menu_juegos()

    elif st.session_state['juego_actual'] == 'trivia_fuentes':
        # Menú para seleccionar la fuente de Trivia (E)
        mostrar_menu_fuentes_trivia()

    elif st.session_state['juego_actual'] == 'trivia_ia_tutor':
        # Generación de Trivia usando IA-Tutor (F - Subsección IA)
        mostrar_generador_ia_tutor()

    # **CORRECCIÓN CLAVE AQUÍ:** Se cambió 'trivia_elaboracion_manual' por 
    # 'trivia_configuracion_manual' para coincidir con el valor seteado en la Sección E.
    elif st.session_state['juego_actual'] == 'trivia_configuracion_manual':
        # Formulario Manual Puro (F - Subsección Manual)
        mostrar_formulario_manual()

    elif st.session_state['juego_actual'] == 'trivia_jugar':
        # Vista de juego (F - Jugar)
        mostrar_juego_trivia()

    # Placeholders para otros juegos o etapas
    elif st.session_state['juego_actual'] == 'pupiletras':
        st.header("🔤 Pupiletras (Próximamente)")
        st.button("↩️ Volver al Menú Juegos", on_click=volver_menu_juegos, type="secondary")

    elif st.session_state['juego_actual'] == 'robot':
        st.header("🤖 Robot (Próximamente)")
        st.button("↩️ Volver al Menú Juegos", on_click=volver_menu_juegos, type="secondary")

    elif st.session_state['juego_actual'] == 'sorteador':
        st.header("🎰 Sorteador (Próximamente)")
        st.button("↩️ Volver al Menú Juegos", on_click=volver_menu_juegos, type="secondary")
        
    elif st.session_state['juego_actual'] == 'biblioteca':
        # Nueva página: Biblioteca (G)
        mostrar_menu_biblioteca()

# Ejecutar la función principal si el archivo se ejecuta directamente
if __name__ == '__main__':
    gamificacion()
