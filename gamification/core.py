import math
from supabase import Client
from typing import Dict, Any, List, Optional
# Importamos las configuraciones y constantes definidas en la Fase 1
from .config import (
    NIVELES_CONFIG, PUNTOS_POR_ACCION, INSIGNIAS_CONFIG,
    DB_TABLE_USERS_INFO, DB_TABLE_LEADERBOARD
)

# =========================================================================
# === 1. UTILIDADES DE CÁLCULO ===
# =========================================================================

def calcular_nivel(puntos_actuales: int) -> str:
    """
    Determina el nombre del nivel del usuario basado en sus puntos totales.

    Args:
        puntos_actuales: El total de puntos acumulados por el usuario.

    Returns:
        El nombre del nivel correspondiente.
    """
    nivel_actual = "Semilla Digital" # Nivel base por defecto
    # Recorremos los niveles de mayor a menor umbral para encontrar el más alto
    # que el usuario ha alcanzado.
    umbrales = sorted(NIVELES_CONFIG.keys(), reverse=True)
    
    for umbral in umbrales:
        if puntos_actuales >= umbral:
            nivel_actual = NIVELES_CONFIG[umbral]
            break
            
    return nivel_actual

def obtener_puntos_por_accion(accion: str) -> int:
    """
    Devuelve los puntos asignados a una acción específica.
    """
    return PUNTOS_POR_ACCION.get(accion, 0)

# =========================================================================
# === 2. INTERACCIÓN CON LA BASE DE DATOS (SUPABASE) ===
# =========================================================================

