import streamlit as st
try:
    from passlib.context import CryptContext
except ImportError:
    # Esto es un fallback en caso de que el requirements.txt falle
    st.error("Faltan módulos de autenticación. Contacte al administrador.")
    
# Inicializa el contexto de encriptación
# Esto DEBE ser idéntico al de create_user.py
try:
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
except NameError:
    # Error si passlib no se importó
    pass 

# =========================================================================
# === BASE DE DATOS DE USUARIOS (Ahora con Hashing) ===
# =========================================================================
#
# ¡NO AÑADIR CONTRASEÑAS EN TEXTO PLANO AQUÍ!
# Usa tu herramienta local "create_user.py" para generar estas líneas.
#
# He convertido tus usuarios "admin" (clave: 123) y "demo" (clave: demo123)
# por ti.

PREMIUM_USERS = {
    "docente01": "$5$rounds=535000$lhPpO2w7c5cLz4wK$7mX/8ggtgrXgiTGwv8uWE4BkzCDUj1BYR/xNNXRJt8."
    # Añade aquí tus nuevos usuarios premium generados con create_user.py
    # "nuevo_cliente": "$2b$12$...",
}

FREE_USERS = {
    "docentea01": "$5$rounds=535000$50TEDdQcOp2s3R5B$LnI98emwNWQDI2MF/yZ1kZCdQmPhhQeaJXyR8K6aBt0"
    # Añade aquí tus nuevos usuarios gratuitos generados con create_user.py
}

# =========================================================================
# === FUNCIÓN DE LOGIN (Ahora con Hashing) ===
# =========================================================================

def login_user(username, password):
    """
    Verifica el usuario y la contraseña hasheada.
    Devuelve "premium", "free" o None.
    """
    
    # 1. Revisa si el usuario es Premium
    if username in PREMIUM_USERS:
        hashed_password = PREMIUM_USERS[username]
        try:
            # Compara la contraseña ingresada con el hash guardado
            if pwd_context.verify(password, hashed_password):
                return "premium"
        except NameError:
            st.error("El servidor de autenticación está fallando.")
            return None
            
    # 2. Revisa si el usuario es Gratuito
    if username in FREE_USERS:
        hashed_password = FREE_USERS[username]
        try:
            # Compara la contraseña ingresada con el hash guardado
            if pwd_context.verify(password, hashed_password):
                return "free"
        except NameError:
            st.error("El servidor de autenticación está fallando.")
            return None

    # 3. Si no se encontró o la contraseña es incorrecta
    return None


