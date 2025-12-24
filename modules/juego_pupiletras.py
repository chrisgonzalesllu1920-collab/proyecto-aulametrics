import streamlit as st
import pedagogical_assistant

def juego_pupiletras(volver_menu_juegos):
    """
    Implementa el juego de Pupiletras (Sopa de Letras) interactivo.
    Incluye generación por IA, tablero interactivo y descarga de ficha en Word.
    """

    # --- BARRA SUPERIOR ---
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("🔙 Menú", use_container_width=True, key="pupi_back"):
            # Limpiamos el estado del juego al salir para permitir nuevas configuraciones
            keys_to_clear = ['pupi_grid', 'pupi_data', 'pupi_found', 'pupi_docx_bytes']
            for k in keys_to_clear:
                if k in st.session_state:
                    del st.session_state[k]
            volver_menu_juegos()
            
    with col_title:
        st.subheader("🔎 Pupiletras: Buscador de Palabras")

    # --- CONFIGURACIÓN INICIAL (Si no hay juego generado) ---
    if 'pupi_grid' not in st.session_state:
        st.info("Configura tu sopa de letras:")
        
        col_conf1, col_conf2, col_conf3 = st.columns([2, 1, 1])
        with col_conf1:
            tema_pupi = st.text_input("Tema:", placeholder="Ej: Héroes del Perú...", key="input_tema_pupi")
        with col_conf2:
            lista_grados_pupi = [
                "1° Primaria", "2° Primaria", "3° Primaria", "4° Primaria", "5° Primaria", "6° Primaria",
                "1° Secundaria", "2° Secundaria", "3° Secundaria", "4° Secundaria", "5° Secundaria"
            ]
            grado_pupi = st.selectbox("Grado:", lista_grados_pupi, index=5, key="select_grado_pupi")
        with col_conf3:
            cant_palabras = st.slider("Palabras:", 5, 12, 8, key="slider_cant_pupi") 

        if st.button("🧩 Generar Sopa de Letras", type="primary", use_container_width=True, key="btn_gen_pupi"):
            if not tema_pupi:
                st.warning("⚠️ Escribe un tema.")
            else:
                with st.spinner("🤖 Diseñando ficha y juego interactivo..."):
                    # A) IA genera palabras a través del asistente pedagógico
                    palabras = pedagogical_assistant.generar_palabras_pupiletras(
                        tema_pupi, grado_pupi, cant_palabras
                    )
                    
                    if palabras:
                        # B) Crear matriz de letras
                        grid, colocados = pedagogical_assistant.crear_grid_pupiletras(palabras)
                        
                        # C) Generar documento Word para descarga
                        docx_buffer = pedagogical_assistant.generar_docx_pupiletras(
                            grid, colocados, tema_pupi, grado_pupi
                        )
                        
                        # Guardar todo en el session_state
                        st.session_state['pupi_grid'] = grid
                        st.session_state['pupi_data'] = colocados
                        st.session_state['pupi_found'] = set()
                        st.session_state['pupi_docx_bytes'] = docx_buffer.getvalue()
                        st.rerun()
                    else:
                        st.error("Error: La IA no pudo generar palabras. Intenta otro tema.")

        return  # Detenemos la ejecución aquí hasta que se genere el juego

    # --- INTERFAZ DEL JUEGO GENERADO ---
    grid = st.session_state['pupi_grid']
    palabras_data = st.session_state['pupi_data']
    encontradas = st.session_state['pupi_found']

    col_tablero, col_panel = st.columns([3, 1])

    # --- RENDERIZADO DEL TABLERO ---
    with col_tablero:
        st.markdown("##### 📍 Tablero Interactivo")
        
        # Identificamos qué celdas deben estar iluminadas (palabras encontradas)
        celdas_iluminadas = set()
        for p in palabras_data:
            if p['palabra'] in encontradas:
                for coord in p['coords']:
                    celdas_iluminadas.add(coord)

        # Construcción de la tabla HTML para la cuadrícula
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
                
                html_grid += f'''
                <td style="
                    width: 45px; height: 45px;
                    text-align: center;
                    font-family: monospace; font-size: 28px;
                    background-color: {bg};
                    color: {color};
                    border: {border};
                    font-weight: {weight};
                ">{letra}</td>'''
            html_grid += "</tr>"
        html_grid += "</table></div>"
        
        st.markdown(html_grid, unsafe_allow_html=True)

    # --- PANEL LATERAL DE CONTROL Y DESCARGA ---
    with col_panel:
        st.success("📄 Ficha Lista")
        st.download_button(
            label="📥 Descargar Word",
            data=st.session_state['pupi_docx_bytes'],
            file_name="Pupiletras_Clase.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            key="btn_download_pupi"
        )
        
        st.divider()
        st.markdown("##### 📝 Encontrar:")
        
        # Barra de progreso basada en palabras encontradas
        total_p = len(palabras_data)
        if total_p > 0:
            progreso = len(encontradas) / total_p
            st.progress(progreso, text=f"{len(encontradas)} de {total_p}")
        
        # Listado interactivo de palabras
        for i, p_item in enumerate(palabras_data):
            palabra = p_item['palabra']
            esta_encontrada = palabra in encontradas
            
            label = f"✅ {palabra}" if esta_encontrada else f"⬜ {palabra}"
            tipo = "primary" if esta_encontrada else "secondary"
            
            if st.button(label, key=f"btn_pupi_word_{i}", type=tipo, use_container_width=True):
                if esta_encontrada:
                    st.session_state['pupi_found'].remove(palabra)
                else:
                    st.session_state['pupi_found'].add(palabra)
                st.rerun()

        st.write("")
        if st.button("🔄 Reiniciar / Nuevo Tema", type="secondary", use_container_width=True, key="btn_reset_pupi"):
            # Borramos la cuadrícula actual para volver a la pantalla de configuración
            if 'pupi_grid' in st.session_state:
                del st.session_state['pupi_grid']
            st.rerun()