async def get_user_gamification_data(supabase: Client, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene los datos de gamificación (puntos, insignias, contadores) de un usuario.

    Args:
        supabase: Instancia del cliente Supabase.
        user_id: ID único del usuario.

    Returns:
        Diccionario con los datos del usuario o None si ocurre un error.
    """
    try:
        # 1. Consulta la tabla principal de información de usuarios
        response = supabase.from_(DB_TABLE_USERS_INFO).select(
            "user_id, total_points, action_counters, earned_badges"
        ).eq("user_id", user_id).single().execute()
        
        # El .data es la fila encontrada
        user_data = response.data
        
        if user_data:
            # Asegurar que action_counters y earned_badges son diccionarios, 
            # inicializando si son None (puede pasar si son columnas JSON/text nuevas)
            if user_data.get('action_counters') is None:
                user_data['action_counters'] = {}
            if user_data.get('earned_badges') is None:
                user_data['earned_badges'] = {}
                
            return user_data
        
        # Si no se encuentra el usuario, devuelve None (lo que implica que 
        # el caller deberá inicializarlo)
        return None
        
    except Exception as e:
        print(f"Error al obtener datos de gamificación del usuario {user_id}: {e}")
        return None

async def upsert_user_data(supabase: Client, user_id: str, new_data: Dict[str, Any]):
    """
    Inserta o actualiza los datos de gamificación de un usuario en la tabla DB_TABLE_USERS_INFO.

    Args:
        supabase: Instancia del cliente Supabase.
        user_id: ID único del usuario.
        new_data: Diccionario con los datos a actualizar/insertar.
    """
    try:
        # Prepara los datos a enviar, incluyendo el user_id para el upsert
        data_to_upsert = {"user_id": user_id, **new_data}
        
        response = supabase.from_(DB_TABLE_USERS_INFO).upsert(
            data_to_upsert, 
            on_conflict="user_id" # Clave para determinar si es un INSERT o UPDATE
        ).execute()
        
        # Opcionalmente, puedes verificar response.count o response.data si necesitas confirmación
        return True
    
    except Exception as e:
        print(f"Error al hacer upsert de datos de gamificación para {user_id}: {e}")
        return False

# =========================================================================
# === 3. LÓGICA DE ASIGNACIÓN DE PUNTOS E INSIGNIAS ===
# =========================================================================

async def registrar_accion_y_actualizar_puntos(
    supabase: Client, 
    user_id: str, 
    accion: str
) -> Optional[Dict[str, Any]]:
    """
    Registra una acción del usuario, calcula los nuevos puntos/insignias 
    y actualiza la base de datos.

    Args:
        supabase: Instancia del cliente Supabase.
        user_id: ID único del usuario.
        accion: La clave de la acción realizada (ej: 'subir_archivo').

    Returns:
        Un diccionario con el estado actualizado (puntos, insignias obtenidas), 
        o None si falla.
    """
    # 1. Obtener datos actuales del usuario
    current_data = await get_user_gamification_data(supabase, user_id)
    
    # Si no se encuentran datos, inicializamos un perfil básico (total_points y contadores)
    if current_data is None:
        current_data = {
            "total_points": 0,
            "action_counters": {},
            "earned_badges": {}
        }

    # 2. Calcular los puntos a añadir
    puntos_ganados = obtener_puntos_por_accion(accion)
    if puntos_ganados == 0:
        # La acción no está configurada para dar puntos
        return None 

    # 3. Actualizar contadores y puntos
    current_data["total_points"] = current_data.get("total_points", 0) + puntos_ganados
    
    # Actualizar contador de acciones
    counters = current_data.get("action_counters", {})
    counters[accion] = counters.get(accion, 0) + 1
    current_data["action_counters"] = counters
    
    # 4. Verificar nuevas insignias basadas en el contador de acciones
    nuevas_insignias_obtenidas = []
    earned_badges = current_data.get("earned_badges", {})
    
    # Revisamos todas las configuraciones de insignias
    for badge_key, config in INSIGNIAS_CONFIG.items():
        # Saltamos las insignias que se otorgan por lógica de estado (ej: ranking/nivel)
        if config[3] is None: 
            continue 

        nombre_accion = None
        # Identificar la acción asociada a esta insignia (ej: 'files_uploaded_X' -> 'subir_archivo')
        for key in PUNTOS_POR_ACCION.keys():
            if key in badge_key:
                nombre_accion = key
                break
        
        # Si la insignia está ligada a una acción que no es la actual, o ya fue ganada, saltamos
        if nombre_accion != accion or badge_key in earned_badges:
            continue
            
        # 5. Lógica de obtención de insignia por umbral de acción
        umbral = config[3]
        contador_actual = counters.get(accion, 0)
        
        if contador_actual >= umbral:
            # ¡Insignia ganada!
            earned_badges[badge_key] = True 
            nuevas_insignias_obtenidas.append({
                "key": badge_key,
                "nombre": config[0],
                "descripcion": config[1],
                "emoji": config[2]
            })

    current_data["earned_badges"] = earned_badges
    
    # 6. Actualizar la base de datos
    success = await upsert_user_data(supabase, user_id, {
        "total_points": current_data["total_points"],
        # Guardamos los JSONs serializados
        "action_counters": current_data["action_counters"],
        "earned_badges": current_data["earned_badges"],
    })
    
    if success:
        # Devolvemos los datos clave, incluyendo el nivel actual y las insignias nuevas
        return {
            "total_points": current_data["total_points"],
            "nivel": calcular_nivel(current_data["total_points"]),
            "insignias_nuevas": nuevas_insignias_obtenidas,
            "puntos_ganados": puntos_ganados
        }
    else:
        return None

# =========================================================================
# === 4. FUNCIONES DE RANKING (LEADERBOARD) ===
# =========================================================================

async def get_leaderboard_data(supabase: Client, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene los datos del ranking (Top N) directamente de la tabla DB_TABLE_USERS_INFO,
    ordenados por total_points de forma descendente.

    Args:
        supabase: Instancia del cliente Supabase.
        limit: El número máximo de usuarios a devolver (ej: Top 10).

    Returns:
        Lista de diccionarios con el user_id, total_points y el nivel de los usuarios.
    """
    try:
        # Se asume que DB_TABLE_USERS_INFO es la fuente de la verdad para los puntos
        response = supabase.from_(DB_TABLE_USERS_INFO).select(
            "user_id, total_points"
        ).order(
            "total_points", 
            desc=True
        ).limit(limit).execute()
        
        leaderboard_data = []
        for row in response.data:
            puntos = row.get('total_points', 0)
            leaderboard_data.append({
                "user_id": row["user_id"],
                "total_points": puntos,
                "nivel": calcular_nivel(puntos)
            })
            
        return leaderboard_data
        
    except Exception as e:
        print(f"Error al obtener datos del ranking: {e}")
        return []

# -------------------------------------------------------------------------
# NOTA IMPORTANTE:
# Las funciones de esta sección (3 y 4) deben ser llamadas desde app.py 
# *después* de que se haya establecido la conexión a Supabase y se haya 
# autenticado el usuario.
# -------------------------------------------------------------------------
