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
from .juego_sorteador import juego_sorteador
from .juego_pupiletras import juego_pupiletras
from .juego_robot import juego_robot
from .juego_trivia import juego_trivia
import uuid # Necesario para generar IDs anónimos
# from streamlit_lottie import st_lottie # Dejar comentada si no se usa

# ============================================================
#   MÓDULO DE GAMIFICACIÓN – VERSIÓN ORGANIZADA
# ============================================================

# ------------------------------------------------------------
# A. GESTIÓN DE ESTADO GENERAL
# ------------------------------------------------------------
def volver_menu_juegos():
    st.session_state['juego_actual'] = None
    st.rerun()

# ------------------------------------------------------------
# B. MENÚ PRINCIPAL DE JUEGOS
# ------------------------------------------------------------
def mostrar_menu_juegos():

    # 1. CSS (Tu mismo CSS pegado sin cambiar nada)
    st.markdown("""
    <style>
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
    </style>
    """, unsafe_allow_html=True)

    # 2. Título (copiado igual)
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h2 style="color: #4A148C; font-size: 38px; font-weight: 900; letter-spacing: -1px;">🎮 ARCADE PEDAGÓGICO</h2>
        <p style="color: #616161; font-size: 18px; font-weight: 500;">Selecciona tu desafío</p>
    </div>
    """, unsafe_allow_html=True)

    # 3. Botones
    col1, col2 = st.columns(2, gap="large")

    with col1:
        if st.button("🧠 TRIVIA\n\n¿Cuánto sabes?", key="btn_card_trivia", use_container_width=True):
            st.session_state['juego_actual'] = 'trivia'
            st.rerun()

    with col2:
        if st.button("🔤 PUPILETRAS\n\nAgudeza Visual", key="btn_card_pupi", use_container_width=True):
            st.session_state['juego_actual'] = 'pupiletras'
            st.rerun()

    st.write("")

    col3, col4 = st.columns(2, gap="large")

    with col3:
        if st.button("🤖 ROBOT\n\nLógica & Deducción", key="btn_card_robot", use_container_width=True):
            st.session_state['juego_actual'] = 'robot'
            st.rerun()

    with col4:
        st.markdown(
            '<div class="card-icon" style="text-align: center; margin-bottom: -55px; position: relative; z-index: 5; pointer-events: none; font-size: 40px;">🎰</div>',
            unsafe_allow_html=True
        )
        if st.button("\n\nSorteador\n\nElegir participantes", key="btn_sorteo_v1", use_container_width=True):
            st.session_state['juego_actual'] = 'sorteador'
            st.rerun()

    elif st.session_state["juego_actual"] == 'trivia':
        juego_trivia(volver_menu_juegos)

    elif st.session_state['juego_actual'] == 'pupiletras':
        juego_pupiletras(volver_menu_juegos)

    elif st.session_state['juego_actual'] == 'robot': 
        juego_robot(volver_menu_juegos)
  
    elif st.session_state['juego_actual'] == 'sorteador':
        juego_sorteador(volver_menu_juegos)

# ------------------------------------------------------------
# E. FUNCIÓN PRINCIPAL: ROUTER
# ------------------------------------------------------------
def gamificacion():

    # Asegura estado inicial
    if "juego_actual" not in st.session_state:
        st.session_state["juego_actual"] = None

    # Router
    if st.session_state["juego_actual"] is None:
        # Asumiendo que 'mostrar_menu_juegos' está definida en alguna parte.
        mostrar_menu_juegos() 

    elif st.session_state["juego_actual"] == 'trivia':
        juego_trivia(volver_menu_juegos)


    elif st.session_state['juego_actual'] == 'pupiletras':
        juego_pupiletras(volver_menu_juegos)
    

    elif st.session_state['juego_actual'] == 'robot': 
        juego_robot(volver_menu_juegos)


    elif st.session_state['juego_actual'] == 'sorteador':
        # Llamada verificada y correcta
        juego_sorteador(volver_menu_juegos)
