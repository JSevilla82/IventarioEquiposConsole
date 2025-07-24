# main.py
import os
from colorama import Fore, Back, Style
from dotenv import load_dotenv

from database import db_manager
from ui import (
    mostrar_encabezado, mostrar_menu, pausar_pantalla
)
from gestion_inventario import (
    registrar_equipo, gestionar_equipos, ver_inventario_consola,
    generar_excel_inventario, menu_gestionar_pendientes, menu_reportes
)
from gestion_acceso import (
    login, menu_usuarios, menu_ver_historico, menu_configuracion_sistema,
    cambiar_contrasena_usuario, inicializar_admin_si_no_existe, ROLES_PERMISOS
)

load_dotenv()

def menu_gestion_inventario(usuario: str):
    user_data = db_manager.get_user_by_username(usuario)
    rol_actual = user_data['rol']
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        opciones_disponibles = []
        if "registrar_equipo" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Registrar nuevo equipo")
        # --- Texto del menú actualizado ---
        if "gestionar_equipo" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Gestionar Equipos")
        if "ver_inventario" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Ver inventario (Consola/Excel)")
        if "generar_reporte" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Generar reportes avanzados")
        if "gestionar_pendientes" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Gestionar Mantenimientos y Devoluciones")
        opciones_disponibles.append("Volver al menú principal")

        mostrar_menu(opciones_disponibles, titulo="Módulo de Gestión de Inventario")
        opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
        
        try:
            opcion_idx = int(opcion) - 1
            if 0 <= opcion_idx < len(opciones_disponibles):
                opcion_texto = opciones_disponibles[opcion_idx]
                if opcion_texto == "Registrar nuevo equipo": registrar_equipo(usuario)
                # --- Llamada a la función actualizada ---
                elif opcion_texto == "Gestionar Equipos": gestionar_equipos(usuario)
                elif opcion_texto == "Ver inventario (Consola/Excel)": menu_ver_inventario(usuario)
                elif opcion_texto == "Generar reportes avanzados": menu_reportes(usuario)
                elif opcion_texto == "Gestionar Mantenimientos y Devoluciones": menu_gestionar_pendientes(usuario)
                elif opcion_texto == "Volver al menú principal": break
            else: print(Fore.RED + "Opción no válida.")
        except (ValueError, IndexError):
            print(Fore.RED + "Entrada no válida.")

def menu_gestion_acceso_sistema(usuario: str):
    user_data = db_manager.get_user_by_username(usuario)
    rol_actual = user_data['rol']
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        opciones_disponibles = []
        if "gestionar_usuarios" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Gestión de usuarios")
        if "ver_historico" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Ver histórico de movimientos")
        if "configurar_sistema" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Configuración del Sistema")
        opciones_disponibles.append("Cambiar mi contraseña")
        opciones_disponibles.append("Volver al menú principal")
        
        mostrar_menu(opciones_disponibles, titulo="Módulo de Acceso y Sistema")
        opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
        
        try:
            opcion_idx = int(opcion) - 1
            if 0 <= opcion_idx < len(opciones_disponibles):
                opcion_texto = opciones_disponibles[opcion_idx]
                if opcion_texto == "Gestión de usuarios": menu_usuarios(usuario)
                elif opcion_texto == "Ver histórico de movimientos": menu_ver_historico(usuario)
                elif opcion_texto == "Configuración del Sistema": menu_configuracion_sistema(usuario)
                elif opcion_texto == "Cambiar mi contraseña": cambiar_contrasena_usuario(usuario)
                elif opcion_texto == "Volver al menú principal": break
            else: print(Fore.RED + "Opción no válida.")
        except (ValueError, IndexError):
            print(Fore.RED + "Entrada no válida.")

def menu_ver_inventario(usuario: str):
    while True:
        mostrar_menu(["Ver en Consola", "Exportar a Excel (Completo)", "Volver"], titulo="Ver Inventario")
        opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
        if opcion == '1': ver_inventario_consola()
        elif opcion == '2': generar_excel_inventario(usuario)
        elif opcion == '3': break
        else: print(Fore.RED + "Opción no válida.")

def menu_principal():
    inicializar_admin_si_no_existe()
    
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production") 

    usuario_logueado = None

    if ENVIRONMENT == 'development':
        usuario_logueado = "admin"
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Back.YELLOW + Fore.BLACK + "--- MODO DESARROLLO ACTIVO ---" + Style.RESET_ALL)
        print(Fore.YELLOW + "Login omitido. Sesión iniciada como 'admin'.\n" + Style.RESET_ALL)
    else:
        while usuario_logueado is None:
            usuario_logueado = login()
            if usuario_logueado is None:
                if input(Fore.RED + "¿Salir del programa? (S/N): " + Style.RESET_ALL).strip().upper() == 'S':
                    return

    import ui
    ui.USUARIO_ACTUAL = usuario_logueado

    user_data = db_manager.get_user_by_username(usuario_logueado)
    rol_actual = user_data['rol']

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Fore.BLUE + "═" * 80)
        print(Back.BLUE + Fore.WHITE + f" MENÚ PRINCIPAL - Usuario: {usuario_logueado} (Rol: {rol_actual}) ".center(80, ' ') + Style.RESET_ALL)
        if ENVIRONMENT == 'development':
            print(Back.YELLOW + Fore.BLACK + "--- MODO DESARROLLO ---".center(80, ' ') + Style.RESET_ALL)
        print(Fore.BLUE + "═" * 80 + Style.RESET_ALL)
        
        opciones_principales = ["Gestión de Inventario", "Gestión de Acceso y Sistema", "Salir"]
        mostrar_menu(opciones_principales, titulo="Módulos del Sistema")
        
        opcion = input(Fore.YELLOW + "Seleccione un módulo: " + Style.RESET_ALL).strip()
        if opcion == '1':
            menu_gestion_inventario(usuario_logueado)
        elif opcion == '2':
            menu_gestion_acceso_sistema(usuario_logueado)
        elif opcion == '3':
            break
        else:
            print(Fore.RED + "\n❌ Opción no válida.")
            pausar_pantalla()
    
    print(Fore.GREEN + "\n¡Gracias por usar el Sistema de Gestión de Inventario!")

if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\nPrograma interrumpido por el usuario.")
    except Exception as e:
        print(Fore.RED + f"\n\n❌ Un error inesperado ha ocurrido: {str(e)}")
    finally:
        db_manager.close()
        print(Fore.GREEN + "\nConexión a la base de datos cerrada.")