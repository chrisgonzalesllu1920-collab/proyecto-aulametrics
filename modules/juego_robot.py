def juego_ahorcado(volver_menu_juegos):
        import streamlit as st
    """
    Implementa el juego "Robot Ahorcado" utilizando Streamlit.

    Args:
        volver_menu_juegos (function): Función de callback para regresar
                                       al menú principal de juegos.
    """
    import streamlit as st
    import time
    # Se asume que 'pedagogical_assistant' está disponible en el entorno.
    import pedagogical_assistant

    # 4. JUEGO ROBOT (AHORCADO - VERSIÓN HÍBRIDA: CONFIGURACIÓN ORIGINAL + MEJORAS)
    # La validación 'juego_actual == 'ahorcado'' que estaba presente ya no es necesaria aquí,
    # pues se asume que esta función solo se llama cuando 'juego_actual' es 'ahorcado'.
    # Sin embargo, para mantener la lógica original del código, se mantiene el 'if'
    # que estaba originalmente para contener todo.
    if st.session_state.get('juego_actual') == 'ahorcado':
        
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

            /* Estilos para el botón "🔙 Menú" en la barra superior */
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
                        # Llamada a la función de la IA (pedagogical_assistant)
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
                # Ajustar el número de columnas para que la 'Ñ' encaje bien. 27 letras.
                # 9 columnas * 3 filas = 27 (perfecto).
                cols = st.columns(9)
                
                # La lógica de iteración se ajusta a 9 columnas
                for i, letra in enumerate(letras_teclado):
                    desactivado = letra in letras_adivinadas
                    type_btn = "secondary"
                    # Si la letra ha sido adivinada Y es parte de la palabra
                    if desactivado and letra in palabra: 
                        type_btn = "primary"
                        
                    # Usamos el módulo 9 para distribuir en 9 columnas
                    if cols[i % 9].button(letra, key=f"key_{letra}", disabled=desactivado, type=type_btn, use_container_width=True):
                        st.session_state['robot_guesses'].add(letra)
                        
                        if letra in palabra:
                            # Sonido de acierto
                            t_stamp = time.time()
                            contenedor_audio.markdown(f"""<audio autoplay style="display:none;"><source src="https://www.soundjay.com/buttons/sounds/button-3.mp3?t={t_stamp}"></audio>""", unsafe_allow_html=True)
                            time.sleep(0.2)
                        else:
                            # Sonido y alerta de error
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
    else:
        # Esto maneja el caso teórico de que se llame la función pero 'juego_actual' no sea 'ahorcado'
        # aunque en una integración normal esto no debería suceder.
        pass
