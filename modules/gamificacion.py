import streamlit as st
import json
import random
import time
import pandas as pd
import pedagogical_assistant

from streamlit_lottie import st_lottie  # Solo si lo usas
import base64  # Solo si algún juego lo usa
import os  # Solo si se usa en algún juego
# Importaciones de Firebase (Necesarias para la persistencia)
try:
    from firebase_admin import initialize_app, credentials
    from firebase_admin import firestore, auth
    from google.cloud.firestore import Client as FirestoreClient
except ImportError:
    # Estos imports son necesarios para el entorno de ejecución, 
    # si fallan, se asume que Streamlit se está ejecutando en Canvas 
    # y los módulos ya están cargados.
    pass 

# ============================================================
#   MÓDULO DE GAMIFICACIÓN – VERSIÓN ORGANIZADA
# ============================================================


# ============================================================
#   A. CONFIGURACIÓN E INICIALIZACIÓN DE FIREBASE/AUTH (NUEVO)
# ============================================================

def initialize_firebase():
    """Inicializa Firebase, Firestore y autentica al usuario."""
    # Solo ejecutar la inicialización una vez
    if 'db' in st.session_state and 'auth' in st.session_state and 'is_auth_ready' in st.session_state and st.session_state.is_auth_ready:
        return
    
    try:
        # Intenta obtener la configuración y el token de las variables globales de Canvas
        firebase_config = json.loads(os.environ.get('__firebase_config', '{}'))
        initial_auth_token = os.environ.get('__initial_auth_token')
        app_id = os.environ.get('__app_id', 'default-app-id')

        # Si la configuración existe, procedemos con la inicialización.
        if firebase_config:
            import firebase_admin
            from firebase_admin import initialize_app, credentials
            from firebase_admin import firestore, auth

            # La app solo debe inicializarse una vez
            if not firebase_admin._apps:
                # Usar el objeto de configuración para inicializar
                cred = credentials.Certificate(firebase_config)
                app = initialize_app(cred)
            else:
                app = firebase_admin.get_app()
                
            db = firestore.client(app)
            firebase_auth = auth
            
            # Autenticación con el token
            if initial_auth_token:
                try:
                    # Verifica el token y obtiene el ID de usuario
                    decoded_token = firebase_auth.verify_id_token(initial_auth_token)
                    user_id = decoded_token['uid']
                    st.session_state['userId'] = user_id
                    st.session_state['is_authenticated'] = True
                except Exception as e:
                    st.warning(f"Error al verificar token: {e}. Usando ID anónimo.")
                    st.session_state['userId'] = "anonymous_" + os.urandom(16).hex()
                    st.session_state['is_authenticated'] = False
            else:
                # Fallback para usuarios anónimos o desarrollo local
                st.session_state['userId'] = "anonymous_" + os.urandom(16).hex()
                st.session_state['is_authenticated'] = False

            # Guardar en el estado de sesión para Streamlit
            st.session_state['db'] = db
            st.session_state['auth'] = firebase_auth
            st.session_state['appId'] = app_id
            st.session_state['is_auth_ready'] = True
            
            # print(f"Firebase Inicializado. UserId: {st.session_state.userId}, AppId: {app_id}")

        else:
            # Caso de desarrollo local sin configuración de Firebase
            st.session_state['db'] = None
            st.session_state['auth'] = None
            st.session_state['appId'] = 'default-app-id'
            st.session_state['userId'] = 'offline-user-id'
            st.session_state['is_auth_ready'] = True
            st.warning("⚠️ Ejecutando sin conexión a Firebase. Los datos no se guardarán.")

    except Exception as e:
        st.error(f"FALLO CRÍTICO DE FIREBASE/AUTH: {e}")
        st.session_state['is_auth_ready'] = False
        st.session_state['db'] = None

# ============================================================
#   B. GESTIÓN DE ESTADO Y UTILIDADES DE FIREBASE (NUEVO)
# ============================================================

