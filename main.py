# main.py
import os
from colorama import Fore, Back, Style
from dotenv import load_dotenv
from datetime import datetime

from database import db_manager
from ui import (
    mostrar_encabezado, mostrar_menu, pausar_pantalla
)
from gestion_inventario import (
    registrar_equipo, gestionar_equipos,
    menu_gestionar_pendientes
)
from gestion_reportes import (
    menu_ver_inventario, menu_ver_ultimos_movimientos,
    generar_excel_inventario, generar_excel_devueltos_proveedor,
    generar_excel_historico
)
from gestion_acceso import (
    login, menu_usuarios, menu_configuracion_sistema,
    cambiar_contrasena_usuario, inicializar_admin_si_no_existe, ROLES_PERMISOS,
    menu_ver_log_sistema
)
from estadisticas import mostrar_estadisticas

load_dotenv()

def menu_gestion_inventario(usuario: str):
    user_data = db_manager.get_user_by_username(usuario)
    rol_actual = user_data['rol']
    
    while True:
        # Se elimina os.system('cls'...) de aquí
        opciones_disponibles = []
        
        # Construcción dinámica del menú
        if "registrar_equipo" in ROLES_PERMISOS[rol_actual]: 
            opciones_disponibles.append("Registrar nuevo equipo")
        if "gestionar_equipo" in ROLES_PERMISOS[rol_actual]: 
            opciones_disponibles.append("Gestionar Equipos")
        
        if "gestionar_pendientes" in ROLES_PERMISOS[rol_actual]:
            equipos = db_manager.get_all_equipos()
            mantenimientos_pendientes = len([e for e in equipos if e.get('estado') == "En mantenimiento"])
            devoluciones_pendientes = len([e for e in equipos if e.get('estado') == "Pendiente Devolución a Proveedor"])
            renovaciones_pendientes = len([e for e in equipos if e.get('estado') == "Renovación"])
            total_pendientes = mantenimientos_pendientes + devoluciones_pendientes + renovaciones_pendientes
            
            color = Fore.GREEN
            if total_pendientes > 0:
                color = Fore.YELLOW if total_pendientes <= 2 else Fore.RED
            
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
            
            if "Registrar nuevo equipo" in opcion_texto:
                registrar_equipo(usuario)
            elif "Gestionar Equipos" in opcion_texto:
                gestionar_equipos(usuario)
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
        # Se elimina os.system('cls'...) de aquí
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

def menu_accesos_rapidos():
    """Muestra una pantalla con la lista de accesos rápidos disponibles."""
    # Se elimina os.system('cls'...) de aquí
    mostrar_encabezado("Accesos Rápidos Disponibles", color=Fore.CYAN)
    print(f"  {Fore.YELLOW}rq{Style.RESET_ALL}  - Registrar un nuevo equipo")
    print(f"  {Fore.YELLOW}gq{Style.RESET_ALL}  - Gestionar un equipo existente")
    print(f"  {Fore.YELLOW}gmd{Style.RESET_ALL} - Gestionar Mantenimientos, Devoluciones y Renovaciones")
    print(f"  {Fore.YELLOW}vm{Style.RESET_ALL} - Ver los últimos 20 movimientos")
    print(f"\n  --- Reportes en Excel ---")
    print(f"  {Fore.YELLOW}ria{Style.RESET_ALL} - Reporte de Inventario Actual")
    print(f"  {Fore.YELLOW}red{Style.RESET_ALL} - Reporte de Equipos Devueltos")
    print(f"  {Fore.YELLOW}rhc{Style.RESET_ALL} - Reporte Histórico Completo (Log)")
    print("\n" + Fore.CYAN + "Escribe estos comandos en el menú principal para ir directamente a la función." + Style.RESET_ALL)
    pausar_pantalla()

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
        # La limpieza y el encabezado ahora son manejados por mostrar_menu
        
        opciones_principales = [
            "Estadísticas de Inventario",
            "Gestión de Inventario",
            "Ver Inventario y Reportes",
            "Gestión de Acceso y Sistema",
            "Aprender Accesos Rápidos",
            "Salir"
        ]
        
        # Construimos un título dinámico para el menú principal
        titulo_principal = f"MENÚ PRINCIPAL - Usuario: {usuario_logueado} (Rol: {rol_actual})"
        if ENVIRONMENT == 'development':
            titulo_principal += " --- MODO DESARROLLO ---"
        
        mostrar_menu(opciones_principales, titulo=titulo_principal)
        
        opcion = input(Fore.YELLOW + "Seleccione un módulo o ingrese un acceso rápido: " + Style.RESET_ALL).strip().lower()
        
        shortcuts = {
            'rq': lambda: registrar_equipo(usuario_logueado),
            'gq': lambda: gestionar_equipos(usuario_logueado),
            'gmd': lambda: menu_gestionar_pendientes(usuario_logueado),
            'vm': lambda: menu_ver_ultimos_movimientos(usuario_logueado),
            'ria': lambda: generar_excel_inventario(usuario_logueado),
            'red': lambda: generar_excel_devueltos_proveedor(usuario_logueado),
            'rhc': lambda: generar_excel_historico(usuario_logueado),
        }
        
        if opcion in shortcuts:
            shortcuts[opcion]()

        elif opcion == '1':
            mostrar_estadisticas(usuario_logueado)
        elif opcion == '2':
            menu_gestion_inventario(usuario_logueado)
        elif opcion == '3':
            menu_ver_inventario(usuario_logueado)
        elif opcion == '4':
            menu_gestion_acceso_sistema(usuario_logueado)
        elif opcion == '5':
            menu_accesos_rapidos()
        elif opcion == '6':
            break
        else:
            if opcion not in shortcuts:
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