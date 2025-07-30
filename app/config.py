# app/config.py

# --- Roles y Permisos ---
ROLES = ["Administrador", "Técnico", "Consulta"]

ROLES_PERMISOS = {
    "Administrador": {
        "gestionar_usuarios",
        "configurar_sistema",
        "registrar_equipo",
        "ver_inventario_completo",
        "generar_reportes"
    },
    "Técnico": {
        "registrar_equipo",
        "ver_inventario_asignado",
        "actualizar_estado_equipo"
    },
    "Consulta": {
        "ver_inventario_completo"
    }
}
