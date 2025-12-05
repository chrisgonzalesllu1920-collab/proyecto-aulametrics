import streamlit as st
from typing import Dict, Any, List
# Importamos las configuraciones y constantes
from .config import NIVELES_CONFIG, INSIGNIAS_CONFIG

# =========================================================================
# === 1. COMPONENTE DE TARJETA DE PERFIL (SIDEBAR) ===
# =========================================================================

def display_user_profile_card(
    user_id: str, 
    total_points: int, 
    nivel: str, 
    earned_badges: Dict[str, bool]
):
    """
    Muestra la tarjeta de perfil del usuario en la barra lateral con su nivel, puntos e insignias.

    Args:
        user_id: ID único del usuario.
        total_points: Puntos totales del usuario.
        nivel: El nombre del nivel actual (calculado).
        earned_badges: Diccionario de insignias ganadas.
    """
    
    # Busca la configuración del nivel actual para obtener el emoji
    nivel_emoji = "⭐"
    # Buscamos el emoji del nivel, iterando la configuración
    for umbral, nombre in NIVELES_CONFIG.items():
        if nombre == nivel:
            # Obtener el índice de la tupla para el emoji, asumiendo que el valor es una tupla (nombre, emoji)
            # En config.py definimos NIVELES_CONFIG como {umbral: nombre_nivel}
            # Asumiremos un diccionario de mapeo adicional si NIVELES_CONFIG solo tiene el nombre.
            # Dado que NIVELES_CONFIG solo tiene el nombre en la Fase 1, usaremos un mapeo manual aquí:
            if nivel == "Semilla Digital":
                nivel_emoji = "🌱"
            elif nivel == "Aprendiz":
                nivel_emoji = "📘"
            elif nivel == "Maestro de Datos":
                nivel_emoji = "📊"
            elif nivel == "Visionario":
                nivel_emoji = "💡"
            elif nivel == "Arquitecto del Conocimiento":
                nivel_emoji = "🧠"
            break


    # --- Tarjeta de perfil en la Sidebar ---
    st.sidebar.markdown(f"**👤 Usuario ID:** `{user_id[:8]}...`")
    st.sidebar.markdown("---")
    
    # Diseño de puntos y nivel (usando markdown y HTML básico para Streamlit)
    st.sidebar.markdown(f"""
        <div style="text-align: center; padding: 10px; border: 1px solid #E0E0E0; border-radius: 10px; background-color: #f9f9f9;">
            <p style="font-size: 16px; margin: 0; color: #555;">PUNTOS TOTALES</p>
            <h2 style="font-size: 32px; font-weight: 700; color: #4CAF50; margin: 5px 0 10px 0;">
                {total_points}
            </h2>
            <div style="font-size: 18px; font-weight: 600; color: #333; border-top: 1px dashed #E0E0E0; padding-top: 10px;">
                {nivel_emoji} {nivel}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏆 Insignias Obtenidas")

    # Muestra las insignias
    insignias_html = ""
    badges_count = 0
    
    for key, config in INSIGNIAS_CONFIG.items():
        nombre, descripcion, emoji, umbral = config
        
        # Si la insignia fue ganada, la mostramos en color
        if earned_badges.get(key):
            badges_count += 1
            insignias_html += f"""
                <span title="{descripcion}" style="font-size: 28px; cursor: help; margin: 2px;">
                    {emoji}
                </span>
            """
        # Si no fue ganada, la mostramos en gris (opcional, para mantener la interfaz limpia)
        # else:
        #     insignias_html += f"""
        #         <span title="{descripcion} (Pendiente: {umbral} acciones)" style="font-size: 28px; opacity: 0.2; margin: 2px;">
        #             {emoji}
        #         </span>
        #     """
            
    if badges_count > 0:
        st.sidebar.markdown(f"""
            <div style="display: flex; flex-wrap: wrap; justify-content: center; padding: 10px; background-color: #fffbe6; border-radius: 8px;">
                {insignias_html}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.info("Aún no has desbloqueado ninguna insignia. ¡Sigue interactuando!")


# =========================================================================
# === 2. COMPONENTE DE RANKING (PÁGINA PRINCIPAL) ===
# =========================================================================

def display_leaderboard(leaderboard_data: List[Dict[str, Any]]):
    """
    Muestra el ranking de usuarios en un formato amigable.

    Args:
        leaderboard_data: Lista de diccionarios con user_id, total_points y nivel.
    """
    st.subheader("🥇 Ranking Global de Usuarios")
    st.markdown("---")
    
    # Diccionario para mapear user_id a un nombre corto
    # Nota: Si tu tabla de usuarios tiene un campo 'nombre' o 'email', 
    # deberías usarlo aquí. Por ahora, truncamos el user_id.
    
    for idx, user in enumerate(leaderboard_data):
        rank = idx + 1
        user_id = user['user_id']
        points = user['total_points']
        nivel = user['nivel']
        
        # Colores y estilos para el Top 3
        if rank == 1:
            emoji = "🥇"
            bg_color = "#FFD70033" # Oro con transparencia
            text_color = "#A36A00"
            border_color = "#FFD700"
        elif rank == 2:
            emoji = "🥈"
            bg_color = "#C0C0C033" # Plata con transparencia
            text_color = "#4D4D4D"
            border_color = "#C0C0C0"
        elif rank == 3:
            emoji = "🥉"
            bg_color = "#CD7F3233" # Bronce con transparencia
            text_color = "#8B4513"
            border_color = "#CD7F32"
        else:
            emoji = f"#{rank}"
            bg_color = "#f0f0f0"
            text_color = "#333333"
            border_color = "#dddddd"
            
        # Diseño HTML para cada fila
        st.markdown(f"""
            <div style="
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                padding: 10px 15px; 
                margin-bottom: 8px;
                border: 1px solid {border_color};
                border-radius: 8px;
                background-color: {bg_color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            ">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 24px; font-weight: 700; color: {text_color}; min-width: 40px; text-align: center;">
                        {emoji}
                    </span>
                    <span style="margin-left: 15px; font-weight: 500; color: #333;">
                        Usuario: {user_id[:12]}...
                    </span>
                </div>
                
                <div style="text-align: right;">
                    <div style="font-size: 18px; font-weight: 700; color: #4CAF50;">
                        {points} Puntos
                    </div>
                    <div style="font-size: 14px; color: #555;">
                        {nivel}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# =========================================================================
# === 3. NOTIFICACIÓN DE INSIGNIA OBTENIDA ===
# =========================================================================

def show_badge_notification(badge_info: Dict[str, Any]):
    """
    Muestra una notificación emergente de Streamlit cuando se gana una insignia.
    
    Args:
        badge_info: Diccionario con la info de la insignia (nombre, descripcion, emoji).
    """
    st.toast(
        body=f"🎉 ¡Insignia obtenida! {badge_info['emoji']} {badge_info['nombre']}",
        icon="🏆"
    )
    
    # Se puede usar st.success o st.info para notificaciones más permanentes
    # en la aplicación principal si es necesario.
