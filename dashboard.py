# dashboard.py
import os
from datetime import datetime, timedelta
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

def mostrar_dashboard(usuario: str):
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

    # Movimientos recientes (últimas 48 horas)
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(hours=48)
    movimientos_recientes = db_manager.get_movimientos_en_rango_de_fechas(
        fecha_inicio.strftime("%Y-%m-%d %H:%M:%S"),
        fecha_fin.strftime("%Y-%m-%d %H:%M:%S")
    )

    # --- 2. Renderizado del Dashboard ---
    
    # Sección de Resumen General
    print(Fore.CYAN + "--- Resumen General del Inventario ---" + Style.RESET_ALL)
    print(f"  Total de Equipos Activos: {Fore.BLUE}{total_equipos_activos}{Style.RESET_ALL}")
    print(f"  Equipos Devueltos a Proveedor: {Fore.WHITE}{estados['Devuelto a Proveedor']}{Style.RESET_ALL}")
    print("-" * 40)

    # Sección de Estado Actual
    print(Fore.CYAN + "\n--- Estado Actual de Equipos Activos ---" + Style.RESET_ALL)
    print(f"  {Fore.GREEN}Disponibles:{' ' * (20 - len('Disponibles'))}{estados['Disponible']}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Asignados / En Préstamo:{' ' * (20 - len('Asignados / En Préstamo'))}{estados['Asignado'] + estados['En préstamo']}{Style.RESET_ALL}")
    
    color_mantenimiento = obtener_color_por_cantidad(estados['En mantenimiento'])
    print(f"  {color_mantenimiento}En Mantenimiento:{' ' * (20 - len('En Mantenimiento'))}{estados['En mantenimiento']}{Style.RESET_ALL}")
    
    color_devolucion = obtener_color_por_cantidad(estados['Pendiente Devolución a Proveedor'])
    print(f"  {color_devolucion}Pendientes de Devolución:{' ' * (20 - len('Pendientes de Devolución'))}{estados['Pendiente Devolución a Proveedor']}{Style.RESET_ALL}")
    print("-" * 40)

    # Sección de Movimientos Recientes
    print(Fore.CYAN + f"\n--- Movimientos en las Últimas 48 Horas ({len(movimientos_recientes)} encontrados) ---" + Style.RESET_ALL)
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