# Define las rutas de Firestore
def get_personal_collection_ref():
    if not st.session_state.get('db'): return None
    appId = st.session_state.get('appId', 'default-app-id')
    userId = st.session_state.get('userId', 'offline-user-id')
    
    # Ruta: /artifacts/{appId}/users/{userId}/trivia_games
    return st.session_state.db.collection(f"artifacts").document(appId).collection("users").document(userId).collection("trivia_games")

def get_global_collection_ref():
    if not st.session_state.get('db'): return None
    appId = st.session_state.get('appId', 'default-app-id')
    
    # Ruta: /artifacts/{appId}/public/data/trivia_games
    return st.session_state.db.collection(f"artifacts").document(appId).collection("public").document("data").collection("trivia_games")


def guardar_juego_trivia(game_data, is_public=False):
    """
    Guarda el juego de trivia en Firestore.
    :param game_data: Diccionario con la estructura del juego.
    :param is_public: Booleano, si es True, guarda en la biblioteca global.
    """
    if not st.session_state.get('is_auth_ready') or not st.session_state.get('db'):
        st.error("No se puede guardar: Firebase no está inicializado o la autenticación falló.")
        return False

    collection_ref = get_global_collection_ref() if is_public else get_personal_collection_ref()
    
    if collection_ref is None:
        st.error("Error al obtener la referencia de la colección.")
        return False
        
    try:
        # Añade metadatos antes de guardar
        game_data['creator_id'] = st.session_state.get('userId', 'anonymous')
        game_data['created_at'] = firestore.SERVER_TIMESTAMP
        game_data['is_public'] = is_public
        
        # Firestore no soporta diccionarios anidados con listas de listas/objetos complejos.
        # Guardaremos el juego como un diccionario simple o como un campo JSON STRING si es complejo.
        # Asumo que game_data es un dict simple aquí.
        collection_ref.add(game_data)
        return True
    except Exception as e:
        st.error(f"Error al guardar el juego en Firestore: {e}")
        return False

# ============================================================
#   C. GESTIÓN DE ESTADO GENERAL Y MENÚS DE NAVEGACIÓN
# ============================================================

def volver_menu_juegos():
    """Vuelve al menú principal de juegos y limpia estados de sub-menú."""
    st.session_state['juego_actual'] = None
    if 'trivia_source' in st.session_state:
        del st.session_state['trivia_source']
    st.rerun()

def volver_menu_fuentes_trivia():
    """Vuelve al menú de selección de fuentes de Trivia."""
    st.session_state['juego_actual'] = 'trivia_fuentes'
    if 'trivia_source' in st.session_state:
        del st.session_state['trivia_source']
    # También reseteamos el juego por si estaba a medio generar
    st.session_state['juego_iniciado'] = False
    st.rerun()

