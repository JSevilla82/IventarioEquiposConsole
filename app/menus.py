# app/menus.py
import time
from colorama import Fore, Style
from . import ui
from .database import DatabaseManager
from .modules.gestion_accesos import registrar_nuevo_usuario, gestionar_usuarios_existentes
from .modules.configuracion import menu_configuracion_sistema
from .modules.gestion_activos import registrar_nuevo_activo
from .auth import cambiar_contrasena_usuario
from .config import ROLES_PERMISOS

def menu_gestion_accesos(db: DatabaseManager, usuario_logueado: dict):
    """Muestra el menú específico para la gestión de accesos."""
    while True:
        ui.mostrar_encabezado("Módulo de Gestión de Accesos", usuario_logueado=usuario_logueado)
        opciones = [
            "Registrar Nuevo Usuario", "Gestionar Usuarios Existentes",
            "Ver Log de Actividad del Sistema", "Cambiar mi Contraseña",
            "Volver al Menú Principal"
        ]
        ui.mostrar_menu(opciones)
        opcion = ui.solicitar_input(Fore.YELLOW + "Seleccione una opción: ")

        if opcion == '1': registrar_nuevo_usuario(db, usuario_logueado)
        elif opcion == '2': gestionar_usuarios_existentes(db, usuario_logueado)
        elif opcion == '3': _ver_log_sistema(db, usuario_logueado)
        elif opcion == '4': cambiar_contrasena_usuario(db, usuario_logueado)
        elif opcion == '5': break
        else: print(Fore.RED + "Opción no válida."); ui.pausar_pantalla()

def _ver_log_sistema(db: DatabaseManager, usuario_logueado: dict):
    """Muestra el log de actividad del sistema con paginación."""
    page, page_size = 1, 15
    while True:
        ui.mostrar_encabezado("Log de Actividad del Sistema", usuario_logueado=usuario_logueado)
        logs, total_pages = db.get_log_sistema_paginated(page, page_size)
        ui.mostrar_log_sistema(logs)
        
        if total_pages > 0:
            print(f"Página {page} de {total_pages}")
            prompt = "Presione (s) para siguiente, (a) para anterior, o (q) para salir: "
            opcion = ui.solicitar_input(Fore.CYAN + prompt).lower()

            if opcion == 's' and page < total_pages: page += 1
            elif opcion == 'a' and page > 1: page -= 1
            elif opcion == 'q': break
        else:
            ui.pausar_pantalla()
            break

def menu_gestion_activos(db: DatabaseManager, usuario_logueado: dict):
    """Muestra el menú para la gestión de activos."""
    while True:
        ui.mostrar_encabezado("Módulo de Gestión de Activos", usuario_logueado=usuario_logueado)
        opciones = ["Registrar Nuevo Activo", "Volver al Menú Principal"]
        ui.mostrar_menu(opciones)
        opcion = ui.solicitar_input(Fore.YELLOW + "Seleccione una opción: ")

        if opcion == '1': registrar_nuevo_activo(db, usuario_logueado)
        elif opcion == '2': break
        else: print(Fore.RED + "Opción no válida."); ui.pausar_pantalla()


def mostrar_menu_principal(db: DatabaseManager, usuario_logueado: dict):
    """Bucle principal que muestra el menú después de un inicio de sesión exitoso."""
    rol_actual = usuario_logueado['nombre_rol']
    
    while True:
        ui.mostrar_encabezado("Menú Principal", usuario_logueado=usuario_logueado)
        
        opciones = {}
        # Menú dinámico basado en permisos
        opciones['1'] = ("💻 Activos de la Organización", menu_gestion_activos)
        opciones['2'] = ("👤 Gestión de Accesos", menu_gestion_accesos)
        
        if "configurar_sistema" in ROLES_PERMISOS.get(rol_actual, {}):
            opciones['3'] = ("⚙️  Configuración del Sistema", menu_configuracion_sistema)
        
        opciones[str(len(opciones) + 1)] = ("↪️  Cerrar Sesión", None)

        # Mostrar menú
        for key, (texto, _) in opciones.items():
            print(Fore.YELLOW + f"{key}." + Style.RESET_ALL + f" {texto}")
        ui.mostrar_menu([]) # Solo para la línea separadora

        opcion_seleccionada = ui.solicitar_input(Fore.YELLOW + "Seleccione un módulo: ")
        
        if opcion_seleccionada in opciones:
            texto, funcion = opciones[opcion_seleccionada]
            if funcion:
                funcion(db, usuario_logueado)
            else: # Es la opción de Cerrar Sesión
                print(Fore.GREEN + "\nCerrando sesión..."); time.sleep(1); break
        else:
            print(Fore.RED + "\n❌ Opción no válida."); ui.pausar_pantalla()