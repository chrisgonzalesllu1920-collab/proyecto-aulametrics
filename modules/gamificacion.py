import streamlit as st
import random
import time
from streamlit_lottie import st_lottie

# Tu función lottie (la importas desde app si prefieres)
def cargar_lottie(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


# ==============================
# FUNCIÓN PRINCIPAL DEL MÓDULO
# ==============================
def show():
    st.markdown("<h2 style='text-align:center;'>🎮 Sistema de Gamificación</h2>", unsafe_allow_html=True)

    # Aquí empieza TODO tu código tal cual estaba antes en home_page()
    # ----------------------------------------------------------------

    st.write("Bienvenido a la sección de gamificación. Aquí encontrarás tus retos, recompensas y misiones.")

    # TARJETAS / UI ORIGINAL
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
            <div style='padding:15px; border-radius:12px; background:#FEE1E8; text-align:center;'>
                <h3>💎 Puntos</h3>
                <h1 style='font-size:40px;'>1200</h1>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div style='padding:15px; border-radius:12px; background:#D9F8C4; text-align:center;'>
                <h3>🏆 Recompensas</h3>
                <h1 style='font-size:40px;'>8</h1>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div style='padding:15px; border-radius:12px; background:#CDE7FF; text-align:center;'>
                <h3>🎯 Misiones</h3>
                <h1 style='font-size:40px;'>3</h1>
            </div>
        """, unsafe_allow_html=True)

    st.write("---")

    # LISTA DE RETOS (CÓDIGO ORIGINAL)
    st.subheader("🔥 Retos Disponibles")

    retos = [
        "Responder 5 preguntas correctamente",
        "Completar una misión diaria",
        "Obtener 300 puntos en un día",
        "Participar en una actividad de clase"
    ]

    for reto in retos:
        with st.container():
            st.markdown(f"""
            <div style='padding:10px; margin-bottom:10px; border-radius:10px; border:1px solid #ccc;'>
                <h4>{reto}</h4>
                <button style='padding:8px; background:#4CAF50; color:white; border:none; border-radius:6px;'>
                    Completar Reto
                </button>
            </div>
            """, unsafe_allow_html=True)

    st.write("---")

    # ANIMACIÓN LOTTIE (CÓDIGO ORIGINAL)
    st.subheader("🎉 Recompensa especial del día")

    anim = cargar_lottie("assets/animations/reward.json")
    st_lottie(anim, height=200, key="reward_animation")

    # ----------------------------------------------------------------
    # FIN DEL CÓDIGO COPIADO TAL CUAL

