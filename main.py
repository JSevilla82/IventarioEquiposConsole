# main.py
import os
from colorama import Fore, Back, Style
from dotenv import load_dotenv
from datetime import datetime

from database import db_manager
from ui import (
    mostrar_encabezado, mostrar_menu, pausar_pantalla
)
# MODIFICACIÓN 1: Se corrigen las funciones importadas
from gestion_inventario import (
    registrar_equipo, gestionar_equipos, menu_busqueda_avanzada,
    gestionar_mantenimientos, gestionar_devoluciones_proveedor,
    gestionar_renovaciones
)
from gestion_reportes import (
    menu_ver_inventario, menu_ver_ultimos_movimientos,
    generar_excel_inventario, generar_excel_devueltos_proveedor,
    generar_excel_historico
)
# MODIFICACIÓN: Se importa la nueva función para gestionar proveedores
from gestion_acceso import (
    login, menu_usuarios, cambiar_contrasena_usuario, inicializar_admin_si_no_existe, ROLES_PERMISOS,
    menu_ver_log_sistema, gestionar_parametros, gestionar_proveedores
)
from estadisticas import mostrar_estadisticas

load_dotenv()


def menu_gestion_inventario(usuario: str):
    user_data = db_manager.get_user_by_username(usuario)
    rol_actual = user_data['rol']
    
    while True:
        mostrar_encabezado("Módulo de Gestión de Inventario")

        # Usaremos un diccionario para mapear el texto de la opción a la función que debe llamar
        opciones_map = {}

        if "registrar_equipo" in ROLES_PERMISOS[rol_actual]: 
            opciones_map["Registrar nuevo equipo"] = lambda: registrar_equipo(usuario)
        if "gestionar_equipo" in ROLES_PERMISOS[rol_actual]: 
            opciones_map["Gestionar Equipos"] = lambda: gestionar_equipos(usuario)
        if "ver_inventario" in ROLES_PERMISOS[rol_actual]:
            opciones_map["Búsqueda Avanzada de Equipos"] = lambda: menu_busqueda_avanzada(usuario)

        if "gestionar_pendientes" in ROLES_PERMISOS[rol_actual]:
            equipos = db_manager.get_all_equipos()
            
            mantenimientos = len([e for e in equipos if e.get('estado') == "En mantenimiento"])
            devoluciones = len([e for e in equipos if e.get('estado') == "Pendiente Devolución a Proveedor"])
            renovaciones = len([e for e in equipos if e.get('estado') == "Renovación"])

            color_mantenimiento = Fore.GREEN if mantenimientos == 0 else Fore.YELLOW
            color_devoluciones = Fore.GREEN if devoluciones == 0 else Fore.YELLOW
            color_renovaciones = Fore.GREEN if renovaciones == 0 else Fore.YELLOW

            # Creamos los textos dinámicos y los asociamos directamente a su función
            texto_mantenimiento = f"Gestionar Equipos en Mantenimiento {color_mantenimiento}({mantenimientos}){Style.RESET_ALL}"
            texto_devoluciones = f"Gestionar Devoluciones a Proveedor {color_devoluciones}({devoluciones}){Style.RESET_ALL}"
            texto_renovaciones = f"Gestionar Renovaciones Pendientes {color_renovaciones}({renovaciones}){Style.RESET_ALL}"
            
            opciones_map[texto_mantenimiento] = lambda: gestionar_mantenimientos(usuario)
            opciones_map[texto_devoluciones] = lambda: gestionar_devoluciones_proveedor(usuario)
            opciones_map[texto_renovaciones] = lambda: gestionar_renovaciones(usuario)
        
        opciones_map["Volver"] = None 

        # Convertimos las llaves del diccionario en una lista para poder enumerarlas
        opciones_disponibles = list(opciones_map.keys())
        
        mostrar_menu([], titulo="")
        for i, texto_opcion in enumerate(opciones_disponibles, 1):
            print(Fore.YELLOW + f"{i}." + Style.RESET_ALL + f" {texto_opcion}")
        print(Style.BRIGHT + Fore.WHITE + "═" * 80 + Style.RESET_ALL)

        opcion_input = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
            
        try:
            opcion_idx = int(opcion_input) - 1
            if 0 <= opcion_idx < len(opciones_disponibles):
                # Obtenemos el texto de la opción seleccionada por el usuario
                texto_seleccionado = opciones_disponibles[opcion_idx]
                # Usamos ese texto para encontrar la función correcta en el diccionario
                funcion_a_llamar = opciones_map[texto_seleccionado]
                
                if funcion_a_llamar:
                    funcion_a_llamar() # Ejecutamos la función
                else:
                    # Si la función es None, es la opción "Volver"
                    break
            else:
                print(Fore.RED + "Opción no válida.")
                pausar_pantalla()
        except (ValueError, IndexError):
            print(Fore.RED + "Entrada no válida.")
            pausar_pantalla()

