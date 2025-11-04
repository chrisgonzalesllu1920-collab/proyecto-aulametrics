def login_user(username, password):
    """
    Función de autenticación.
    Verifica las credenciales y devuelve el nivel del usuario.
    """
    
    # --- DEFINE AQUÍ TUS USUARIOS ---
    
    # 1. Usuario Premium (Usa tus credenciales reales)
    PREMIUM_USERNAME = "admin20" 
    PREMIUM_PASSWORD = "admin20"
    
    # 2. Usuario Gratuito (Credenciales de ejemplo)
    FREE_USERNAME = "admin"
    FREE_PASSWORD = "admin"

    # --- Lógica de validación ---
    
    if username == PREMIUM_USERNAME and password == PREMIUM_PASSWORD:
        return "premium" # Devuelve el nivel "premium"
    
    elif username == FREE_USERNAME and password == FREE_PASSWORD:
        return "free" # Devuelve el nivel "free"
        
    else:
        return None # Devuelve None si el login falla