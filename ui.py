# ui.py
from colorama import init, Fore, Style
from typing import List

# Inicializar colorama
init(autoreset=True)

# Variable global para el usuario logueado
USUARIO_ACTUAL = None

def mostrar_encabezado(titulo: str, ancho: int = 80, color: str = Fore.CYAN):
    """Muestra un encabezado con formato en la consola."""
    print("\n" + color + "═" * ancho)
    print(f" {titulo.upper()} ".center(ancho, ' '))
    print("═" * ancho + Style.RESET_ALL)

def mostrar_menu(opciones: List[str], titulo: str):
    """Muestra un menú de opciones con formato."""
    mostrar_encabezado(titulo, color=Fore.MAGENTA)
    for i, opcion in enumerate(opciones, 1):
        print(Fore.YELLOW + f"{i}." + Style.RESET_ALL + f" {opcion}")
    print(Fore.MAGENTA + "═" * 80 + Style.RESET_ALL)

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