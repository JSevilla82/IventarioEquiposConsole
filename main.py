# main.py
import os
from colorama import Fore, Back, Style
from dotenv import load_dotenv

from database import db_manager
from ui import (
    mostrar_encabezado, mostrar_menu, pausar_pantalla
)
from gestion_inventario import (
    registrar_equipo, gestionar_equipos, menu_ver_inventario_excel,
    menu_gestionar_pendientes
)
from gestion_acceso import (
    login, menu_usuarios, menu_configuracion_sistema,
    cambiar_contrasena_usuario, inicializar_admin_si_no_existe, ROLES_PERMISOS,
    menu_ver_log_sistema
)

load_dotenv()

def menu_gestion_inventario(usuario: str):
    user_data = db_manager.get_user_by_username(usuario)
    rol_actual = user_data['rol']
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        opciones_disponibles = []
        
        # Construcción dinámica del menú
        if "registrar_equipo" in ROLES_PERMISOS[rol_actual]: 
            opciones_disponibles.append("Registrar nuevo equipo")
        if "gestionar_equipo" in ROLES_PERMISOS[rol_actual]: 
            opciones_disponibles.append("Gestionar Equipos")
        if "ver_inventario" in ROLES_PERMISOS[rol_actual]: 
            opciones_disponibles.append("Ver Inventario en Excel")
        
        if "gestionar_pendientes" in ROLES_PERMISOS[rol_actual]:
            mantenimientos_pendientes = len([e for e in db_manager.get_all_equipos() if e.get('estado') == "En mantenimiento"])
            devoluciones_pendientes = len([e for e in db_manager.get_all_equipos() if e.get('estado') == "Pendiente Devolución a Proveedor"])
            total_pendientes = mantenimientos_pendientes + devoluciones_pendientes
            
            color = Fore.GREEN
            if total_pendientes > 0:
                color = Fore.YELLOW if total_pendientes == 1 else Fore.RED
            
            texto_menu_pendientes = f"Gestionar Mantenimientos y Devoluciones {color}({total_pendientes} Pendientes){Style.RESET_ALL}"
            opciones_disponibles.append(texto_menu_pendientes)

        opciones_disponibles.append("Volver al menú principal")

        mostrar_menu(opciones_disponibles, titulo="Módulo de Gestión de Inventario")
        opcion_input = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
        
        try:
            opciones_map = {str(i+1): texto for i, texto in enumerate(opciones_disponibles)}
            opcion_texto = opciones_map.get(opcion_input)

            if not opcion_texto:
                print(Fore.RED + "Opción no válida.")
                pausar_pantalla()
                continue

            # --- CORRECCIÓN APLICADA AQUÍ ---
            # Se usa 'in' para que funcione aunque el texto tenga contadores dinámicos
            if "Registrar nuevo equipo" in opcion_texto:
                registrar_equipo(usuario)
            elif "Gestionar Equipos" in opcion_texto:
                gestionar_equipos(usuario)
            elif "Ver Inventario en Excel" in opcion_texto:
                menu_ver_inventario_excel(usuario)
            elif "Gestionar Mantenimientos y Devoluciones" in opcion_texto:
                menu_gestionar_pendientes(usuario)
            elif "Volver al menú principal" in opcion_texto:
                break
            else: 
                print(Fore.RED + "Opción no válida.")
                pausar_pantalla()

        except (ValueError, IndexError):
            print(Fore.RED + "Entrada no válida.")

def menu_gestion_acceso_sistema(usuario: str):
    user_data = db_manager.get_user_by_username(usuario)
    rol_actual = user_data['rol']
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        opciones_disponibles = []
        if "gestionar_usuarios" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Gestión de usuarios")
        if "configurar_sistema" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Configuración del Sistema")
        if "ver_historico" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Ver Log de Actividad del Sistema")
        opciones_disponibles.append("Cambiar mi contraseña")
        opciones_disponibles.append("Volver al menú principal")
        
        mostrar_menu(opciones_disponibles, titulo="Módulo de Acceso y Sistema")
        opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
        
        try:
            opcion_idx = int(opcion) - 1
            if 0 <= opcion_idx < len(opciones_disponibles):
                opcion_texto = opciones_disponibles[opcion_idx]
                if opcion_texto == "Gestión de usuarios": menu_usuarios(usuario)
                elif opcion_texto == "Configuración del Sistema": menu_configuracion_sistema(usuario)
                elif opcion_texto == "Ver Log de Actividad del Sistema": menu_ver_log_sistema(usuario)
                elif opcion_texto == "Cambiar mi contraseña": cambiar_contrasena_usuario(usuario)
                elif opcion_texto == "Volver al menú principal": break
            else: print(Fore.RED + "Opción no válida.")
        except (ValueError, IndexError):
            print(Fore.RED + "Entrada no válida.")

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