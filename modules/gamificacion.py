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
import uuid # Necesario para generar IDs anónimos

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
#   A. CONFIGURACIÓN E INICIALIZACIÓN
# ============================================================

# Inicialización de Firebase (Singleton)
def inicializar_firebase():
    """Inicializa la app de Firebase Admin si aún no ha sido inicializada."""
    if 'firebase_initialized' not in st.session_state:
        st.session_state['firebase_initialized'] = False

    if not st.session_state['firebase_initialized']:
        try:
            # 1. Usar el JSON de configuración para crear credenciales
            config = json.loads(FIREBASE_CONFIG_JSON)
            
            # El SDK Admin usa 'credentials.Certificate', no la configuración simple
            # Esto asume que FIREBASE_CONFIG_JSON contiene las credenciales de servicio.
            
            # --- Simplificación para entornos de ejecución que proveen Service Account ---
            cred_data = json.loads(FIREBASE_CONFIG_JSON)
            cred = credentials.Certificate(cred_data)
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'databaseURL': config.get('databaseURL')
                })
            
            st.session_state['db'] = firestore.client()
            st.session_state['firebase_initialized'] = True
            st.session_state['user_id'] = None # Se establecerá tras la autenticación
            
            st.success("✅ Firebase Admin SDK inicializado.")
            
        except Exception as e:
            st.warning(f"⚠️ Inicialización de Firebase Fallida (Admin SDK). Esto puede ser normal en entornos sin la Service Account. Error: {e}")
            st.session_state['db'] = None
            st.session_state['firebase_initialized'] = True # Para no reintentar

# Inicialización de Autenticación (Usuario anónimo/Canvas)
def inicializar_autenticacion():
    """Asegura que el usuario esté autenticado (vía Canvas Token o anónimamente)."""
    
    # Solo inicializamos la autenticación si Firebase Admin está listo
    if st.session_state.get('firebase_initialized') and st.session_state.get('db'):
        
        if 'auth_ready' not in st.session_state:
            st.session_state['auth_ready'] = False

        if not st.session_state['auth_ready']:
            try:
                # 1. Autenticar con el token de Canvas si existe
                if INITIAL_AUTH_TOKEN:
                    
                    # Usamos el token para obtener el ID del usuario
                    decoded_token = auth.verify_id_token(INITIAL_AUTH_TOKEN)
                    user_id = decoded_token['uid']
                    
                    st.session_state['user_id'] = user_id
                    st.session_state['auth_ready'] = True
                    st.success(f"🔒 Usuario Canvas autenticado: {user_id}")
                    return
                
                # 2. Autenticación Anónima (Fallback)
                else:
                    st.warning("⚠️ No se detectó token de Canvas. Usando ID Anónimo.")
                    
                    if 'anonymous_user_id' not in st.session_state:
                        # Creamos un ID anónimo persistente en la sesión
                        st.session_state['anonymous_user_id'] = f"anon-{uuid.uuid4().hex}"
                    
                    st.session_state['user_id'] = st.session_state['anonymous_user_id']
                    st.session_state['auth_ready'] = True
                    st.info(f"👤 ID Anónimo asignado: {st.session_state['user_id']}")
            
            except Exception as e:
                st.error(f"❌ Error en la autenticación: {e}")
                st.session_state['auth_ready'] = True # Para evitar bucles
                
# ============================================================
#   B. UTILIDADES Y LÓGICA DE TRIVIA
# ============================================================

def get_db():
    """Devuelve la instancia de Firestore o None si no está inicializada."""
    if st.session_state.get('db') is None:
        inicializar_firebase() # Intenta inicializar de nuevo si es necesario
    return st.session_state.get('db')

def get_user_id():
    """Devuelve el ID del usuario actual o None si no está autenticado."""
    if st.session_state.get('user_id') is None:
        inicializar_autenticacion() # Intenta autenticar de nuevo
    return st.session_state.get('user_id')

def get_private_collection_ref(collection_name):
    """Obtiene la referencia a una colección privada del usuario."""
    db = get_db()
    user_id = get_user_id()
    if db and user_id:
        return db.collection(f"artifacts/{APP_ID}/users/{user_id}/{collection_name}")
    return None

def get_public_collection_ref(collection_name):
    """Obtiene la referencia a una colección pública de la aplicación."""
    db = get_db()
    if db:
        return db.collection(f"artifacts/{APP_ID}/public/data/{collection_name}")
    return None

# --- Lógica de Guardado (CRUD) ---

