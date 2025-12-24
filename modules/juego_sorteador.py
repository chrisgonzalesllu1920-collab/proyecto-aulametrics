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
