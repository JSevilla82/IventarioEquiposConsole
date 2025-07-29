# app/auth.py
import bcrypt, re, time
from datetime import datetime
from colorama import Fore, Style
from . import ui
from .database import DatabaseManager

def hash_contrasena(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_contrasena(contrasena: str, hash_almacenado: str) -> bool:
    return bcrypt.checkpw(contrasena.encode('utf-8'), hash_almacenado.encode('utf-8'))

def validar_contrasena(contrasena: str) -> bool:
    if len(contrasena) < 8: return False
    if not re.search(r'[A-Za-z]', contrasena): return False
    if not re.search(r'[0-9]', contrasena): return False
    return True

def generar_contrasena_temporal() -> str:
    fecha = datetime.now().strftime("%d%m")
    return f"inventario{fecha}+"

def validar_email(email: str) -> bool:
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_nombre_completo(nombre: str) -> bool:
    patron = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
    if not re.match(patron, nombre): return False
    return len(nombre.strip().split()) >= 2

def login(db: DatabaseManager, admin_creado: bool, admin_pass: str):
    error_message, username, intentos = "", "", 0
    while intentos < 3:
        ui.mostrar_encabezado("Inicio de Sesión")
        print("Bienvenido al Control de Inventario de Equipos (CIE).")
        if admin_creado:
            print(Fore.GREEN + "\n✨ ¡Primera ejecución! Se ha creado el usuario administrador:")
            print(f"   - Usuario: {Style.BRIGHT}admin{Style.RESET_ALL}\n   - Contraseña: {Style.BRIGHT}{admin_pass}{Style.RESET_ALL}")
            print(Fore.YELLOW + "   Deberá cambiar la contraseña después de iniciar sesión.")
        print(Fore.WHITE + "─" * 80)
        if error_message: print(Fore.RED + f"\n{error_message}\n")
        
        username = ui.solicitar_input(Fore.YELLOW + "👤 Ingrese su usuario: ", default=username)
        if not username: error_message = ""; continue
        contrasena = ui.solicitar_contrasena_con_asteriscos(Fore.YELLOW + "🔑 Ingrese su contraseña: ")
        if not contrasena: error_message = ""; continue
        
        print(Fore.CYAN + "\nValidando credenciales...", end="", flush=True); time.sleep(1)
        print("\r" + " " * 30 + "\r", end="", flush=True)
        
        user_data = db.get_user_by_username(username)
        if user_data and verificar_contrasena(contrasena, user_data['password_hash']):
            if not user_data['is_active']:
                error_message = "❌ Su cuenta está bloqueada."; intentos += 1; continue
            db.log_login_attempt(user_data['id'])
            if user_data['cambio_clave_requerido']:
                ui.mostrar_encabezado("Cambio de Contraseña Requerido", usuario_logueado=user_data)
                print(Fore.YELLOW + "⚠️ Por seguridad, debe cambiar su contraseña."); ui.pausar_pantalla()
                if not cambiar_contrasena_usuario(db, user_data, forzar_cambio=True):
                    error_message = "No se pudo cambiar la contraseña. Intente de nuevo."; continue
            return db.get_user_by_username(username)
        else:
            error_message = "❌ Credenciales incorrectas."; intentos += 1
    print(Fore.RED + "\n❌ Demasiados intentos fallidos."); return None

def cambiar_contrasena_usuario(db: DatabaseManager, usuario: dict, forzar_cambio: bool = False) -> bool:
    ui.mostrar_encabezado(f"Cambiar Contraseña para {usuario['username']}", usuario_logueado=usuario)
    print(Fore.CYAN + "💡 La nueva contraseña debe tener al menos 8 caracteres, con letras y números.")
    try:
        while True:
            if not forzar_cambio:
                actual = ui.solicitar_contrasena_con_asteriscos(Fore.YELLOW + "Contraseña actual: ")
                if not verificar_contrasena(actual, usuario['password_hash']):
                    print(Fore.RED + "Contraseña actual incorrecta."); continue
            nueva = ui.solicitar_contrasena_con_asteriscos(Fore.YELLOW + "Nueva contraseña: ")
            if not validar_contrasena(nueva):
                print(Fore.RED + "La contraseña nueva no es segura."); continue
            confirmacion = ui.solicitar_contrasena_con_asteriscos(Fore.YELLOW + "Confirme la nueva contraseña: ")
            if nueva != confirmacion:
                print(Fore.RED + "Las contraseñas no coinciden."); continue
            break
        nuevo_hash = hash_contrasena(nueva)
        db.update_user_password(usuario['id'], nuevo_hash, require_change=False)
        print(Fore.GREEN + "\n✅ Contraseña actualizada exitosamente."); ui.pausar_pantalla(); return True
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n\n🚫 Operación cancelada."); ui.pausar_pantalla(); return False