def guardar_juego_trivia():
    """Guarda la configuración y las preguntas de la trivia en Firestore."""
    
    db = get_db()
    user_id = get_user_id()
    
    if not db or not user_id:
        st.error("No se puede guardar: Base de datos o autenticación no disponible.")
        return False

    if 'preguntas_trivia' not in st.session_state or not st.session_state['preguntas_trivia']:
        st.error("No hay preguntas generadas para guardar.")
        return False
        
    if 'trivia_config' not in st.session_state:
        st.error("Configuración de trivia no disponible.")
        return False

    # 1. Preparar el documento
    doc_data = {
        'user_id': user_id,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'config': st.session_state['trivia_config'],
        # Serializar preguntas a JSON para asegurar compatibilidad con Firestore
        'preguntas_json': json.dumps(st.session_state['preguntas_trivia']),
        'titulo': st.session_state['trivia_config']['titulo'],
        'area': st.session_state['trivia_config']['area'],
        'grado': st.session_state['trivia_config']['grado'],
        'modo': st.session_state['trivia_config']['modo']
    }

    # 2. Guardar en la colección privada
    try:
        coleccion = get_private_collection_ref('trivias')
        doc_ref = coleccion.add(doc_data)
        st.success(f"🎉 Trivia '{doc_data['titulo']}' guardada con éxito.")
        st.session_state['juego_guardado_id'] = doc_ref.id
        return True
    except Exception as e:
        st.error(f"Error al guardar la trivia: {e}")
        return False

# --- Lógica de Carga y Visualización ---

def cargar_trivias_usuario():
    """Carga todos los juegos de trivia guardados por el usuario."""
    db = get_db()
    if not db:
        return []
    
    try:
        coleccion = get_private_collection_ref('trivias')
        if coleccion is None:
            return [] # No hay autenticación
            
        docs = coleccion.order_by('timestamp', direction=firestore.Query.DESCENDING).get()
        
        trivias = []
        for doc in docs:
            data = doc.to_dict()
            # Deserializar preguntas si existen
            data['preguntas'] = json.loads(data.get('preguntas_json', '[]'))
            data['id'] = doc.id
            trivias.append(data)
        
        return trivias
    except Exception as e:
        st.error(f"Error al cargar trivias: {e}")
        return []

def cargar_trivias_globales():
    """Carga todos los juegos de trivia compartidos globalmente."""
    db = get_db()
    if not db:
        return []
    
    try:
        coleccion = get_public_collection_ref('trivias_globales')
        if coleccion is None:
            return []
            
        # Limitar la carga para evitar sobrecarga
        docs = coleccion.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).get()
        
        trivias = []
        for doc in docs:
            data = doc.to_dict()
            data['preguntas'] = json.loads(data.get('preguntas_json', '[]'))
            data['id'] = doc.id
            trivias.append(data)
        
        return trivias
    except Exception as e:
        st.error(f"Error al cargar trivias globales: {e}")
        return []

def seleccionar_trivia_para_jugar(trivia_doc):
    """Carga el juego de trivia seleccionado en el estado de sesión para jugarlo."""
    st.session_state['trivia_juego_seleccionado'] = {
        'id': trivia_doc.get('id'),
        'titulo': trivia_doc.get('titulo'),
        'preguntas': trivia_doc.get('preguntas'), # Ya deserializadas
        'config': trivia_doc.get('config', {})
    }
    st.session_state['juego_actual'] = 'trivia_jugar'
    st.session_state['trivia_paso'] = 0 # Iniciar el juego en la primera pregunta
    st.session_state['trivia_puntuacion'] = 0
    st.rerun()

# ============================================================
#   C. FUNCIONES DE RENDERIZADO Y NAVEGACIÓN
# ============================================================

def volver_menu_juegos():
    """Vuelve al menú principal de juegos y limpia el estado de navegación de trivia."""
    st.session_state['juego_actual'] = 'menu_juegos'
    # Limpia el estado específico de Trivia
    if 'trivia_config' in st.session_state:
        del st.session_state['trivia_config']
    if 'preguntas_trivia' in st.session_state:
        del st.session_state['preguntas_trivia']
    if 'juego_iniciado' in st.session_state:
        st.session_state['juego_iniciado'] = False
    
    st.rerun()

def volver_menu_fuentes_trivia():
    """Vuelve al menú de selección de fuentes de trivia."""
    st.session_state['juego_actual'] = 'trivia_fuentes'
    st.rerun()

