# estadisticas.py
import os
from datetime import datetime
from colorama import Fore, Style, init
from database import db_manager
from ui import mostrar_encabezado, pausar_pantalla

# Inicializar colorama
init(autoreset=True)

def obtener_color_por_cantidad(cantidad, umbral_bajo=1, umbral_alto=5):
    """Devuelve un color basado en la cantidad."""
    if cantidad == 0:
        return Fore.GREEN
    elif cantidad <= umbral_bajo:
        return Fore.YELLOW
    else:
        return Fore.RED

def mostrar_estadisticas(usuario: str):
    """
    Muestra el panel de control principal con un resumen completo del inventario.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    mostrar_encabezado("Estadísticas de Inventario", color=Fore.BLUE)

    # --- 1. Obtención de Datos ---
    equipos = db_manager.get_all_equipos()
    
    # Resumen por estado
    estados = {
        "Disponible": 0,
        "Asignado": 0,
        "En préstamo": 0,
        "En mantenimiento": 0,
        "Pendiente Devolución a Proveedor": 0,
        "Devuelto a Proveedor": 0,
    }
    for equipo in equipos:
        if equipo['estado'] in estados:
            estados[equipo['estado']] += 1
    
    total_equipos_activos = sum(v for k, v in estados.items() if k != "Devuelto a Proveedor")

    # Últimos 10 movimientos
    movimientos_recientes = db_manager.get_all_log_inventario()[:10]

    # --- 2. Renderizado del Dashboard ---
    
    # Sección de Resumen General
    print(Fore.CYAN + "--- Resumen General del Inventario ---" + Style.RESET_ALL)
    print(f"  Total de Equipos Activos: {Fore.YELLOW}{total_equipos_activos}{Style.RESET_ALL}")
    print(f"  Equipos Devueltos a Proveedor: {Fore.YELLOW}{estados['Devuelto a Proveedor']}{Style.RESET_ALL}")
    print("-" * 40)

    # Sección de Estado Actual
    print(Fore.CYAN + "\n--- Estado Actual de Equipos Activos ---" + Style.RESET_ALL)
    print(f"  {Fore.WHITE}Disponibles:{' ' * (28 - len('Disponibles:'))}{Fore.YELLOW}{estados['Disponible']}{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}Asignados / En Préstamo:{' ' * (28 - len('Asignados / En Préstamo:'))}{Fore.YELLOW}{estados['Asignado'] + estados['En préstamo']}{Style.RESET_ALL}")
    
    # Aplicar color dinámico solo a los valores que lo necesitan
    color_mantenimiento = obtener_color_por_cantidad(estados['En mantenimiento'])
    print(f"  {Fore.WHITE}En Mantenimiento:{' ' * (28 - len('En Mantenimiento:'))}{color_mantenimiento}{estados['En mantenimiento']}{Style.RESET_ALL}")
    
    color_devolucion = obtener_color_por_cantidad(estados['Pendiente Devolución a Proveedor'])
    print(f"  {Fore.WHITE}Pendientes de Devolución:{' ' * (28 - len('Pendientes de Devolución:'))}{color_devolucion}{estados['Pendiente Devolución a Proveedor']}{Style.RESET_ALL}")
    print("-" * 40)

    # Sección de Movimientos Recientes
    print(Fore.CYAN + f"\n--- Últimos {len(movimientos_recientes)} Movimientos del Inventario ---" + Style.RESET_ALL)
    if not movimientos_recientes:
        print(Fore.GREEN + "  No se han registrado movimientos recientemente.")
    else:
        print(f"  {Fore.WHITE}{'FECHA':<20} {'PLACA':<15} {'ACCIÓN':<30} {'USUARIO'}{Style.RESET_ALL}")
        print(f"  {'-'*18} {'-'*13} {'-'*28} {'-'*15}")
        for mov in movimientos_recientes:
            fecha_obj = datetime.strptime(mov['fecha'], "%Y-%m-%d %H:%M:%S")
            fecha_formateada = fecha_obj.strftime("%d/%m/%Y %H:%M")
            accion = mov['accion']
            if len(accion) > 28:
                accion = accion[:27] + "..."
            print(f"  {fecha_formateada:<20} {mov['equipo_placa']:<15} {accion:<30} {mov['usuario']}")
    
    pausar_pantalla()