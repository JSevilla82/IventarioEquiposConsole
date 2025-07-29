# app/config.py
ROLES = ["Administrador", "Gestor", "Visualizador"]

ROLES_PERMISOS = {
    "Administrador": { "gestionar_usuarios", "ver_log_sistema" },
    "Gestor": {},
    "Visualizador": {}
}