def mostrar_menu_juegos():
    """D. Muestra el menú principal de selección de juegos (Arcade)."""
    st.title("🕹️ Selección de Juegos Educativos")
    
    st.markdown("---")
    
    # 1. Trivia (Generador)
    with st.container(border=True):
        st.subheader("🧠 Trivia Maker")
        st.markdown("Crea juegos de preguntas y respuestas automáticamente con IA o manualmente.")
        if st.button("Crear Trivia Nueva", key="btn_crear_trivia", use_container_width=True, type="primary"):
            st.session_state['juego_actual'] = 'trivia_fuentes'
            st.rerun()

    st.markdown("---")
    
    # 2. Biblioteca
    with st.container(border=True):
        st.subheader("📚 Mi Biblioteca")
        st.markdown("Accede a tus juegos de trivia guardados.")
        if st.button("Ir a la Biblioteca", key="btn_biblioteca", use_container_width=True):
            st.session_state['juego_actual'] = 'biblioteca'
            st.rerun()

    # 3. Juegos Globales
    with st.container(border=True):
        st.subheader("🌍 Juegos de la Comunidad")
        st.markdown("Juega trivias compartidas por otros usuarios.")
        if st.button("Explorar Juegos Globales", key="btn_globales", use_container_width=True):
            st.session_state['juego_actual'] = 'juegos_globales'
            st.rerun()

def mostrar_menu_fuentes_trivia():
    """E. Muestra el menú para seleccionar la fuente de la trivia (IA vs Manual)."""
    st.title("🧠 1. Elige la Fuente de la Trivia")
    st.markdown("Selecciona cómo deseas generar las preguntas para tu nuevo juego.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.subheader("🤖 Generación con IA Tutor")
            st.markdown("Describe el tema, y la IA generará preguntas y respuestas automáticas.")
            if st.button("Usar Generador IA", key="btn_ia_tutor", use_container_width=True, type="primary"):
                st.session_state['juego_actual'] = 'trivia_ia_tutor'
                st.rerun()

    with col2:
        with st.container(border=True):
            st.subheader("✍️ Configuración Manual")
            st.markdown("Introduce las preguntas y opciones una por una manualmente.")
            if st.button("Usar Formulario Manual", key="btn_manual", use_container_width=True):
                st.session_state['juego_actual'] = 'trivia_configuracion_manual'
                st.rerun()
                
    st.markdown("---")
    st.button("↩️ Volver al Menú Juegos", on_click=volver_menu_juegos, type="secondary")

# --- FUNCIONES F: CONFIGURACIÓN Y JUEGO ---

def generar_trivia_con_gemini(tema, grado, area, num_preguntas):
    """
    Llama a la API de Gemini para generar preguntas de trivia.
    Devuelve una lista de preguntas.
    """
    # 1. Configurar la llamada a la IA
    system_prompt = (
        f"Actúa como un profesor experto en {area} para el nivel {grado}. "
        "Tu tarea es generar preguntas de trivia de opción múltiple (4 opciones, 1 correcta) "
        "basadas en el tema proporcionado. El formato de salida debe ser JSON estricto."
    )
    user_prompt = (
        f"Genera {num_preguntas} preguntas de trivia sobre el siguiente tema: '{tema}'. "
        "Incluye la respuesta correcta y tres distractores por pregunta."
    )
    
    # 2. Definir el esquema de salida JSON (STRUCTURAL OUTPUT)
    response_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "pregunta": {"type": "STRING"},
                "opciones": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Las 4 opciones, incluyendo la correcta."
                },
                "respuesta_correcta": {"type": "STRING", "description": "El texto exacto de la opción correcta."}
            },
            "required": ["pregunta", "opciones", "respuesta_correcta"]
        }
    }
    
    # 3. Realizar la llamada usando el módulo asistencial
    try:
        st.session_state['is_generating'] = True
        
        # pedagogical_assistant debe contener la función para llamar a Gemini
        # Asumiendo que esta función está disponible globalmente
        json_response = pedagogical_assistant.call_gemini_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
            model_name="gemini-2.5-flash-preview-09-2025"
        )
        
        st.session_state['is_generating'] = False
        
        if json_response:
            return json.loads(json_response)
        else:
            return []
            
    except Exception as e:
        st.session_state['is_generating'] = False
        st.error(f"Error al conectar con la IA: {e}")
        return []

