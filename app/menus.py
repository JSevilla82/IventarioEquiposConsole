# app/menus.py
import time
from colorama import Fore
from . import ui
from .database import DatabaseManager
from .modules.gestion_accesos import registrar_nuevo_usuario, gestionar_usuarios_existentes
from .auth import cambiar_contrasena_usuario

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
        
        print(f"Página {page} de {total_pages}")
        prompt = "Presione (s) para siguiente, (a) para anterior, o (q) para salir: "
        opcion = ui.solicitar_input(Fore.CYAN + prompt).lower()

        if opcion == 's' and page < total_pages: page += 1
        elif opcion == 'a' and page > 1: page -= 1
        elif opcion == 'q': break

def mostrar_menu_principal(db: DatabaseManager, usuario_logueado: dict):
    """Bucle principal que muestra el menú después de un inicio de sesión exitoso."""
    while True:
        ui.mostrar_encabezado("Menú Principal", usuario_logueado=usuario_logueado)
        opciones = ["👤 Gestión de Accesos", "↪️ Cerrar Sesión"]
        ui.mostrar_menu(opciones)
        opcion = ui.solicitar_input(Fore.YELLOW + "Seleccione un módulo: ")
        
        if opcion == '1': menu_gestion_accesos(db, usuario_logueado)
        elif opcion == '2': print(Fore.GREEN + "\nCerrando sesión..."); time.sleep(1); break
        else: print(Fore.RED + "\n❌ Opción no válida."); ui.pausar_pantalla()