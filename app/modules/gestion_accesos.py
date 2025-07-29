# app/modulos/gestion_accesos.py
from colorama import Fore, Style
from datetime import datetime
from .. import ui
from ..database import DatabaseManager
from ..auth import (
    generar_contrasena_temporal,
    hash_contrasena,
    validar_email,
    validar_nombre_completo
)
from ..config import ROLES

def registrar_nuevo_usuario(db: DatabaseManager, admin_user: dict):
    """Gestiona el flujo interactivo para registrar un nuevo usuario."""
    campos = ["Nombre completo", "Correo electrónico", "Confirmar correo", "Rol"]
    datos = {campo: "" for campo in campos}
    indice_actual = 0

    # Diccionario de prompts personalizados
    prompts = {
        "Nombre completo": "Escriba el nombre completo:",
        "Correo electrónico": "Ingrese el correo electrónico:",
        "Confirmar correo": "Confirme el correo electrónico:",
        "Rol": "Seleccione un rol para este usuario:"
    }

    try:
        while indice_actual < len(campos):
            campo_actual = campos[indice_actual]
            ui.mostrar_formulario_interactivo("Registrar Nuevo Usuario", campos, datos, indice_actual, admin_user)
            
            # Lógica para mostrar la lista de roles
            if campo_actual == "Rol":
                roles_disponibles = [r for r in ROLES if r != "Administrador"]
                print(Fore.CYAN + "Roles disponibles:")
                for i, rol in enumerate(roles_disponibles, 1):
                    print(f"  {i}. {rol}")
                print() # Espacio adicional antes del prompt

            # Seleccionar el prompt correspondiente
            prompt_actual = prompts.get(campo_actual, f"{campo_actual}: ")
            valor = ui.solicitar_input(Fore.YELLOW + prompt_actual + " ").strip()

            if not valor:
                print(Fore.RED + "Este campo no puede estar vacío."); ui.pausar_pantalla(); continue

            if campo_actual == "Nombre completo":
                if not validar_nombre_completo(valor):
                    print(Fore.RED + "El nombre debe tener al menos dos palabras y no contener símbolos."); ui.pausar_pantalla(); continue
                datos[campo_actual] = ' '.join(word.capitalize() for word in valor.split())
            
            elif campo_actual == "Correo electrónico":
                if not validar_email(valor.lower()):
                    print(Fore.RED + "El formato del correo no es válido."); ui.pausar_pantalla(); continue
                if db.check_if_email_exists(valor.lower()):
                    print(Fore.RED + "Este correo ya está registrado."); ui.pausar_pantalla(); continue
                datos[campo_actual] = valor.lower()

            elif campo_actual == "Confirmar correo":
                if valor.lower() != datos["Correo electrónico"]:
                    print(Fore.RED + "Los correos no coinciden."); ui.pausar_pantalla(); continue
                datos[campo_actual] = valor.lower()

            elif campo_actual == "Rol":
                try:
                    rol_idx = int(valor) - 1
                    if 0 <= rol_idx < len(roles_disponibles):
                        datos[campo_actual] = roles_disponibles[rol_idx]
                    else:
                        print(Fore.RED + "Selección de rol no válida."); ui.pausar_pantalla(); continue
                except ValueError:
                    print(Fore.RED + "Debe ingresar un número."); ui.pausar_pantalla(); continue

            indice_actual += 1
        
        username = datos["Correo electrónico"].split('@')[0]
        contrasena_temporal = generar_contrasena_temporal()

        ui.mostrar_encabezado("Confirmar Registro", usuario_logueado=admin_user)
        print(f"  {'Nombre Completo:'.ljust(25)} {datos['Nombre completo']}")
        print(f"  {'Correo Electrónico:'.ljust(25)} {datos['Correo electrónico']}")
        print(f"  {'Rol Asignado:'.ljust(25)} {datos['Rol']}")
        print(f"  {'Usuario de Acceso:'.ljust(25)} {Fore.YELLOW}{username}{Style.RESET_ALL}")
        print(f"  {'Contraseña Temporal:'.ljust(25)} {Fore.GREEN}{contrasena_temporal}{Style.RESET_ALL}")
        
        print(Fore.WHITE + "─" * 80)
        
        print(Fore.YELLOW + "\n✅ ¿Desea registrar este usuario?")
        prompt = f"Para confirmar, escriba el correo del nuevo usuario ({datos['Correo electrónico']}): "
        confirmacion = ui.solicitar_input(Fore.CYAN + prompt).lower()
        
        if confirmacion == datos['Correo electrónico']:
            user_data = {
                "nombre_completo": datos['Nombre completo'],
                "email": datos['Correo electrónico'],
                "username": username,
                "password_hash": hash_contrasena(contrasena_temporal),
                "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if db.add_new_user(user_data, datos['Rol']):
                db.registrar_movimiento_sistema(
                    accion="Creación de Usuario",
                    detalles=f"Se creó el usuario '{username}' con el rol '{datos['Rol']}'.",
                    usuario=admin_user['username']
                )
                print(Fore.GREEN + "\n✅ Usuario registrado exitosamente.")
                print(Fore.YELLOW + "   Por favor, proporcione la contraseña temporal al usuario.")
                print(Fore.YELLOW + "   El usuario deberá cambiarla en su primer inicio de sesión.")
            else:
                print(Fore.RED + "\n❌ Error: El usuario o email ya existe.")
        else:
            print(Fore.RED + "\nLa confirmación no coincide. Operación cancelada.")

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n\n🚫 Operación cancelada.")
    finally:
        ui.pausar_pantalla()


def gestionar_usuarios_existentes(db: DatabaseManager, admin_user: dict):
    """Menú principal para la gestión de usuarios."""
    while True:
        ui.mostrar_encabezado("Gestión de Usuarios", usuario_logueado=admin_user)
        
        usuarios_raw = [u for u in db.get_all_users_with_roles() if u['username'] != admin_user['username']]
        usuarios_enriquecidos = []
        for user in usuarios_raw:
            user_dict = dict(user)
            user_dict['ultima_sesion'] = db.get_last_login_for_user(user_dict['id']) or "No ha iniciado sesión"
            usuarios_enriquecidos.append(user_dict)
            
        ui.mostrar_tabla_usuarios(usuarios_enriquecidos)
        
        username_input = ui.solicitar_input(Fore.YELLOW + "\nIngrese el Usuario a gestionar (o 'q' para volver): ")
        if username_input.lower() == 'q': break

        target_user = db.get_user_by_username(username_input.lower())
        
        if not target_user or target_user['username'] == admin_user['username']:
            print(Fore.RED + "Usuario no encontrado o no válido."); ui.pausar_pantalla(); continue
        
        _menu_usuario_especifico(db, admin_user, target_user)

def _menu_usuario_especifico(db: DatabaseManager, admin_user: dict, target_user: dict):
    """Submenú de acciones para un usuario seleccionado."""
    while True:
        current_user_data = db.get_user_by_username(target_user['username'])
        if not current_user_data:
            print(Fore.RED + "El usuario ya no existe."); ui.pausar_pantalla(); break
        
        ui.mostrar_encabezado(f"Perfil de Usuario: {current_user_data['username']}", usuario_logueado=admin_user)

        estado_display = (Fore.GREEN + "Activo") if current_user_data['is_active'] else (Fore.RED + "Inactivo")
        
        info_panel = {
            "Fecha de Registro": current_user_data['fecha_registro'],
            "ID de Usuario": current_user_data['id'],
            "Nombre Completo": current_user_data['nombre_completo'],
            "Email": current_user_data['email'],
            "Rol": current_user_data['nombre_rol'],
            "Estado": f"{estado_display}{Style.RESET_ALL}",
        }
        ui.mostrar_panel_info("Información del Usuario", info_panel)

        opcion_activar = "Desactivar usuario" if current_user_data['is_active'] else "Activar usuario"
        opciones = ["Modificar nombre completo", "Cambiar rol", opcion_activar, "Resetear contraseña", "Volver"]
        
        ui.mostrar_menu(opciones)
        opcion = ui.solicitar_input(Fore.YELLOW + "Seleccione una acción: ")

        if opcion == '1': _modificar_nombre_usuario(db, admin_user, current_user_data)
        elif opcion == '2': _cambiar_rol_usuario(db, admin_user, current_user_data)
        elif opcion == '3': _cambiar_estado_usuario(db, admin_user, current_user_data)
        elif opcion == '4': _resetear_contrasena_usuario(db, admin_user, current_user_data)
        elif opcion == '5': break
        else: print(Fore.RED + "Opción no válida."); ui.pausar_pantalla()

def _modificar_nombre_usuario(db: DatabaseManager, admin_user: dict, target_user: dict):
    """Flujo para modificar el nombre de un usuario."""
    ui.mostrar_encabezado(f"Modificar Nombre de {target_user['username']}", usuario_logueado=admin_user)
    print(f"Nombre actual: {Fore.CYAN}{target_user['nombre_completo']}{Style.RESET_ALL}")
    nuevo_nombre = ui.solicitar_input(Fore.YELLOW + "Ingrese el nuevo nombre completo: ").strip()
    
    if nuevo_nombre:
        if not validar_nombre_completo(nuevo_nombre):
            print(Fore.RED + "\nEl nombre debe tener al menos dos palabras y no contener símbolos.")
        else:
            nombre_capitalizado = ' '.join(word.capitalize() for word in nuevo_nombre.split())
            db.update_user_fullname(target_user['id'], nombre_capitalizado)
            db.registrar_movimiento_sistema(
                accion="Modificación de Usuario",
                detalles=f"Se cambió el nombre de '{target_user['username']}' a '{nombre_capitalizado}'.",
                usuario=admin_user['username']
            )
            print(Fore.GREEN + "\n✅ Nombre actualizado exitosamente.")
    else:
        print(Fore.YELLOW + "\nOperación cancelada. El nombre no puede estar vacío.")
    ui.pausar_pantalla()

def _cambiar_estado_usuario(db: DatabaseManager, admin_user: dict, target_user: dict):
    """Flujo para activar o desactivar un usuario."""
    nuevo_estado = not target_user['is_active']
    accion = "desactivar" if nuevo_estado is False else "activar"
    
    ui.mostrar_encabezado(f"Confirmar {accion.capitalize()} Usuario", color=Fore.RED, usuario_logueado=admin_user)
    print(Fore.YELLOW + f"Está a punto de {accion} al usuario '{target_user['username']}'.")
    
    confirmacion = ui.solicitar_input(f"Para confirmar, escriba el nombre de usuario ({target_user['username']}): ")

    if confirmacion == target_user['username']:
        db.update_user_status(target_user['id'], nuevo_estado)
        db.registrar_movimiento_sistema(
            accion="Cambio de Estado",
            detalles=f"El usuario '{target_user['username']}' fue {'desactivado' if not nuevo_estado else 'activado'}.",
            usuario=admin_user['username']
        )
        print(Fore.GREEN + f"\n✅ Usuario {'desactivado' if not nuevo_estado else 'activado'} correctamente.")
    else:
        print(Fore.RED + "\nLa confirmación no coincide. Operación cancelada.")
    ui.pausar_pantalla()

def _resetear_contrasena_usuario(db: DatabaseManager, admin_user: dict, target_user: dict):
    """Flujo para resetear la contraseña de un usuario."""
    ui.mostrar_encabezado(f"Resetear Contraseña de {target_user['username']}", color=Fore.RED, usuario_logueado=admin_user)
    print(Fore.YELLOW + "Esta acción generará una nueva contraseña temporal para el usuario.")
    
    print(Fore.WHITE + "─" * 80)
    confirmacion = ui.solicitar_input(f"Para confirmar, escriba el nombre de usuario ({target_user['username']}): ")

    if confirmacion == target_user['username']:
        temp_pass = generar_contrasena_temporal()
        new_hash = hash_contrasena(temp_pass)
        db.update_user_password(target_user['id'], new_hash, require_change=True)
        db.registrar_movimiento_sistema(
            accion="Reseteo de Contraseña",
            detalles=f"Se reseteó la contraseña del usuario '{target_user['username']}'.",
            usuario=admin_user['username']
        )
        print(Fore.GREEN + f"\n✅ Contraseña reseteada. La nueva contraseña temporal es: {Style.BRIGHT}{temp_pass}{Style.RESET_ALL}")
        print(Fore.YELLOW + "El usuario deberá cambiarla en su próximo inicio de sesión.")
    else:
        print(Fore.RED + "\nLa confirmación no coincide. Operación cancelada.")
    ui.pausar_pantalla()

def _cambiar_rol_usuario(db: DatabaseManager, admin_user: dict, target_user: dict):
    """Flujo para cambiar el rol de un usuario."""
    ui.mostrar_encabezado(f"Cambiar Rol de {target_user['username']}", usuario_logueado=admin_user)
    print(f"Rol actual: {Fore.CYAN}{target_user['nombre_rol']}{Style.RESET_ALL}")
    
    roles_disponibles = [r for r in ROLES if r not in ["Administrador", target_user['nombre_rol']]]
    if not roles_disponibles:
        print(Fore.YELLOW + "\nNo hay otros roles disponibles para asignar a este usuario.")
        ui.pausar_pantalla()
        return

    print(Fore.CYAN + "\nRoles disponibles para asignar:")
    for i, rol in enumerate(roles_disponibles, 1):
        print(f"  {i}. {rol}")
    
    try:
        opcion = ui.solicitar_input(Fore.YELLOW + "\nSeleccione el nuevo rol: ")
        rol_idx = int(opcion) - 1
        if 0 <= rol_idx < len(roles_disponibles):
            nuevo_rol_nombre = roles_disponibles[rol_idx]
            
            print(Fore.WHITE + "─" * 80)
            confirmacion = ui.solicitar_input(Fore.RED + f"Para confirmar el cambio a '{nuevo_rol_nombre}', escriba el nombre del rol: ").strip()

            if confirmacion.capitalize() == nuevo_rol_nombre:
                nuevo_rol_id = db.get_role_id_by_name(nuevo_rol_nombre)
                if nuevo_rol_id:
                    db.update_user_role(target_user['id'], nuevo_rol_id)
                    db.registrar_movimiento_sistema(
                        accion="Cambio de Rol",
                        detalles=f"Se cambió el rol de '{target_user['username']}' de '{target_user['nombre_rol']}' a '{nuevo_rol_nombre}'.",
                        usuario=admin_user['username']
                    )
                    print(Fore.GREEN + f"\n✅ Rol del usuario actualizado a '{nuevo_rol_nombre}'.")
                else:
                    print(Fore.RED + "\nError interno: No se pudo encontrar el ID del rol.")
            else:
                print(Fore.RED + "\nLa confirmación no coincide. Operación cancelada.")
        else:
            print(Fore.RED + "Selección no válida.")
    except ValueError:
        print(Fore.RED + "Debe ingresar un número.")
    finally:
        ui.pausar_pantalla()