def mostrar_generador_ia_tutor():
    """F.1 Interfaz para generar juegos de trivia con la IA."""
    st.title("🤖 Generador IA Tutor")
    st.subheader("Paso 2: Define tu tema y nivel")
    
    # Asegurar el estado de generación
    if 'is_generating' not in st.session_state:
        st.session_state['is_generating'] = False
    
    # Inicializar config (si viene de una recarga)
    if 'trivia_config' not in st.session_state:
        st.session_state['trivia_config'] = {}
        st.session_state['preguntas_trivia'] = []
    
    # --- Formulario de Configuración ---
    with st.form("ia_generator_form"):
        col_grade, col_area, col_num = st.columns(3)
        with col_grade:
            st.session_state['trivia_config']['grado'] = st.selectbox(
                "Grado/Nivel", 
                ["6° Primaria", "7° Secundaria", "8° Secundaria", "9° Secundaria", "Universidad"], 
                key="ia_grado",
                index=["6° Primaria", "7° Secundaria", "8° Secundaria", "9° Secundaria", "Universidad"].index(st.session_state['trivia_config'].get('grado', '6° Primaria'))
            )
        with col_area:
            st.session_state['trivia_config']['area'] = st.selectbox(
                "Área/Materia", 
                ["Ciencias Naturales", "Historia", "Literatura", "Matemáticas", "Geografía"], 
                key="ia_area",
                index=["Ciencias Naturales", "Historia", "Literatura", "Matemáticas", "Geografía"].index(st.session_state['trivia_config'].get('area', 'Ciencias Naturales'))
            )
        with col_num:
            st.session_state['trivia_config']['num_preguntas'] = st.number_input(
                "Cantidad de Preguntas", 
                min_value=1, 
                max_value=10, 
                value=st.session_state['trivia_config'].get('num_preguntas', 5), 
                key="ia_num_preg_input"
            )

        st.session_state['trivia_config']['tema'] = st.text_area(
            "Tema/Tópico a Generar (Sé específico)", 
            height=100, 
            key="ia_tema",
            value=st.session_state['trivia_config'].get('tema', '')
        )
        
        submitted = st.form_submit_button(
            "🚀 Generar Preguntas", 
            disabled=st.session_state.get('is_generating') or not st.session_state['trivia_config'].get('tema'), 
            use_container_width=True, 
            type="primary"
        )
        
    if submitted:
        st.session_state['juego_iniciado'] = False # Resetear bandera
        
        with st.spinner(f"Generando trivia sobre '{st.session_state['trivia_config']['tema']}'..."):
            preguntas = generar_trivia_con_gemini(
                st.session_state['trivia_config']['tema'],
                st.session_state['trivia_config']['grado'],
                st.session_state['trivia_config']['area'],
                st.session_state['trivia_config']['num_preguntas']
            )
            
            if preguntas:
                st.session_state['preguntas_trivia'] = preguntas
                st.session_state['juego_iniciado'] = True
                # Definir título después de la generación
                st.session_state['trivia_config']['titulo'] = f"Trivia IA: {st.session_state['trivia_config']['tema'][:30]}..."
                st.session_state['trivia_config']['modo'] = 'IA'
                st.toast("🎉 Trivia generada con éxito.", icon="✅")
                # Forzar rerender para mostrar la sección de gestión
                st.rerun() 
            else:
                st.error("No se pudieron generar preguntas. Inténtalo de nuevo con un tema diferente.")
        
    # ---------------------------------------------------------------
    # Opciones de Gestión post-generación
    # ---------------------------------------------------------------
    
    if st.session_state.get('juego_iniciado') and st.session_state.get('preguntas_trivia'):
        st.markdown("---")
        st.subheader("✅ Trivia Generada - Opciones de Gestión")

        col_guardar, col_jugar = st.columns(2)
        
        # Guardar en la Biblioteca Personal
        with col_guardar:
            if st.button("💾 Guardar en Biblioteca", disabled=False, use_container_width=True, help="Guarda esta trivia en tu biblioteca personal."):
                if guardar_juego_trivia():
                    pass # Ya se muestra el toast dentro de la función

        # Jugar la Trivia (navegar)
        with col_jugar:
            if st.button("🎮 Iniciar el Juego", use_container_width=True, type="primary"):
                # Cargamos la trivia generada en el estado de juego
                seleccionar_trivia_para_jugar({
                    'id': 'temp_ia',
                    'titulo': st.session_state['trivia_config']['titulo'],
                    'preguntas': st.session_state['preguntas_trivia'],
                    'config': st.session_state['trivia_config']
                })
                
        st.markdown("---")
        
        # Mostrar el resultado de la generación de la IA
        st.subheader(f"Contenido de la Trivia: {st.session_state['trivia_config']['titulo']}")
        
        for i, pregunta in enumerate(st.session_state['preguntas_trivia']):
            with st.expander(f"Pregunta {i+1}: {pregunta['pregunta'][:50]}...", expanded=False):
                st.markdown(f"**Pregunta:** {pregunta['pregunta']}")
                st.markdown("**Opciones:**")
                for opcion in pregunta['opciones']:
                    if opcion == pregunta['respuesta_correcta']:
                        st.success(f"• {opcion} (Correcta)")
                    else:
                        st.markdown(f"• {opcion}")

    st.markdown("---")
    st.button("↩️ Volver a Fuentes", on_click=volver_menu_fuentes_trivia, type="secondary")

