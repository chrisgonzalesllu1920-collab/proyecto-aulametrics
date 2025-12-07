import streamlit as st
import json
import time
import random
# Asumimos que pedagogical_assistant está disponible para la llamada a la IA
import pedagogical_assistant 

def gamificacion(supabase=None):
    """
    Función que gestiona la página de Gamificación, incluyendo el menú 
    de juegos y la lógica específica de cada juego (Trivia).

    Args:
        supabase (Client, optional): Cliente de Supabase. No se usa directamente 
                                     en esta versión de Gamificación, pero se mantiene 
                                     para futuras integraciones de puntajes.
    """
    
    # --- A. GESTIÓN DE ESTADO ---
    if 'juego_actual' not in st.session_state:
        st.session_state['juego_actual'] = None

    def volver_menu_juegos():
        """Reinicia el estado para volver a mostrar el menú principal de juegos."""
        # Limpiamos todos los estados específicos de los juegos para evitar conflictos
        if 'juego_preguntas' in st.session_state: del st.session_state['juego_preguntas']
        if 'juego_terminado' in st.session_state: del st.session_state['juego_terminado']
        if 'juego_iniciado' in st.session_state: del st.session_state['juego_iniciado']
        if 'juego_en_lobby' in st.session_state: del st.session_state['juego_en_lobby']
        
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
    
    # --- C. JUEGO TRIVIA (LÓGICA) ---
    def mostrar_juego_trivia():
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
            /* Estilos para el botón primario (Generar) */
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
            /* Estilos para los botones de opciones (Respuestas) */
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
            # Creamos un estado local para el checkbox para que no interfiera con otros juegos
            if 'modo_cine_trivia' not in st.session_state:
                st.session_state['modo_cine_trivia'] = False
                
            modo_cine = st.checkbox("📺 Modo Cine", key="modo_cine_trivia_check", 
                                    value=st.session_state['modo_cine_trivia'], 
                                    help="Oculta la barra lateral.")
            st.session_state['modo_cine_trivia'] = modo_cine
            
        if st.session_state['modo_cine_trivia']:
            # Ocultamos la barra lateral, header y footer
            st.markdown("""<style>[data-testid="stSidebar"], header, footer {display: none;}</style>""", unsafe_allow_html=True)


        # --- LÓGICA TRIVIA: GENERACIÓN (Lobby de Configuración) ---
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
                                # La función pedagogical_assistant.generar_trivia_juego debe existir
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
                                    
                                    st.session_state['juego_en_lobby'] = True # Pasa a la pantalla de "empezar"
                                    st.session_state['juego_iniciado'] = True # Bandera para no volver a esta sección
                                    
                                    exito = True # Rompemos el bucle
                                    st.rerun()
                                else:
                                    raise Exception("Respuesta vacía de la IA")

                        except json.JSONDecodeError:
                            # ¡Ajá! Aquí capturamos el error de formato (ej. Expecting , delimiter)
                            time.sleep(1) # Esperamos un segundo para no saturar
                            continue # Volvemos a empezar el bucle while
                            
                        except Exception as e:
                            st.error(f"Error inesperado durante la generación: {e}")
                            break # Si es otro error, paramos
                    
                    # Si después de 3 intentos sigue fallando...
                    if not exito:
                        st.error("❌ La IA está teniendo dificultades con este tema específico. Por favor, intenta cambiar ligeramente el nombre del tema.")
            st.divider()

        # --- LÓGICA TRIVIA: LOBBY (Pantalla de inicio) ---
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

        # --- LÓGICA TRIVIA: JUEGO ACTIVO (Pregunta-Respuesta) ---
        elif not st.session_state.get('juego_terminado', False):
            idx = st.session_state['juego_indice']
            preguntas = st.session_state['juego_preguntas']
            current_score = int(st.session_state['juego_puntaje'])
            modo = st.session_state.get('modo_avance', 'auto')
            fase = st.session_state.get('fase_pregunta', 'respondiendo')

            if idx >= len(preguntas):
                # Caso de seguridad: si el índice se sale del rango, termina el juego.
                st.session_state['juego_terminado'] = True
                st.rerun()

            pregunta_actual = preguntas[idx]
            
            col_info1, col_info2 = st.columns([3, 1])
            with col_info1:
                st.caption(f"Pregunta {idx + 1} de {len(preguntas)}")
                st.progress((idx + 1) / len(preguntas))
            with col_info2:
                # Muestra el puntaje
                st.markdown(f"""<div style="text-align: right;"><span style="font-size: 45px; font-weight: 900; color: #28a745; background: #e6fffa; padding: 5px 20px; border-radius: 15px; border: 2px solid #28a745;">{current_score}</span></div>""", unsafe_allow_html=True)
            
            st.write("") 
            st.markdown(f"""<div class="big-question">{pregunta_actual['pregunta']}</div>""", unsafe_allow_html=True)
            
            if fase == 'respondiendo':
                opciones = pregunta_actual['opciones']
                col_opt1, col_opt2 = st.columns(2)
                
                # Función manejadora de la respuesta
                def responder(opcion_elegida):
                    
                    correcta = pregunta_actual['respuesta_correcta']
                    puntos_por_pregunta = 100 / len(preguntas)
                    es_correcta = (opcion_elegida == correcta)
                    
                    if es_correcta:
                        st.session_state['juego_puntaje'] += puntos_por_pregunta
                        st.session_state['ultimo_feedback'] = f"correcta|{int(puntos_por_pregunta)}"
                    else:
                        st.session_state['ultimo_feedback'] = f"incorrecta|{correcta}"

                    # Si es modo automático (rápido), avanza inmediatamente
                    if modo == 'auto':
                        # Mostrar feedback temporalmente antes de avanzar
                        feedback_container = st.empty()
                        if es_correcta:
                            feedback_container.markdown(f"""<div style="background-color: #d1e7dd; color: #0f5132; padding: 20px; border-radius: 10px; text-align: center; font-size: 30px; font-weight: bold;">🎉 ¡CORRECTO!</div>""", unsafe_allow_html=True)
                        else:
                            feedback_container.markdown(f"""<div style="background-color: #f8d7da; color: #842029; padding: 20px; border-radius: 10px; text-align: center; font-size: 30px; font-weight: bold;">❌ INCORRECTO. Era: {correcta}</div>""", unsafe_allow_html=True)
                        
                        # Pausa de 2 segundos para que el usuario vea el feedback
                        time.sleep(2.0) 
                        
                        # Limpiar el feedback
                        feedback_container.empty()
                        
                        # Avanzar o terminar
                        if st.session_state['juego_indice'] < len(preguntas) - 1:
                            st.session_state['juego_indice'] += 1
                        else:
                            st.session_state['juego_terminado'] = True
                        st.rerun()
                    else:
                        # Modo guiado: pasa a la fase de feedback para que el docente controle el avance
                        st.session_state['fase_pregunta'] = 'feedback'
                        st.rerun()

                # Renderizado de opciones de respuesta
                opciones_letras = ["A", "B", "C", "D"]
                columnas = [col_opt1, col_opt2, col_opt1, col_opt2] # Distribuye en 2x2
                
                for i, opcion in enumerate(opciones):
                    col = columnas[i]
                    with col:
                        # Aseguramos que los botones de opciones usen la clave correcta
                        if st.button(f"{opciones_letras[i]}) {opcion}", use_container_width=True, key=f"btn_opt_{idx}_{i}"): 
                            responder(opcion)
            
            # Fase de Feedback (Solo para Modo Guiado)
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

        # --- LÓGICA TRIVIA: RESULTADOS (Juego Terminado) ---
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
                    # Limpiamos todos los estados específicos para volver al lobby de configuración
                    st.session_state['juego_iniciado'] = False 
                    if 'juego_preguntas' in st.session_state: del st.session_state['juego_preguntas']
                    if 'juego_terminado' in st.session_state: del st.session_state['juego_terminado']
                    if 'juego_en_lobby' in st.session_state: del st.session_state['juego_en_lobby']
                    st.rerun()

