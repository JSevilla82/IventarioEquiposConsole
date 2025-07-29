# app/modulos/gestion_configuracion.py
from colorama import Fore
from .. import ui
from ..database import DatabaseManager

def menu_configuracion_sistema(db: DatabaseManager, admin_user: dict):
    """Menú principal para la configuración de parámetros del sistema."""
    while True:
        ui.mostrar_encabezado("Configuración del Sistema", usuario_logueado=admin_user)
        opciones = [
            "Gestionar Tipos de Activo", "Gestionar Marcas",
            "Gestionar Dominios de Correo", "Gestionar Proveedores",
            "Volver al Menú Principal"
        ]
        ui.mostrar_menu(opciones)
        opcion = ui.solicitar_input(Fore.YELLOW + "Seleccione una opción: ")

        if opcion == '1': gestionar_parametros(db, admin_user, 'tipo_activo', 'Tipo de Activo')
        elif opcion == '2': gestionar_parametros(db, admin_user, 'marca_equipo', 'Marca')
        elif opcion == '3': gestionar_parametros(db, admin_user, 'dominio_correo', 'Dominio de Correo')
        elif opcion == '4': gestionar_proveedores(db, admin_user)
        elif opcion == '5': break
        else: print(Fore.RED + "Opción no válida."); ui.pausar_pantalla()

def gestionar_parametros(db: DatabaseManager, admin_user: dict, tipo_parametro: str, nombre_amigable: str):
    """Flujo genérico para gestionar parámetros (Tipos, Marcas, Dominios)."""
    while True:
        ui.mostrar_encabezado(f"Gestionar {nombre_amigable}s", usuario_logueado=admin_user)
        items = db.get_parametros_por_tipo(tipo_parametro)
        ui.mostrar_tabla_parametros(f"Listado de {nombre_amigable}s", items)
        
        opciones = [f"Añadir nuevo {nombre_amigable}", "Modificar", "Activar/Inactivar", "Eliminar", "Volver"]
        ui.mostrar_menu(opciones)
        id_input_prompt = f"\n{Fore.YELLOW}Seleccione una acción o ingrese un ID para gestionar directamente: {Fore.RESET}"
        opcion = ui.solicitar_input(id_input_prompt).strip()

        if opcion == '1': _añadir_parametro(db, admin_user, tipo_parametro, nombre_amigable)
        elif opcion == '2': _modificar_parametro(db, admin_user, nombre_amigable, items)
        elif opcion == '3': _cambiar_estado_parametro(db, admin_user, nombre_amigable, items)
        elif opcion == '4': _eliminar_parametro(db, admin_user, nombre_amigable, items)
        elif opcion == '5': break
        else: print(Fore.RED + "Opción no válida."); ui.pausar_pantalla()

def _añadir_parametro(db: DatabaseManager, admin_user: dict, tipo: str, nombre: str):
    ui.mostrar_encabezado(f"Añadir Nuevo {nombre}", usuario_logueado=admin_user)
    
    while True:
        nuevo_valor = ui.solicitar_input(Fore.YELLOW + f"Paso 1: Ingrese el nombre del nuevo {nombre}: ").strip()
        if not nuevo_valor:
            print(Fore.RED + "El nombre no puede estar vacío."); continue

        confirmacion = ui.solicitar_input(Fore.YELLOW + f"Paso 2: Confirme el nombre del nuevo {nombre}: ").strip()
        if nuevo_valor.lower() == confirmacion.lower():
            break
        else:
            print(Fore.RED + "Los nombres no coinciden. Intente de nuevo."); ui.pausar_pantalla()

    valor_final = nuevo_valor.title() if tipo != 'dominio_correo' else nuevo_valor.lower()

    if db.add_parametro(tipo, valor_final):
        db.registrar_movimiento_sistema("Configuración", f"Añadido {nombre}: '{valor_final}'", admin_user['username'])
        print(Fore.GREEN + f"\n✅ {nombre} '{valor_final}' añadido con éxito.")
    else:
        print(Fore.RED + f"\n❌ Error: El {nombre} '{valor_final}' ya existe.")
    ui.pausar_pantalla()

def _modificar_parametro(db: DatabaseManager, admin_user: dict, nombre: str, items: list):
    id_input = ui.solicitar_input(Fore.YELLOW + f"\nIngrese el ID del {nombre} a modificar: ")
    try:
        item = next((i for i in items if i['id'] == int(id_input)), None)
        if item:
            if db.is_parametro_in_use(item['id']):
                print(Fore.RED + f"\n❌ No se puede modificar '{item['valor']}', está en uso.")
            else:
                print(f"Valor actual: {Fore.CYAN}{item['valor']}{Fore.RESET}")
                nuevo_valor = ui.solicitar_input(Fore.YELLOW + "Ingrese el nuevo valor: ").strip()
                if nuevo_valor and nuevo_valor.lower() != item['valor'].lower():
                    valor_final = nuevo_valor.title() if item['tipo'] != 'dominio_correo' else nuevo_valor.lower()
                    if db.update_parametro(item['id'], valor_final):
                        db.registrar_movimiento_sistema("Configuración", f"Modificado {nombre}: de '{item['valor']}' a '{valor_final}'", admin_user['username'])
                        print(Fore.GREEN + "\n✅ Elemento modificado con éxito.")
                    else:
                        print(Fore.RED + f"\n❌ Error: El valor '{valor_final}' ya existe.")
                else:
                    print(Fore.YELLOW + "\nOperación cancelada o sin cambios.")
        else:
            print(Fore.RED + "ID no encontrado.")
    except ValueError:
        print(Fore.RED + "Entrada no válida.")
    ui.pausar_pantalla()