# -----------------------------------------------------------
# F.2 Formulario Manual
# -----------------------------------------------------------

def mostrar_formulario_manual():
    """F.2 Interfaz para crear un juego de trivia manualmente."""
    st.title("✍️ Configuración Manual de Trivia")
    st.subheader("Paso 2: Define las preguntas")

    # Inicializar estado para el modo manual
    if 'manual_config' not in st.session_state:
        st.session_state['manual_config'] = {
            'titulo': '',
            'area': 'General',
            'grado': 'General',
            'preguntas': [{'pregunta': '', 'opciones': ['', '', '', ''], 'correcta': 0}]
        }
    
    config = st.session_state['manual_config']

    # --- Título y Configuración General ---
    with st.container(border=True):
        col_t, col_a, col_g = st.columns(3)
        with col_t:
            config['titulo'] = st.text_input("Título de la Trivia", value=config['titulo'])
        with col_a:
            config['area'] = st.selectbox("Área/Materia", ["General", "Ciencias", "Historia"], index=["General", "Ciencias", "Historia"].index(config['area']))
        with col_g:
            config['grado'] = st.selectbox("Grado/Nivel", ["General", "Primaria", "Secundaria"], index=["General", "Primaria", "Secundaria"].index(config['grado']))

    st.markdown("---")
    
    # --- Editor de Preguntas ---
    st.subheader("Editor de Preguntas y Opciones")

    preguntas_a_eliminar = []
    
    for i, pregunta in enumerate(config['preguntas']):
        with st.expander(f"Pregunta {i+1}: {pregunta['pregunta'] or 'Nueva Pregunta'}", expanded=True):
            col_p, col_e = st.columns([0.9, 0.1])
            with col_p:
                pregunta['pregunta'] = st.text_area(f"Pregunta {i+1}", value=pregunta['pregunta'], key=f"manual_q_{i}", height=70)
            with col_e:
                st.markdown("<div style='height: 38px;'></div>", unsafe_allow_html=True) # Espaciador
                if st.button("🗑️", key=f"btn_delete_{i}", help="Eliminar pregunta", use_container_width=True):
                    preguntas_a_eliminar.append(i)

            st.markdown("**Opciones (marca la correcta):**")
            
            for j in range(4):
                col_o, col_r = st.columns([0.9, 0.1])
                with col_o:
                    pregunta['opciones'][j] = st.text_input(f"Opción {j+1}", value=pregunta['opciones'][j], key=f"manual_q_{i}_o_{j}")
                with col_r:
                    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True) # Espaciador
                    es_correcta = st.checkbox("R Correcta", value=(pregunta['correcta'] == j), key=f"manual_q_{i}_r_{j}")
                    if es_correcta:
                        pregunta['correcta'] = j
                    elif pregunta['correcta'] == j and not es_correcta:
                        # Si desmarcas la correcta, la deseleccionamos
                        pregunta['correcta'] = -1 
    
    # Eliminar preguntas marcadas
    for index in sorted(preguntas_a_eliminar, reverse=True):
        del config['preguntas'][index]
        
    # Botón para añadir nueva pregunta
    if st.button("➕ Añadir otra pregunta", use_container_width=True, type="secondary"):
        config['preguntas'].append({'pregunta': '', 'opciones': ['', '', '', ''], 'correcta': 0})
        st.rerun()

    st.markdown("---")

    # --- Botón de Guardar/Jugar ---
    if st.button("✅ Terminar y Jugar/Guardar", use_container_width=True, type="primary"):
        # 1. Validar las preguntas
        valid = True
        preguntas_limpias = []
        for pregunta in config['preguntas']:
            if not pregunta['pregunta'].strip():
                continue # Ignorar preguntas vacías
            
            opciones_validas = [o.strip() for o in pregunta['opciones'] if o.strip()]
            
            if len(opciones_validas) != 4 or pregunta['correcta'] == -1:
                st.error(f"La pregunta '{pregunta['pregunta'][:50]}...' no tiene 4 opciones válidas o no tiene una respuesta correcta marcada.")
                valid = False
                break
            
            # Formato de salida estandarizado (compatible con IA)
            preguntas_limpias.append({
                'pregunta': pregunta['pregunta'].strip(),
                'opciones': opciones_validas,
                'respuesta_correcta': opciones_validas[pregunta['correcta']]
            })
            
        if not valid or not preguntas_limpias:
            if not preguntas_limpias and valid:
                 st.error("Debes crear al menos una pregunta válida para continuar.")
            return

        # 2. Guardar en el estado de sesión y navegar
        st.session_state['preguntas_trivia'] = preguntas_limpias
        st.session_state['trivia_config']['titulo'] = config['titulo'] or "Trivia Manual Sin Título"
        st.session_state['trivia_config']['area'] = config['area']
        st.session_state['trivia_config']['grado'] = config['grado']
        st.session_state['trivia_config']['modo'] = 'Manual'
        
        # Guardar automáticamente la trivia manual
        guardar_juego_trivia()
        
        # Navegar
        seleccionar_trivia_para_jugar({
            'id': 'temp_manual',
            'titulo': st.session_state['trivia_config']['titulo'],
            'preguntas': st.session_state['preguntas_trivia'],
            'config': st.session_state['trivia_config']
        })
        
    st.markdown("---")
    st.button("↩️ Volver a Fuentes", on_click=volver_menu_fuentes_trivia, type="secondary")