# --- NUEVA FUNCIÓN ---
def menu_configuracion_sistema(usuario: str):
    """Muestra el menú para la configuración de parámetros del sistema."""
    user_data = db_manager.get_user_by_username(usuario)
    rol_actual = user_data['rol']

    if "configurar_sistema" not in ROLES_PERMISOS.get(rol_actual, {}):
        print(Fore.RED + "❌ No tiene permisos para acceder a la configuración del sistema.")
        pausar_pantalla()
        return

    while True:
        mostrar_encabezado("Módulo de Configuración del Sistema")
        opciones_menu = [
            "Gestionar Tipos de Equipo", 
            "Gestionar Marcas", 
            "Gestionar Dominios de Correo permitidos", # --- TEXTO MODIFICADO ---
            "Gestionar Proveedores", # --- NUEVA OPCIÓN ---
            "Volver"
        ]
        mostrar_menu(opciones_menu, titulo="Parámetros del Sistema")
        
        opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
        
        if opcion == '1':
            gestionar_parametros(usuario, 'tipo_equipo', 'Tipo de Equipo')
        elif opcion == '2':
            gestionar_parametros(usuario, 'marca_equipo', 'Marca')
        elif opcion == '3':
            gestionar_parametros(usuario, 'dominio_correo', 'Dominio de Correo Permitido')
        elif opcion == '4':
            gestionar_proveedores(usuario) # --- LLAMADA A LA NUEVA FUNCIÓN ---
        elif opcion == '5':
            break
        else:
            print(Fore.RED + "Opción no válida.")
            pausar_pantalla()

# --- FUNCIÓN RENOMBRADA Y MODIFICADA ---
def menu_gestion_accesos(usuario: str):
    user_data = db_manager.get_user_by_username(usuario)
    rol_actual = user_data['rol']
    
    while True:
        mostrar_encabezado("Módulo de Gestión de Accesos")

        opciones_disponibles = []
        if "gestionar_usuarios" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Gestión de usuarios")
        if "ver_historico" in ROLES_PERMISOS[rol_actual]: opciones_disponibles.append("Ver Log de Actividad del Sistema")
        opciones_disponibles.append("Cambiar mi contraseña")
        opciones_disponibles.append("Volver")
        
        mostrar_menu([], titulo="")
        for i, opcion in enumerate(opciones_disponibles, 1):
            print(Fore.YELLOW + f"{i}." + Style.RESET_ALL + f" {opcion}")
        print(Style.BRIGHT + Fore.WHITE + "═" * 80 + Style.RESET_ALL)
        
        opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()

        try:
            opcion_idx = int(opcion) - 1
            if 0 <= opcion_idx < len(opciones_disponibles):
                opcion_texto = opciones_disponibles[opcion_idx]
                if opcion_texto == "Gestión de usuarios": menu_usuarios(usuario)
                elif opcion_texto == "Ver Log de Actividad del Sistema": menu_ver_log_sistema(usuario)
                elif opcion_texto == "Cambiar mi contraseña": cambiar_contrasena_usuario(usuario)
                elif opcion_texto == "Volver": break
            else: print(Fore.RED + "Opción no válida.")
        except (ValueError, IndexError):
            print(Fore.RED + "Entrada no válida.")