def _cambiar_estado_parametro(db: DatabaseManager, admin_user: dict, nombre: str, items: list):
    id_input = ui.solicitar_input(Fore.YELLOW + f"\nIngrese el ID del {nombre} a activar/inactivar: ")
    try:
        item = next((i for i in items if i['id'] == int(id_input)), None)
        if item:
            nuevo_estado = not item['is_active']
            db.update_parametro_status(item['id'], nuevo_estado)
            accion = "activado" if nuevo_estado else "inactivado"
            db.registrar_movimiento_sistema("Configuración", f"{nombre} '{item['valor']}' {accion}", admin_user['username'])
            print(Fore.GREEN + f"\n✅ {nombre} '{item['valor']}' {accion} con éxito.")
        else:
            print(Fore.RED + "ID no encontrado.")
    except ValueError:
        print(Fore.RED + "Entrada no válida. Debe ser un número.")
    ui.pausar_pantalla()

def _eliminar_parametro(db: DatabaseManager, admin_user: dict, nombre: str, items: list):
    id_input = ui.solicitar_input(Fore.YELLOW + f"\nIngrese el ID del {nombre} a ELIMINAR: ")
    try:
        item = next((i for i in items if i['id'] == int(id_input)), None)
        if item:
            if db.is_parametro_in_use(item['id']):
                print(Fore.RED + f"\n❌ No se puede eliminar '{item['valor']}', está en uso.")
            else:
                confirmacion = ui.solicitar_input(Fore.RED + f"¿Seguro que desea eliminar '{item['valor']}'? Escriba el valor para confirmar: ")
                if confirmacion == item['valor']:
                    db.delete_parametro(item['id'])
                    db.registrar_movimiento_sistema("Configuración", f"Eliminado {nombre}: '{item['valor']}'", admin_user['username'])
                    print(Fore.GREEN + "\n✅ Elemento eliminado con éxito.")
                else:
                    print(Fore.YELLOW + "\nLa confirmación no coincide. Operación cancelada.")
        else:
            print(Fore.RED + "ID no encontrado.")
    except ValueError:
        print(Fore.RED + "Entrada no válida. Debe ser un número.")
    ui.pausar_pantalla()

def gestionar_proveedores(db: DatabaseManager, admin_user: dict):
    """Flujo específico para gestionar proveedores."""
    while True:
        ui.mostrar_encabezado("Gestionar Proveedores", usuario_logueado=admin_user)
        proveedores = db.get_all_proveedores()
        ui.mostrar_tabla_parametros("Listado de Proveedores", proveedores, es_proveedor=True)

        opciones = ["Añadir nuevo Proveedor", "Modificar", "Activar/Inactivar", "Eliminar", "Volver"]
        ui.mostrar_menu(opciones)
        opcion = ui.solicitar_input(Fore.YELLOW + "\nSeleccione una acción: ")

        if opcion == '1': _añadir_proveedor(db, admin_user)
        elif opcion == '2': _modificar_proveedor(db, admin_user, proveedores)
        elif opcion == '3': _cambiar_estado_proveedor(db, admin_user, proveedores)
        elif opcion == '4': _eliminar_proveedor(db, admin_user, proveedores)
        elif opcion == '5': break
        else: print(Fore.RED + "Opción no válida."); ui.pausar_pantalla()

def _añadir_proveedor(db: DatabaseManager, admin_user: dict):
    campos = ["Nombre del Proveedor", "Confirmar Nombre", "Iniciales de Placa (Opcional)"]
    datos = {c: "" for c in campos}
    idx = 0
    while idx < len(campos):
        campo_actual = campos[idx]
        ui.mostrar_formulario_interactivo("Añadir Nuevo Proveedor", campos, datos, idx, admin_user)
        
        if campo_actual == "Iniciales de Placa (Opcional)":
            print(Fore.CYAN + "💡 Si este proveedor usa un prefijo en sus placas (ej. 'DELL-'), ingréselo aquí.")
        
        valor = ui.solicitar_input(Fore.YELLOW + f"{campo_actual}: ").strip()

        if not valor and campo_actual != "Iniciales de Placa (Opcional)":
            print(Fore.RED + "Este campo no puede estar vacío."); ui.pausar_pantalla(); continue

        if campo_actual == "Nombre del Proveedor":
            datos[campo_actual] = valor.title()
        elif campo_actual == "Confirmar Nombre":
            if valor.title() != datos["Nombre del Proveedor"]:
                print(Fore.RED + "Los nombres no coinciden."); ui.pausar_pantalla(); continue
            datos[campo_actual] = valor.title()
        elif campo_actual == "Iniciales de Placa (Opcional)":
            datos[campo_actual] = valor.upper()
        
        idx += 1

    if db.add_proveedor(datos["Nombre del Proveedor"], datos["Iniciales de Placa (Opcional)"]):
        db.registrar_movimiento_sistema("Configuración", f"Añadido Proveedor: '{datos['Nombre del Proveedor']}'", admin_user['username'])
        print(Fore.GREEN + "\n✅ Proveedor añadido con éxito.")
    else:
        print(Fore.RED + f"\n❌ Error: El proveedor '{datos['Nombre del Proveedor']}' ya existe.")
    ui.pausar_pantalla()

