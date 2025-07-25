# ui.py
import os
from colorama import init, Fore, Style, Back
from typing import List

# Inicializar colorama
init(autoreset=True)

# Variable global para el usuario logueado
USUARIO_ACTUAL = None

def mostrar_encabezado(titulo: str, ancho: int = 80, color: str = Fore.CYAN):
    """Limpia la pantalla y muestra un encabezado permanente y uno específico."""
    # Limpiar pantalla
    os.system('cls' if os.name == 'nt' else 'clear')

    # Encabezado permanente
    print(Fore.WHITE + Style.BRIGHT + "═" * ancho)
    print(Back.WHITE + Style.DIM + Fore.BLACK + " Control de Inventario de Equipos (CIE) ".center(ancho, ' ') + Style.RESET_ALL)
    print(Back.WHITE + Fore.BLACK + Style.BRIGHT + " Powered by Jairo Sevilla ".center(ancho, ' ') + Style.RESET_ALL)
    print(Fore.WHITE + Style.BRIGHT + "═" * ancho + Style.RESET_ALL)

    # Encabezado específico del menú
    if titulo:
        print("\n" + color + Style.BRIGHT + f" {titulo.upper()} ".center(ancho, ' ') + Style.RESET_ALL)
        print(color + "─" * ancho + Style.RESET_ALL)


def mostrar_menu(opciones: List[str], titulo: str):
    """Muestra un menú de opciones con formato."""
    # Se usa color blanco para el título del menú
    mostrar_encabezado(titulo, color=Fore.WHITE)
    for i, opcion in enumerate(opciones, 1):
        print(Fore.YELLOW + f"{i}." + Style.RESET_ALL + f" {opcion}")
    # La línea final del menú ahora es blanca y en negrita
    print(Style.BRIGHT + Fore.WHITE + "═" * 80 + Style.RESET_ALL)


def pausar_pantalla():
    """Pausa la ejecución hasta que el usuario presione Enter."""
    input(Fore.CYAN + "\nPresione Enter para continuar..." + Style.RESET_ALL)

def confirmar_con_placa(placa_correcta: str) -> bool:
    while True:
        print(Fore.CYAN + "💡 Escriba 'C' para cancelar la operación." + Style.RESET_ALL)
        confirmacion_placa = input(Fore.YELLOW + "🔑 Para confirmar, ingrese la placa del equipo: " + Style.RESET_ALL).strip().upper()
        
        if confirmacion_placa == placa_correcta:
            return True
        elif confirmacion_placa == 'C':
            print(Fore.YELLOW + "\n🚫 Operación cancelada por el usuario." + Style.RESET_ALL)
            pausar_pantalla()
            return False
        else:
            print(Fore.RED + "\n❌ Placa incorrecta. Por favor, intente de nuevo.")