def menu_accesos_rapidos():
    """Muestra una pantalla con la lista de accesos rápidos disponibles."""
    mostrar_encabezado("Accesos Rápidos Disponibles", color=Fore.CYAN)
    print(f"  {Fore.YELLOW}rq{Style.RESET_ALL}  - Registrar un nuevo equipo")
    print(f"  {Fore.YELLOW}gq{Style.RESET_ALL}  - Gestionar un equipo existente")
    print(f"  {Fore.YELLOW}vm{Style.RESET_ALL} - Ver los últimos 20 movimientos")
    print(f"\n  --- Reportes en Excel ---")
    print(f"  {Fore.YELLOW}ria{Style.RESET_ALL} - Reporte de Inventario Actual")
    print(f"  {Fore.YELLOW}red{Style.RESET_ALL} - Reporte de Equipos Devueltos")
    print(f"  {Fore.YELLOW}rhc{Style.RESET_ALL} - Reporte Histórico Completo (Log)")
    print("\n" + Fore.CYAN + "Escribe estos comandos en el menú principal para ir directamente a la función." + Style.RESET_ALL)
    pausar_pantalla()


# --- FUNCIÓN PRINCIPAL MODIFICADA Y CORREGIDA ---
def menu_principal():
    inicializar_admin_si_no_existe()
    
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production") 

    while True: # Bucle principal que mantiene el programa corriendo
        usuario_logueado = None
        import ui

        ui.USUARIO_ACTUAL = None
        ui.ROL_ACTUAL = None
        ui.NOMBRE_COMPLETO_USUARIO = None

        if ENVIRONMENT == 'development':
            usuario_logueado = "admin"
        else:
            while usuario_logueado is None:
                usuario_logueado = login()
                if usuario_logueado is None:
                    if input(Fore.RED + "¿Salir del programa? (S/N): " + Style.RESET_ALL).strip().upper() == 'S':
                        print(Fore.GREEN + "\n¡Gracias por usar el Sistema de Gestión de Inventario!")
                        db_manager.close()
                        print(Fore.GREEN + "\nConexión a la base de datos cerrada.")
                        return # Termina la ejecución del programa

        user_data = db_manager.get_user_by_username(usuario_logueado)
        ui.USUARIO_ACTUAL = usuario_logueado
        ui.ROL_ACTUAL = user_data['rol']
        ui.NOMBRE_COMPLETO_USUARIO = user_data.get('nombre_completo', usuario_logueado)

        while usuario_logueado: # Bucle de sesión de usuario
            mostrar_encabezado("Menú Principal")
            
            opciones_principales = [
                "📊 Estadísticas de Inventario",
                "📦 Gestión de Inventario",
                "📋 Ver Inventario y Reportes",
                "👤 Gestión de Accesos",
                "⚙️ Configuración del Sistema",
                "⚡ Aprender Accesos Rápidos",
                "↪️ Cerrar Sesión"
            ]
            
            mostrar_menu([], titulo="")
            for i, opcion in enumerate(opciones_principales, 1):
                print(Fore.YELLOW + f"{i}." + Style.RESET_ALL + f" {opcion}")
            print(Style.BRIGHT + Fore.WHITE + "═" * 80 + Style.RESET_ALL)
            
            opcion = input(Fore.YELLOW + "Seleccione un módulo o ingrese un acceso rápido: " + Style.RESET_ALL).strip().lower()
            
            shortcuts = {
                'rq': lambda: registrar_equipo(usuario_logueado),
                'gq': lambda: gestionar_equipos(usuario_logueado),
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
                menu_gestion_accesos(usuario_logueado)
            elif opcion == '5':
                menu_configuracion_sistema(usuario_logueado)
            elif opcion == '6':
                menu_accesos_rapidos()
            elif opcion == '7':
                print(Fore.GREEN + "\nCerrando sesión...")
                usuario_logueado = None # Rompe el bucle de sesión y vuelve al login
                pausar_pantalla()
            else:
                if opcion not in shortcuts:
                    print(Fore.RED + "\n❌ Opción no válida.")
                    pausar_pantalla()


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