def _modificar_proveedor(db: DatabaseManager, admin_user: dict, proveedores: list):
    id_input = ui.solicitar_input(Fore.YELLOW + "\nIngrese el ID del proveedor a modificar: ")
    try:
        item = next((p for p in proveedores if p['id'] == int(id_input)), None)
        if item:
            if db.is_proveedor_in_use(item['id']):
                print(Fore.RED + f"\n❌ No se puede modificar '{item['nombre']}', está en uso.")
                ui.pausar_pantalla()
                return

            campos = ["Nuevo Nombre", "Nuevas Iniciales de Placa (Opcional)"]
            datos_actuales = { "Nuevo Nombre": item['nombre'], "Nuevas Iniciales de Placa (Opcional)": item['placa_inicial'] or "" }
            datos = datos_actuales.copy()
            idx = 0
            
            while idx < len(campos):
                ui.mostrar_formulario_interactivo(f"Modificar Proveedor: {item['nombre']}", campos, datos, idx, admin_user)
                campo_actual = campos[idx]
                valor = ui.solicitar_input(Fore.YELLOW + f"{campo_actual} (Actual: {datos_actuales[campo_actual]}): ").strip()
                
                if valor: datos[campo_actual] = valor
                idx += 1
            
            nuevo_nombre = datos["Nuevo Nombre"].title()
            nuevas_iniciales = datos["Nuevas Iniciales de Placa (Opcional)"].upper()

            if db.update_proveedor(item['id'], nuevo_nombre, nuevas_iniciales):
                db.registrar_movimiento_sistema("Configuración", f"Modificado Proveedor ID {item['id']} a '{nuevo_nombre}'", admin_user['username'])
                print(Fore.GREEN + "\n✅ Proveedor modificado con éxito.")
            else:
                print(Fore.RED + f"\n❌ Error: El nombre '{nuevo_nombre}' ya existe.")
        else:
            print(Fore.RED + "ID no encontrado.")
    except ValueError:
        print(Fore.RED + "Entrada no válida.")
    ui.pausar_pantalla()

def _cambiar_estado_proveedor(db: DatabaseManager, admin_user: dict, proveedores: list):
    id_input = ui.solicitar_input(Fore.YELLOW + "\nIngrese el ID del proveedor a activar/inactivar: ")
    try:
        item = next((p for p in proveedores if p['id'] == int(id_input)), None)
        if item:
            nuevo_estado = not item['is_active']
            db.update_proveedor_status(item['id'], nuevo_estado)
            accion = "activado" if nuevo_estado else "inactivado"
            db.registrar_movimiento_sistema("Configuración", f"Proveedor '{item['nombre']}' {accion}", admin_user['username'])
            print(Fore.GREEN + f"\n✅ Proveedor '{item['nombre']}' {accion} con éxito.")
        else:
            print(Fore.RED + "ID no encontrado.")
    except ValueError:
        print(Fore.RED + "Entrada no válida.")
    ui.pausar_pantalla()

def _eliminar_proveedor(db: DatabaseManager, admin_user: dict, proveedores: list):
    id_input = ui.solicitar_input(Fore.YELLOW + "\nIngrese el ID del proveedor a ELIMINAR: ")
    try:
        item = next((p for p in proveedores if p['id'] == int(id_input)), None)
        if item:
            if db.is_proveedor_in_use(item['id']):
                print(Fore.RED + f"\n❌ No se puede eliminar '{item['nombre']}', está en uso.")
            else:
                confirmacion = ui.solicitar_input(Fore.RED + f"¿Seguro que desea eliminar '{item['nombre']}'? Escriba el nombre para confirmar: ")
                if confirmacion == item['nombre']:
                    db.delete_proveedor(item['id'])
                    db.registrar_movimiento_sistema("Configuración", f"Eliminado Proveedor: '{item['nombre']}'", admin_user['username'])
                    print(Fore.GREEN + "\n✅ Proveedor eliminado con éxito.")
                else:
                    print(Fore.YELLOW + "\nLa confirmación no coincide. Operación cancelada.")
        else:
            print(Fore.RED + "ID no encontrado.")
    except ValueError:
        print(Fore.RED + "Entrada no válida.")
    ui.pausar_pantalla()