# -----------------------------------------------------------
# F.3 Vista de Juego de Trivia
# -----------------------------------------------------------

def mostrar_juego_trivia():
    """F.3 Interfaz donde el usuario juega la trivia seleccionada."""
    
    if 'trivia_juego_seleccionado' not in st.session_state or not st.session_state['trivia_juego_seleccionado']:
        st.error("No se ha seleccionado ningún juego de trivia para empezar.")
        st.button("↩️ Volver al Menú Juegos", on_click=volver_menu_juegos, type="primary")
        return
        
    trivia_data = st.session_state['trivia_juego_seleccionado']
    
    # Asegurar estado del juego
    if 'trivia_paso' not in st.session_state:
        st.session_state['trivia_paso'] = 0
    if 'trivia_puntuacion' not in st.session_state:
        st.session_state['trivia_puntuacion'] = 0
    if 'opcion_seleccionada' not in st.session_state:
        st.session_state['opcion_seleccionada'] = None
    if 'respuesta_dada' not in st.session_state:
        st.session_state['respuesta_dada'] = False

    paso_actual = st.session_state['trivia_paso']
    preguntas = trivia_data['preguntas']
    total_preguntas = len(preguntas)
    
    st.title(f"🎮 {trivia_data['titulo']}")
    st.subheader(f"Pregunta {paso_actual + 1} de {total_preguntas}")
    st.markdown(f"**Puntuación:** {st.session_state['trivia_puntuacion']}")
    st.markdown("---")
    
    # -----------------------------------------------------------
    # Lógica de Fin de Juego
    # -----------------------------------------------------------
    if paso_actual >= total_preguntas:
        st.balloons()
        st.header("¡Juego Terminado! 🏆")
        st.success(f"Tu puntuación final es: {st.session_state['trivia_puntuacion']} de {total_preguntas}.")
        
        if st.button("↩️ Volver al Menú Juegos", on_click=volver_menu_juegos, type="primary"):
            # Limpiar estado del juego
            del st.session_state['trivia_juego_seleccionado']
            if 'trivia_paso' in st.session_state: del st.session_state['trivia_paso']
            if 'trivia_puntuacion' in st.session_state: del st.session_state['trivia_puntuacion']
        return

    # -----------------------------------------------------------
    # Renderizar Pregunta
    # -----------------------------------------------------------
    pregunta_actual = preguntas[paso_actual]
    
    st.markdown(f"### {pregunta_actual['pregunta']}")
    
    # Las opciones deben ser únicas para cada pregunta
    opciones_mezcladas = pregunta_actual['opciones'] # Ya deberían estar mezcladas si la IA lo hizo bien.
    random.shuffle(opciones_mezcladas) # Aseguramos el orden aleatorio en el cliente
    
    col_opts = st.columns(2)
    
    def manejar_respuesta(opcion):
        """Función de callback para cuando se selecciona una opción."""
        if st.session_state['respuesta_dada']:
            return # Evitar doble click
            
        st.session_state['opcion_seleccionada'] = opcion
        st.session_state['respuesta_dada'] = True
        
        es_correcta = (opcion == pregunta_actual['respuesta_correcta'])
        
        if es_correcta:
            st.session_state['trivia_puntuacion'] += 1
            st.toast("✅ ¡Respuesta Correcta!", icon="👍")
        else:
            st.toast("❌ Respuesta Incorrecta.", icon="👎")
        
        st.rerun() # Forzar el rerender para mostrar feedback
        
    # Mostrar Opciones y manejar clicks
    for idx, opcion in enumerate(opciones_mezcladas):
        col = col_opts[idx % 2]
        
        button_style = "secondary"
        button_disabled = st.session_state['respuesta_dada']
        
        if st.session_state['respuesta_dada']:
            # Mostrar feedback
            if opcion == pregunta_actual['respuesta_correcta']:
                button_style = "success"
            elif opcion == st.session_state['opcion_seleccionada']:
                button_style = "danger"
            # Si no es la correcta ni la elegida, queda como secondary/disabled
        elif st.session_state['opcion_seleccionada'] == opcion:
             button_style = "primary" # Marcar la selección antes de confirmar

        with col:
            st.button(
                f"{opcion}",
                key=f"opt_{paso_actual}_{idx}",
                on_click=manejar_respuesta,
                args=(opcion,),
                use_container_width=True,
                type=button_style,
                disabled=button_disabled
            )

    # -----------------------------------------------------------
    # Botón de Siguiente Pregunta (Solo visible después de responder)
    # -----------------------------------------------------------
    st.markdown("---")
    if st.session_state['respuesta_dada']:
        def pasar_siguiente_pregunta():
            st.session_state['trivia_paso'] += 1
            st.session_state['opcion_seleccionada'] = None
            st.session_state['respuesta_dada'] = False
            st.rerun()

        st.button(
            "➡️ Siguiente Pregunta", 
            key="btn_next_q", 
            on_click=pasar_siguiente_pregunta, 
            use_container_width=True,
            type="primary"
        )
    else:
        st.info("Selecciona una opción para continuar.")
        
