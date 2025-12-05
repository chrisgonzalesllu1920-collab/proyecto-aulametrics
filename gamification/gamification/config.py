# Definiciones de constantes para el módulo de Gamificación

# --- UMBRALES DE NIVELES (PUNTOS MÍNIMOS REQUERIDOS) ---
# El nivel se basa en el total de puntos acumulados.
NIVELES_CONFIG = {
    0: "Semilla Digital",
    100: "Explorador de Datos",
    300: "Analista Emergente",
    700: "Guardián del Conocimiento",
    1200: "Maestro de las Métricas",
    2000: "Leyenda del Aula",
}

# --- ASIGNACIÓN DE PUNTOS POR ACCIÓN ---
# Puntos que se otorgan al usuario por realizar ciertas acciones dentro de la aplicación.
PUNTOS_POR_ACCION = {
    "login": 5,           # Al iniciar sesión
    "subir_archivo": 25,  # Al subir y procesar un archivo de datos
    "generar_reporte": 15, # Al generar un reporte o un análisis
    "usar_ppt_generator": 30, # Al usar la herramienta de generador de PPTs
    "usar_asistente": 10, # Al interactuar con el asistente pedagógico
    "sorteo_participar": 5, # Al participar en un sorteo
    "sorteo_ganar": 50, # Al ganar un sorteo
}

# --- CONFIGURACIÓN DE INSIGNIAS ---
# Diccionario que define las insignias y el criterio para obtenerlas (basado en el número de veces que se realiza una acción).
INSIGNIAS_CONFIG = {
    # {nombre_interno}: (nombre_visible, descripción, emoji, umbral_accion)
    "files_uploaded_1": ("Iniciador de Datos", "Ha subido su primer archivo.", "📁", 1),
    "files_uploaded_5": ("Archivista", "Ha subido 5 o más archivos.", "🗃️", 5),
    "reports_generated_1": ("Reportero Novato", "Ha generado su primer informe.", "📄", 1),
    "reports_generated_10": ("Generador Pro", "Ha generado 10 o más informes.", "📰", 10),
    "ppt_used_1": ("Presentador", "Ha usado el generador de PPT por primera vez.", "🖼️", 1),
    "ppt_used_5": ("Conferencista", "Ha generado 5 presentaciones de PPT.", "🎤", 5),
    "assistant_used_10": ("Asistente Fiel", "Ha consultado al asistente 10 veces.", "🤖", 10),
    # Las siguientes insignias no tienen un umbral de acción fijo, sino que se otorgan por lógica de estado (nivel o posición en el ranking).
    "leader_board_top_3": ("Podio de Honor", "Ha estado en el Top 3 del ranking.", "🥇", None), 
    "level_maestro": ("Maestro de las Métricas", "Alcanzó el nivel 'Maestro de las Métricas'.", "🌟", 1), 
}

# --- NOMBRES DE TABLAS DE LA BASE DE DATOS (Supabase) ---
# Nombres de las tablas de Supabase para evitar errores de tipeo.
DB_TABLE_USERS_INFO = "users_info"
DB_TABLE_LEADERBOARD = "leaderboard" # Donde se guarda el ranking o resumen de puntos.

# --- ESTILOS DE LA INTERFAZ (Se usará en el módulo views.py) ---
# Estilos CSS básicos (en línea) para la visualización del ranking/insignias.
ESTILOS_CSS_LEADERBOARD = """
    /* Clase para cada elemento del ranking */
    .leaderboard-item {
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 10px 15px; 
        margin-bottom: 8px; 
        border-radius: 12px; 
        background-color: #f7f7f7;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s;
    }
    .leaderboard-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 10px rgba(0, 0, 0, 0.1);
    }
    /* Estilo para el número de rango (1, 2, 3...) */
    .rank-number {
        font-size: 24px; 
        font-weight: 700; 
        color: #4CAF50; /* Color primario */
        margin-right: 15px;
        min-width: 30px; /* Asegura el alineamiento */
        text-align: center;
    }
    /* Estilo para el nombre del usuario */
    .name-style {
        font-size: 18px; 
        font-weight: 500; 
        color: #333;
        flex-grow: 1; /* Permite que el nombre ocupe el espacio restante */
    }
    /* Estilo para los puntos */
    .points-style {
        font-size: 20px; 
        font-weight: bold; 
        color: #FF9800; /* Color de acento */
        margin-left: 15px;
    }
    /* Estilo para el nivel */
    .level-style {
        font-size: 14px; 
        font-weight: 400; 
        color: #666; 
        margin-left: 10px;
        font-style: italic;
    }
    /* Estilos especiales para el top 3 */
    .rank-gold { background-color: #FFD70030; }
    .rank-silver { background-color: #C0C0C030; }
    .rank-bronze { background-color: #CD7F3230; }
"""
