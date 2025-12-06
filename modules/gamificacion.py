import streamlit as st
import json
import time
import random
import pedagogical_assistant

def run():
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