# --- FUNCIONES G: BIBLIOTECA Y GLOBAL ---

def mostrar_menu_biblioteca():
    """G. Interfaz para ver los juegos de trivia guardados por el usuario (Biblioteca Personal)."""
    st.title("📚 Mi Biblioteca Personal")
    st.markdown("Estos son los juegos de trivia que has creado y guardado.")

    db = get_db()
    if not db:
        st.warning("⚠️ Base de datos no disponible. Intenta recargar la página.")
        st.button("↩️ Volver al Menú Juegos", on_click=volver_menu_juegos, type="secondary")
        return

    # Usar cache o spinner
    @st.cache_data(show_spinner="Cargando tus trivias...")
    def get_trivias():
        return cargar_trivias_usuario()
        
    trivias = get_trivias()

    if not trivias:
        st.info("Aún no has guardado ninguna trivia. ¡Crea una con el Generador IA!")
    else:
        st.subheader(f"Tienes {len(trivias)} trivias guardadas:")
        
        col_list = st.columns(3)
        
        for i, trivia in enumerate(trivias):
            with col_list[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{trivia.get('titulo', 'Sin Título')}**")
                    st.caption(f"Área: {trivia.get('area', 'N/A')} | Preguntas: {len(trivia.get('preguntas', []))}")
                    st.caption(f"Modo: {trivia.get('modo', 'N/A')}")
                    
                    if st.button("🎮 Jugar Ahora", key=f"jugar_bib_{trivia['id']}", use_container_width=True, type="primary"):
                        seleccionar_trivia_para_jugar(trivia)
                    
                    col_share, col_del = st.columns(2)
                    
                    with col_share:
                        if st.button("🌍 Compartir", key=f"share_bib_{trivia['id']}", use_container_width=True):
                            # Lógica para compartir en colección pública
                            compartir_trivia_global(trivia)
                    
                    with col_del:
                        if st.button("🗑️ Eliminar", key=f"del_bib_{trivia['id']}", use_container_width=True, type="secondary"):
                            # Lógica para eliminar
                            eliminar_trivia(trivia['id'])
                            st.cache_data.clear() # Limpiar cache para recargar la lista
                            st.rerun()

    st.markdown("---")
    st.button("↩️ Volver al Menú Juegos", on_click=volver_menu_juegos, type="secondary")
    
def compartir_trivia_global(trivia):
    """Copia una trivia de la biblioteca privada a la colección global."""
    db = get_db()
    if not db:
        st.error("Base de datos no disponible.")
        return False
        
    try:
        coleccion_global = get_public_collection_ref('trivias_globales')
        if coleccion_global is None:
            st.error("No se puede acceder a la colección global.")
            return False

        # Preparamos el documento sin el user_id (para anonimato en la colección pública)
        doc_data = {
            'timestamp': firestore.SERVER_TIMESTAMP,
            'config': trivia['config'],
            'preguntas_json': json.dumps(trivia['preguntas']),
            'titulo': trivia['titulo'],
            'area': trivia['area'],
            'grado': trivia['grado'],
            'modo': trivia['modo'],
            'origen_user_id': get_user_id() # Mantenemos el ID de origen si es necesario
        }
        
        coleccion_global.add(doc_data)
        st.toast(f"🎉 Trivia '{trivia['titulo']}' compartida globalmente.", icon="🌍")
        return True
    except Exception as e:
        st.error(f"Error al compartir la trivia: {e}")
        return False

def eliminar_trivia(doc_id):
    """Elimina una trivia de la biblioteca privada."""
    db = get_db()
    if not db:
        st.error("Base de datos no disponible.")
        return False
        
    try:
        coleccion = get_private_collection_ref('trivias')
        if coleccion is None:
            st.error("No se puede acceder a la colección privada.")
            return False
            
        coleccion.document(doc_id).delete()
        st.toast("🗑️ Trivia eliminada con éxito.", icon="✅")
        return True
    except Exception as e:
        st.error(f"Error al eliminar la trivia: {e}")
        return False

def mostrar_juegos_globales():
    """G. Interfaz para ver los juegos de trivia compartidos globalmente (Comunidad)."""
    st.title("🌍 Juegos de la Comunidad")
    st.markdown("Explora y juega las trivias compartidas por la comunidad educativa.")

    db = get_db()
    if not db:
        st.warning("⚠️ Base de datos no disponible. Intenta recargar la página.")
        st.button("↩️ Volver al Menú Juegos", on_click=volver_menu_juegos, type="secondary")
        return

    # Usar cache o spinner
    @st.cache_data(show_spinner="Cargando juegos globales...")
    def get_global_trivias():
        return cargar_trivias_globales()
        
    trivias = get_global_trivias()

    if not trivias:
        st.info("Aún no hay trivias compartidas globalmente. ¡Sé el primero en compartir!")
    else:
        st.subheader(f"Se encontraron {len(trivias)} trivias globales:")
        
        col_list = st.columns(3)
        
        for i, trivia in enumerate(trivias):
            with col_list[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{trivia.get('titulo', 'Sin Título')}**")
                    st.caption(f"Área: {trivia.get('area', 'N/A')} | Preguntas: {len(trivia.get('preguntas', []))}")
                    st.caption(f"Creado por: {trivia.get('origen_user_id', 'Anónimo')[:8]}...")
                    
                    if st.button("🎮 Jugar Trivia", key=f"jugar_glob_{trivia['id']}", use_container_width=True, type="primary"):
                        seleccionar_trivia_para_jugar(trivia)

    st.markdown("---")
    st.button("↩️ Volver al Menú Juegos", on_click=volver_menu_juegos, type="secondary")

# ============================================================
# I. FUNCIÓN PRINCIPAL: ROUTER
# ============================================================

def gamificacion():
    """
    Función principal que gestiona el enrutamiento (routing) de las diferentes vistas del arcade.
    """
    
    # 0. Inicialización de Firebase/Auth
    if 'auth_ready' not in st.session_state or not st.session_state['auth_ready']:
        inicializar_firebase()
        inicializar_autenticacion()
        
    if not st.session_state.get('auth_ready'):
        # Mostrar mensaje de espera mientras se autentica
        st.info("Cargando servicios de autenticación...")
        # st.stop() # No usamos stop para no interrumpir el flujo del iframe

    # 1. GESTIÓN DE ESTADO (Asegurando el estado inicial)
    if 'juego_actual' not in st.session_state:
        # Inicializa a 'menu_juegos'
        st.session_state['juego_actual'] = 'menu_juegos'
        
    # 2. RENDERIZADO DE VISTAS
    if st.session_state['juego_actual'] == 'menu_juegos':
        # Menú principal de juegos (D)
        mostrar_menu_juegos()

    elif st.session_state['juego_actual'] == 'trivia_fuentes':
        # Menú para seleccionar la fuente de Trivia (E)
        mostrar_menu_fuentes_trivia()

    elif st.session_state['juego_actual'] == 'trivia_ia_tutor':
        # Generación de Trivia usando IA-Tutor (F - Subsección IA)
        mostrar_generador_ia_tutor()

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
    
    elif st.session_state['juego_actual'] == 'juegos_globales':
        # Nueva página: Juegos Globales (G)
        mostrar_juegos_globales()
    
    else:
        # Fallback de seguridad
        st.session_state['juego_actual'] = 'menu_juegos'
        st.rerun()

# Ejecutar la función principal si el archivo se ejecuta directamente
if __name__ == '__main__':
    gamificacion()
