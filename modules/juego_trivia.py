import streamlit as st
import json
import time

def juego_trivia(volver_menu_juegos):
    """
    Función que gestiona la lógica completa del juego de Trivia.
    Requiere que 'pedagogical_assistant' esté disponible en el scope global 
    o importado correctamente.
    """
    # Barra superior
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("🔙 Menú", use_container_width=True, key="btn_volver_menu"):
            volver_menu_juegos()
    with col_title:
        st.subheader("Desafío Trivia")

    # --- CSS TRIVIA ---
    st.markdown("""
        <style>

        /* ========================================================= */
        /* BOTÓN "🔙 Menú" - selector hiper-específico (INFALIBLE)  */
        /* ========================================================= */

        button[data-testid="baseButton-default"][id="btn_volver_menu"] {
            background-color: #fff59d !important;
            color: #1e3a8a !important;
            border: 2px solid #fbc02d !important;
            font-size: 14px !important;      /* tamaño del texto */
            padding: 4px 10px !important;      /* tamaño del botón */
            border-radius: 10px !important;   /* curvas */
            box-shadow: 0px 3px 0px #f9a825 !important;
        }

        button[data-testid="baseButton-default"][id="btn_volver_menu"]:hover {
            background-color: #fff176 !important;
            transform: translateY(-2px);
        }

        /* ----------------------------- */
        /* BOTÓN PRINCIPAL (no usado aquí) */
        /* ----------------------------- */
        div.stButton > button[kind="primary"] {
            background-color: #28a745 !important;
            border-color: #28a745 !important;
            color: white !important;
            font-size: 24px !important;
            font-weight: bold !important;
            padding: 15px 30px !important;
        }

        /* ----------------------------- */
        /* ESTILO PREGUNTA PRINCIPAL */
        /* ----------------------------- */
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

        /* ----------------------------- */
        /* BOTONES DE OPCIONES DE RESPUESTA */
        /* ----------------------------- */
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
                            # 1. Llamada a la IA (Asumiendo que pedagogical_assistant está disponible)
                            respuesta_json = pedagogical_assistant.generar_trivia_juego(tema_input, grado_input, "General", num_input)
                            
                            if respuesta_json:
                                # 2. Limpieza agresiva del JSON
                                clean_json = respuesta_json.replace('```json', '').replace('```', '').strip()
                                
                                # 3. Intento de conversión
                                preguntas = json.loads(clean_json)
                                
                                # 4. Si pasa, ÉXITO. Guardamos todo en el estado.
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
                        time.sleep(1) # Esperamos un segundo para no saturar
                        continue # Volvemos a intentar el bucle
                        
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")
                        break 
                
                if not exito:
                    st.error("❌ La IA está teniendo dificultades con este tema. Intenta con un término más general.")
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
            
            def responder(opcion_elegida):
                # La librería time ya está importada al inicio del archivo
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
                # Limpieza de estados del juego para reiniciar
                if 'juego_preguntas' in st.session_state: del st.session_state['juego_preguntas']
                if 'juego_terminado' in st.session_state: del st.session_state['juego_terminado']
                st.rerun()