# ------------------------------------------------------------
# D. MENÚ PRINCIPAL DE JUEGOS (MODIFICADO para añadir BIBLIOTECA)
# ------------------------------------------------------------
def mostrar_menu_juegos():

    # 1. CSS 
    st.markdown("""
    <style>
        /* Estilos principales de los botones del menú de juegos */
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
        }
        /* Estilo específico para el botón de Biblioteca */
        #btn_card_biblioteca button {
            background: linear-gradient(135deg, #fbc02d 0%, #ff8f00 100%) !important;
            box-shadow: 0 10px 20px rgba(255, 143, 0, 0.3) !important;
        }
         #btn_card_biblioteca button:hover {
            background: linear-gradient(135deg, #ff8f00 0%, #fbc02d 100%) !important;
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

    # 3. Botones - Layout con 3 columnas en la primera fila (para 5 botones)
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
        # NUEVO BOTÓN: BIBLIOTECA
        if st.button("📚 BIBLIOTECA\n\nGuardar y Compartir", key="btn_card_biblioteca", use_container_width=True):
            st.session_state['juego_actual'] = 'biblioteca'
            st.rerun()

    st.write("")
    
    col4, col5, col_spacer = st.columns(3, gap="large")

    with col4:
        if st.button("🤖 ROBOT\n\nLógica & Deducción", key="btn_card_robot", use_container_width=True):
            st.session_state['juego_actual'] = 'ahorcado'
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
        if st.button("🔙 Menú Juegos", use_container_width=True, key="btn_volver_menu_fuentes"):
            volver_menu_juegos()
    with col_title:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #4CAF50; font-size: 32px; font-weight: 900;">🧠 SELECCIONA LA FUENTE DE TRIVIA</h2>
            <p style="color: #616161; font-size: 16px;">¿De dónde quieres que la IA extraiga el conocimiento?</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    
    # 3. Opciones de Fuente (En columnas para mejor layout)
    col1, col2, col3 = st.columns(3, gap="medium")

    def set_source_and_continue(source):
        st.session_state['juego_actual'] = 'trivia'
        st.session_state['trivia_source'] = source
        st.rerun()

    with col1:
        # Elaboración manual
        if st.button("📝 Elaboración manual\n\n(Crea tus preguntas)", use_container_width=True, key="source_manual", help="Introduce o pega tu propio texto de contenido para crear el juego a partir de él."):
            set_source_and_continue('Manual') 
    
    with col2:
        # Archivo PDF/TXT - DESHABILITADO
        if st.button("📁 Archivo PDF/TXT\n\n(Próximamente)", use_container_width=True, key="source_archivo", disabled=True, help="Sube un documento y la IA lo analizará."):
            pass 
    
    with col3:
        # Uso de IA-Tutor
        if st.button("🌐 Uso de IA-Tutor\n\n(Crea preguntas con IA)", use_container_width=True, key="source_ia_tutor", help="Deja que la IA busque un tema general en Internet y genere un juego educativo automáticamente."):
            set_source_and_continue('IA-Tutor')

    # Aplicamos el estilo a los botones recién creados
    st.markdown("""
    <script>
        document.querySelectorAll('button[key^="source_"]').forEach(function(button) {
            button.classList.add('source-button');
        });
    </script>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# F. JUEGO 1: TRIVIA
# ------------------------------------------------------------
def juego_trivia(volver_menu_juegos):

    # Verifica si estamos en la configuración del juego o si ya hay un juego cargado
    trivia_source = st.session_state.get('trivia_source')

    # ... (El resto de la función juego_trivia, incluyendo el CSS y la lógica, permanece igual 
    # excepto que ahora el botón "Nuevo Juego" debería volver a 'trivia_fuentes' y no a 'juego_actual=None').
    
    # Barra superior
    col_back, col_title = st.columns([1, 5])
    with col_back:
        # Botón vuelve al menú de fuentes de trivia si estamos en la fase de configuración
        if st.session_state.get('juego_iniciado', False) or st.session_state.get('juego_en_lobby', False):
             if st.button("🔙 Menú Fuentes", use_container_width=True, key="btn_volver_menu"):
                # Si el juego ya está iniciado/cargado, volvemos al menú principal
                volver_menu_juegos()
        else:
             if st.button("🔙 Fuentes", use_container_width=True, key="btn_volver_menu"):
                volver_menu_fuentes_trivia()

    with col_title:
        st.subheader(f"Desafío Trivia: {trivia_source if trivia_source else 'Configuración'}")


    # --- Resto del CSS del juego Trivia... (Tu CSS original) ---
    st.markdown("""
        <style>
        /* ... CSS Trivia ... */
        button[data-testid="baseButton-default"][id="btn_volver_menu"] {
            background-color: #fff59d !important;
            color: #1e3a8a !important;
            border: 2px solid #fbc02d !important;
            font-size: 14px !important;
            padding: 4px 10px !important;
            border-radius: 10px !important;
            box-shadow: 0px 3px 0px #f9a825 !important;
        }

        button[data-testid="baseButton-default"][id="btn_volver_menu"]:hover {
            background-color: #fff176 !important;
            transform: translateY(-2px);
        }
        
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

    st.divider()

    # --- LÓGICA TRIVIA: FASE DE CONFIGURACIÓN ---
    if 'juego_iniciado' not in st.session_state or not st.session_state['juego_iniciado']:
        
        # ------------------------------------------------------------
        # 1. CAMPO DE ENTRADA DINÁMICO SEGÚN LA FUENTE 
        # ------------------------------------------------------------
        tema_input = None
        
        # CLAVE 'Manual'
        if trivia_source == 'Manual':
            st.markdown(f"**Fuente de la Trivia:** **<span style='color:#1b5e20;'>Elaboración manual</span>**", unsafe_allow_html=True)
            tema_input = st.text_area("Pega el texto fuente aquí:", height=200, placeholder="Ej: La biografía de Marie Curie, el resumen de la Segunda Guerra Mundial, etc. (Mínimo 50 caracteres)")
            
        # CLAVE 'IA-Tutor' 
        elif trivia_source == 'IA-Tutor':
            st.markdown(f"**Fuente de la Trivia:** **<span style='color:#1b5e20;'>Uso de IA-Tutor</span>**", unsafe_allow_html=True)
            tema_input = st.text_input("Tema General:", placeholder="Ej: La Célula, La Revolución Francesa, Álgebra...")
            
        elif trivia_source is None:
            st.warning("⚠️ Debes seleccionar una fuente de Trivia primero.")
            st.stop()
            
        # ------------------------------------------------------------
        # 2. CONFIGURACIÓN GENERAL Y GENERACIÓN
        # ------------------------------------------------------------
        col_game1, col_game2 = st.columns([2, 1])
        with col_game1:
            lista_grados = ["1° Primaria", "2° Primaria", "3° Primaria", "4° Primaria", "5° Primaria", "6° Primaria", "1° Secundaria", "2° Secundaria", "3° Secundaria", "4° Secundaria", "5° Secundaria"]
            grado_input = st.selectbox("Nivel Educativo (Grado):", lista_grados, index=6)
        with col_game2:
            num_input = st.slider("Número de Preguntas:", 1, 10, 5)
            modo_avance = st.radio("Modo de Juego:", ["Automático (Rápido)", "Guiado por Docente (Pausa)"])

        # BOTÓN GENERAR
        if st.button("🎲 Generar Juego", type="primary", use_container_width=True):
            
            is_text_too_short = (trivia_source == 'Manual' and (not tema_input or len(tema_input) < 50))
            is_topic_missing = (trivia_source == 'IA-Tutor' and not tema_input)

            if is_text_too_short or is_topic_missing:
                st.warning(f"⚠️ Por favor, introduce un tema válido o pega un texto de al menos 50 caracteres para la fuente.")
            else:
                intentos = 0
                max_intentos = 3
                exito = False
                
                while intentos < max_intentos and not exito:
                    intentos += 1
                    try:
                        msg_intento = f"🧠 Creando desafíos desde {trivia_source}..." if intentos == 1 else f"⚠️ Ajustando formato (Intento {intentos}/{max_intentos})..."
                        
                        with st.spinner(msg_intento):
                            respuesta_json = pedagogical_assistant.generar_trivia_juego(tema_input, grado_input, trivia_source, num_input)
                            
                            if respuesta_json:
                                clean_json = respuesta_json.replace('```json', '').replace('```', '').strip()
                                preguntas = json.loads(clean_json)
                                
                                # GUARDAMOS LA ESTRUCTURA DEL JUEGO
                                st.session_state['juego_preguntas'] = preguntas
                                st.session_state['juego_indice'] = 0
                                st.session_state['juego_puntaje'] = 0
                                st.session_state['juego_terminado'] = False
                                st.session_state['tema_actual'] = tema_input
                                st.session_state['modo_avance'] = "auto" if "Automático" in modo_avance else "guiado"
                                st.session_state['fase_pregunta'] = "respondiendo"
                                
                                st.session_state['juego_en_lobby'] = True
                                st.session_state['juego_iniciado'] = True
                                
                                exito = True
                                st.rerun()
                            else:
                                raise Exception("Respuesta vacía de la IA")

                    except json.JSONDecodeError:
                        time.sleep(1)
                        continue
                        
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")
                        break
                
                if not exito:
                    st.error("❌ La IA está teniendo dificultades con este tema específico. Por favor, intenta cambiar ligeramente el nombre del tema o el texto fuente.")

    # --- LÓGICA TRIVIA: FASE DE LOBBY / JUEGO ACTIVO / TERMINADO (Sin cambios) ---
    
    # ... Lógica de Lobby, Activo y Terminado (Se mantiene igual)

    elif st.session_state.get('juego_en_lobby', False):
        # LÓGICA DE LOBBY
        tema_mostrar = st.session_state.get('tema_actual', 'Trivia')
        modo_mostrar = "Modo Automático" if st.session_state.get('modo_avance') == "auto" else "Modo Guiado (Pausa)"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 40px; background-color: white; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h1 style="font-size: 70px; color: #28a745; margin: 0;">🏆 TRIVIA TIME 🏆</h1>
            <h2 style="color: #555; font-size: 30px; margin-top: 10px;">Tema: {tema_mostrar[:50]}...</h2>
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
            
            def responder(opcion_elegida):
                import time
                
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
                    
                    time.sleep(2.0)
                    
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
            # LÓGICA DE FEEDBACK
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
        # LÓGICA DE PANTALLA FINAL
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
                # Limpiamos todos los estados de juego y volvemos al menú de fuentes
                for key in ['juego_preguntas', 'juego_terminado', 'juego_indice', 'juego_puntaje', 'juego_en_lobby', 'tema_actual', 'modo_avance', 'fase_pregunta', 'trivia_source']:
                    if key in st.session_state:
                        del st.session_state[key]
                volver_menu_juegos() # Volvemos al menú principal
                st.rerun()

# ------------------------------------------------------------
# G. NUEVA PÁGINA: BIBLIOTECA DE JUEGOS (ESQUELETO)
# ------------------------------------------------------------
def mostrar_menu_biblioteca():
    
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("🔙 Menú Juegos", use_container_width=True, key="btn_volver_menu_biblioteca"):
            volver_menu_juegos()
    with col_title:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #FF8F00; font-size: 32px; font-weight: 900;">📚 BIBLIOTECA DE JUEGOS</h2>
            <p style="color: #616161; font-size: 16px;">Carga o comparte juegos de Trivia con tus compañeros.</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- Secciones de la Biblioteca ---
    
    # Biblioteca Personal (Guardada en /artifacts/{appId}/users/{userId}/trivia_games)
    st.subheader("👤 Mi Colección Personal")
    st.info("Aquí verás los juegos que has guardado. Haz clic para cargarlos.")
    # TODO: Implementar la carga de datos de Firestore para la colección personal.

    # Biblioteca Global (Guardada en /artifacts/{appId}/public/data/trivia_games)
    st.subheader("🌎 Juegos Compartidos (Global)")
    st.info("Juegos creados y compartidos por la comunidad. ¡Carga uno y juega!")
    # TODO: Implementar la carga de datos de Firestore para la colección global.

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

# ------------------------------------------------------------
# I. FUNCIÓN PRINCIPAL: ROUTER
# ------------------------------------------------------------
def gamificacion():

    # 0. INICIALIZACIÓN CRÍTICA DE FIREBASE Y AUTH
    initialize_firebase()
    if not st.session_state.get('is_auth_ready', False):
        st.warning("Esperando la inicialización de la autenticación...")
        return

    # 1. Asegura estado inicial
    if "juego_actual" not in st.session_state:
        st.session_state["juego_actual"] = None

    # 2. Router
    if st.session_state["juego_actual"] is None:
        mostrar_menu_juegos()

    # Trivia: Seleccionar fuente
    elif st.session_state["juego_actual"] == "trivia_fuentes":
        mostrar_menu_fuentes_trivia()

    # Trivia: Juego activo/configuración
    elif st.session_state["juego_actual"] == "trivia":
        juego_trivia(volver_menu_juegos)

    # NUEVA PÁGINA DE BIBLIOTECA
    elif st.session_state["juego_actual"] == "biblioteca":
        mostrar_menu_biblioteca()

    # Otros juegos (stubs)
    elif st.session_state['juego_actual'] == 'pupiletras':
        juego_pupiletras(volver_menu_juegos)

    elif st.session_state['juego_actual'] == 'ahorcado':
        juego_ahorcado(volver_menu_juegos)

    elif st.session_state['juego_actual'] == 'sorteador':
        juego_sorteador(volver_menu_juegos)
