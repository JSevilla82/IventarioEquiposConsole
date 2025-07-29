# app/ui.py
import os
from typing import List, Dict
from colorama import init, Fore, Style, Back

try:
    import msvcrt
    def get_char(): return msvcrt.getch().decode('utf-8', errors='ignore')
except ImportError:
    import sys, tty, termios
    def get_char():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno()); ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

init(autoreset=True)

def mostrar_encabezado(titulo: str, ancho: int = 80, color: str = Fore.WHITE, usuario_logueado: dict = None):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.WHITE + Style.BRIGHT + "═" * ancho)
    print(Back.WHITE + Style.DIM + Fore.BLACK + " Control de Inventario de Equipos (CIE) ".center(ancho, ' ') + Style.RESET_ALL)
    if usuario_logueado:
        info_usuario = f"{usuario_logueado['nombre_completo'].title()} ({usuario_logueado['username'].upper()}) / Rol: {usuario_logueado['nombre_rol'].title()}"
        print(Back.WHITE + Fore.BLACK + Style.BRIGHT + f" {info_usuario} ".center(ancho, ' ') + Style.RESET_ALL)
    else:
        print(Back.WHITE + Fore.BLACK + Style.BRIGHT + " Powered by Jairo Sevilla ".center(ancho, ' ') + Style.RESET_ALL)
    print(Fore.WHITE + Style.BRIGHT + "═" * ancho + Style.RESET_ALL)
    print("\n" + color + Style.BRIGHT + f" {titulo.upper()} ".center(ancho, ' ') + Style.RESET_ALL)
    print(color + "─" * ancho + Style.RESET_ALL)

def mostrar_menu(opciones: List[str]):
    for i, opcion in enumerate(opciones, 1):
        print(Fore.YELLOW + f"{i}." + Style.RESET_ALL + f" {opcion}")
    print(Style.BRIGHT + Fore.WHITE + "═" * 80 + Style.RESET_ALL)

def pausar_pantalla():
    input(Fore.CYAN + "\nPresione Enter para continuar..." + Style.RESET_ALL)

def solicitar_input(prompt: str, default: str = "") -> str:
    return input(prompt + Style.RESET_ALL).strip() or default

def solicitar_contrasena_con_asteriscos(prompt: str) -> str:
    print(prompt, end="", flush=True); password = ""
    while True:
        char = get_char()
        if char in ('\r', '\n'): print(); break
        elif char in ('\b', '\x7f'):
            if len(password) > 0: print("\b \b", end="", flush=True); password = password[:-1]
        elif char == '\x03': raise KeyboardInterrupt
        else: password += char; print("*", end="", flush=True)
    return password

def mostrar_formulario_interactivo(titulo: str, campos: List[str], datos: Dict, indice_actual: int, usuario_logueado: dict):
    mostrar_encabezado(titulo, color=Fore.BLUE, usuario_logueado=usuario_logueado)
    print(Fore.CYAN + "💡 Complete los siguientes campos. Puede presionar Ctrl+C para cancelar." + Style.RESET_ALL)
    for i, campo in enumerate(campos):
        indicador = Fore.YELLOW + " -> " if i == indice_actual else "    "
        valor_mostrado = f"{Fore.GREEN}{datos.get(campo, '')}{Style.RESET_ALL}" if datos.get(campo) else ""
        print(f"{indicador}{campo.ljust(30)}: {valor_mostrado}")
    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

def mostrar_tabla_usuarios(usuarios: List[Dict]):
    print(f"{Fore.CYAN}{'NOMBRE COMPLETO':<30} {'USUARIO':<20} {'ESTADO':<15} {'ÚLTIMA SESIÓN'}{Style.RESET_ALL}")
    print(Fore.CYAN + "-" * 90 + Style.RESET_ALL)
    if not usuarios:
        print(Fore.YELLOW + "No hay otros usuarios registrados.")
    else:
        for user in usuarios:
            estado = (Fore.GREEN + "Activo") if user['is_active'] else (Fore.RED + "Inactivo")
            nombre = user.get('nombre_completo') or 'N/A'
            ultima_sesion = user.get('ultima_sesion', 'Nunca')
            print(f"{nombre:<30} {user['username']:<20} {estado:<15}{Style.RESET_ALL} {ultima_sesion}")
    print(Fore.CYAN + "-" * 90 + Style.RESET_ALL)

def mostrar_panel_info(titulo: str, info_dict: Dict):
    print(Fore.CYAN + f"--- {titulo} ---" + Style.RESET_ALL)
    for clave, valor in info_dict.items():
        print(f"  {clave.ljust(25)}: {valor}")
    print(Fore.CYAN + "-" * (len(titulo) + 8) + Style.RESET_ALL)

def mostrar_log_sistema(logs: List[Dict]):
    print(f"{Fore.CYAN}{'FECHA':<22} {'USUARIO':<20} {'ACCIÓN':<25} {'DETALLES'}{Style.RESET_ALL}")
    print(Fore.CYAN + "-" * 90 + Style.RESET_ALL)
    if not logs:
        print(Fore.YELLOW + "No hay registros de actividad en el sistema.")
    else:
        for log in logs:
            detalles = log['detalles']
            if len(detalles) > 40: detalles = detalles[:37] + "..."
            print(f"{log['fecha']:<22} {log['usuario']:<20} {log['accion']:<25} {detalles}")
    print(Fore.CYAN + "-" * 90 + Style.RESET_ALL)