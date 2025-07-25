# ui.py
import os
import getpass
from typing import List
from colorama import init, Fore, Style, Back

# Variables globales para el usuario logueado
USUARIO_ACTUAL = None
ROL_ACTUAL = None
NOMBRE_COMPLETO_USUARIO = None

# Inicializar colorama
init(autoreset=True)

# --- Funciones de bajo nivel para entrada de contraseña con asteriscos ---
try:
    # Para Windows
    import msvcrt
    def get_char():
        return msvcrt.getch().decode('utf-8', errors='ignore')
except ImportError:
    # Para Unix (Linux, macOS)
    import sys, tty, termios
    def get_char():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def solicitar_contrasena_con_asteriscos(prompt: str) -> str:
    """Solicita una contraseña mostrando asteriscos en lugar de los caracteres."""
    print(prompt, end="", flush=True)
    password = ""
    while True:
        char = get_char()
        if char in ('\r', '\n'): # Enter
            print()
            break
        elif char in ('\b', '\x7f'): # Backspace/Delete
            if len(password) > 0:
                print("\b \b", end="", flush=True)
                password = password[:-1]
        elif char == '\x03': # Ctrl+C
             raise KeyboardInterrupt
        else:
            password += char
            print("*", end="", flush=True)
    return password

# --- Funciones de UI principales ---

def mostrar_encabezado(titulo: str, ancho: int = 80, color: str = Fore.WHITE):
    """Limpia la pantalla y muestra un encabezado permanente y uno específico."""
    os.system('cls' if os.name == 'nt' else 'clear')

    # Encabezado permanente
    print(Fore.WHITE + Style.BRIGHT + "═" * ancho)
    print(Back.WHITE + Style.DIM + Fore.BLACK + " Control de Inventario de Equipos (CIE) ".center(ancho, ' ') + Style.RESET_ALL)
    
    # Línea dinámica: Muestra créditos o información del usuario
    if USUARIO_ACTUAL and ROL_ACTUAL and NOMBRE_COMPLETO_USUARIO:
        info_usuario = f"{NOMBRE_COMPLETO_USUARIO.title()} ({USUARIO_ACTUAL.upper()}) / Rol: {ROL_ACTUAL.title()}"
        print(Back.WHITE + Fore.BLACK + Style.BRIGHT + f" {info_usuario} ".center(ancho, ' ') + Style.RESET_ALL)
    else:
        print(Back.WHITE + Fore.BLACK + Style.BRIGHT + " Powered by Jairo Sevilla ".center(ancho, ' ') + Style.RESET_ALL)
        
    print(Fore.WHITE + Style.BRIGHT + "═" * ancho + Style.RESET_ALL)

    # Encabezado específico del menú
    if titulo:
        print("\n" + color + Style.BRIGHT + f" {titulo.upper()} ".center(ancho, ' ') + Style.RESET_ALL)
        print(color + "─" * ancho + Style.RESET_ALL)

def mostrar_menu(opciones: List[str], titulo: str):
    """Muestra un menú de opciones con formato."""
    mostrar_encabezado(titulo, color=Fore.WHITE)
    for i, opcion in enumerate(opciones, 1):
        print(Fore.YELLOW + f"{i}." + Style.RESET_ALL + f" {opcion}")
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

def solicitar_input(prompt: str, default: str = "") -> str:
    """Solicita un input al usuario."""
    return input(prompt + Style.RESET_ALL).strip() or default