import streamlit as st
import json
import time
import random
import pandas as pd

# Asumimos que pedagogical_assistant está disponible para la llamada a la IA
import pedagogical_assistant 

def gamificacion(supabase=None):
    """
    Función que gestiona la página de Gamificación, incluyendo el menú 
    de juegos y la lógica específica de cada juego (Trivia).
    """
    
    # --- A. GESTIÓN DE ESTADO (Inicialización) ---
    if 'juego_actual' not in st.session_state:
        st.session_state['juego_actual'] = None

    def volver_menu_juegos():
        """Reinicia el estado para volver a mostrar el menú principal de juegos."""
        # Limpiamos estados específicos de los juegos
        st.session_state.pop('juego_preguntas', None)
        st.session_state.pop('juego_terminado', None)
        st.session_state.pop('juego_iniciado', None)
        st.session_state.pop('juego_en_lobby', None)
        
        st.session_state['juego_actual'] = None
        st.rerun() 

    # --- B. RENDERIZADO PRINCIPAL (Ruteo Interno) ---
    
    # Esta es la lógica crucial que decide qué dibujar.
    if st.session_state['juego_actual'] is None:
        # Caso 1: No hay juego seleccionado. Mostramos el menú.
        mostrar_menu_principal(volver_menu_juegos)
        
    elif st.session_state['juego_actual'] == "Trivia":
        # Caso 2: El juego de Trivia está seleccionado.
        mostrar_pagina_trivia(volver_menu_juegos)
        
    elif st.session_state['juego_actual'] == "Ranking de Puntos":
        # Caso 3: Otro juego o sección.
        mostrar_ranking(volver_menu_juegos)

# =========================================================================
# --- C. FUNCIONES DE RENDERIZADO DETALLADAS ---
# =========================================================================

def mostrar_menu_principal(volver_menu_juegos_callback):
    """Renderiza el título de la página y los botones para seleccionar un juego."""
    
    st.title("🏆 Zona de Gamificación")
    st.markdown(
        """
        ¡Bienvenido a la zona de juegos de AulaMetrics! Selecciona un juego para empezar.
        """
    )
    
    st.divider()

    # Definimos los juegos disponibles
    juegos = {
        "Trivia": {
            "icon": "🧠",
            "description": "Pon a prueba tus conocimientos sobre los datos cargados. Generado por IA.",
        },
        "Ranking de Puntos": {
            "icon": "🏅",
            "description": "Consulta tu posición y la de tus compañeros.",
        },
    }

    # Creamos un diseño de columnas responsive
    cols = st.columns(2) # Dos columnas para las tarjetas
    
    for i, (nombre, info) in enumerate(juegos.items()):
        # Usamos el operador módulo para asignar el juego a la columna correcta (0 o 1)
        with cols[i % 2]: 
            # Contenedor/Tarjeta
            with st.container(border=True):
                st.subheader(f"{info['icon']} {nombre}")
                st.write(info["description"])
                
                # Botón para iniciar el juego
                if st.button(f"Jugar {nombre}", key=f"btn_{nombre}", use_container_width=True):
                    # Al presionar, cambiamos el estado y forzamos la recarga
                    st.session_state['juego_actual'] = nombre
                    st.rerun() 

def mostrar_pagina_trivia(volver_menu_juegos_callback):
    """Esqueleto de la página de Trivia."""
    
    col1, col2 = st.columns([0.2, 0.8])
    with col1:
        st.button("↩️ Volver", on_click=volver_menu_juegos_callback, use_container_width=True)
        
    with col2:
        st.header("🧠 Trivia (Generada por IA)")
    
    st.divider()

    st.info("Esta es la página de Trivia. Aquí iría la lógica para generación de preguntas y el flujo del juego.")
    # El resto de la lógica de Trivia (generación de preguntas, etc.) iría aquí.

def mostrar_ranking(volver_menu_juegos_callback):
    """Esqueleto para la página de Ranking."""
    
    col1, col2 = st.columns([0.2, 0.8])
    with col1:
        st.button("↩️ Volver", on_click=volver_menu_juegos_callback, use_container_width=True)
        
    with col2:
        st.header("🏅 Ranking de Puntos")

    st.divider()
    
    st.warning("Esta sección está en desarrollo. Aquí se mostrarían las tablas de puntajes usando Supabase.")
    # El resto de la lógica de Ranking iría aquí.
