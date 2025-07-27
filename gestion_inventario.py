# gestion_inventario.py
import os
import re
import textwrap
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from colorama import Fore, Style

from database import db_manager, Equipo, registrar_movimiento_inventario, registrar_movimiento_sistema
from ui import mostrar_encabezado, mostrar_menu, pausar_pantalla, confirmar_con_placa
from gestion_acceso import requiere_permiso
from gestion_reportes import generar_excel_historico_equipo

# --- INICIO DE MODIFICACIÓN PARA REGISTRO DE EQUIPO ---

def _mostrar_formulario_interactivo(campos: List[str], datos: Dict[str, str], indice_actual: int):
    """
    Muestra una representación visual del formulario de registro,
    indicando el campo actual con una flecha.
    """
    mostrar_encabezado("Registro de Nuevo Equipo", color=Fore.BLUE)
    print(Fore.CYAN + "💡 Complete los siguientes campos. Puede presionar Ctrl+C para cancelar." + Style.RESET_ALL)
    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

    for i, campo in enumerate(campos):
        indicador = Fore.YELLOW + " -> " if i == indice_actual else "    "
        valor_mostrado = datos.get(campo, "")
        if valor_mostrado:
            valor_mostrado = f"{Fore.GREEN}{valor_mostrado}{Style.RESET_ALL}"
        print(f"{indicador}{campo.ljust(20)}: {valor_mostrado}")

    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)


@requiere_permiso("registrar_equipo")
def registrar_equipo(usuario: str):
    """Función mejorada para registrar un nuevo equipo con una interfaz interactiva."""
    tipos_existentes = db_manager.get_parametros_por_tipo('tipo_equipo', solo_activos=True)
    marcas_existentes = db_manager.get_parametros_por_tipo('marca_equipo', solo_activos=True)

    if not tipos_existentes or not marcas_existentes:
        mostrar_encabezado("Registro de Nuevo Equipo", color=Fore.RED)
        print(Fore.RED + "❌ No se puede registrar un nuevo equipo.")
        if not tipos_existentes: print(Fore.YELLOW + "   - No hay 'Tipos de Equipo' activos configurados.")
        if not marcas_existentes: print(Fore.YELLOW + "   - No hay 'Marcas' activas configuradas.")
        print(Fore.CYAN + "Por favor, pida a un Administrador que configure estos parámetros.")
        pausar_pantalla()
        return

    campos_requeridos = ["Placa", "Tipo de Equipo", "Marca", "Modelo", "Número de serie", "Observaciones"]
    datos_equipo = {campo: "" for campo in campos_requeridos}
    indice_actual = 0
    
    try:
        while indice_actual < len(campos_requeridos):
            campo_actual = campos_requeridos[indice_actual]
            _mostrar_formulario_interactivo(campos_requeridos, datos_equipo, indice_actual)

            if campo_actual == "Placa":
                placa = input(Fore.YELLOW + "Ingrese la Placa del equipo: " + Style.RESET_ALL).strip().upper()
                if not validar_placa_formato(placa):
                    print(Fore.RED + "⚠️ Formato de placa inválido (mín. 4 caracteres alfanuméricos).")
                    pausar_pantalla()
                    continue
                equipo_existente = db_manager.get_equipo_by_placa(placa)
                if equipo_existente:
                    if equipo_existente['estado'] == "Devuelto a Proveedor":
                        print(Fore.YELLOW + f"\n⚠️ Este equipo (Placa: {placa}) ya existe y fue devuelto al proveedor.")
                        confirmacion = input(Fore.YELLOW + "¿Desea reactivarlo? (S/N): " + Style.RESET_ALL).strip().upper()
                        if confirmacion == 'S':
                            equipo_reactivado = Equipo(**equipo_existente)
                            equipo_reactivado.estado = "Disponible"
                            equipo_reactivado.asignado_a = None
                            db_manager.update_equipo(equipo_reactivado)
                            registrar_movimiento_inventario(placa, "Reactivación", "Equipo reactivado en el inventario.", usuario)
                            print(Fore.GREEN + f"\n✅ ¡Equipo {placa} reactivado!")
                            pausar_pantalla()
                            return
                        else:
                            print(Fore.YELLOW + "Reactivación cancelada. Intente con otra placa.")
                            pausar_pantalla()
                            continue
                    else:
                        print(Fore.RED + "⚠️ Esta placa ya está registrada y activa en el sistema.")
                        pausar_pantalla()
                        continue
                datos_equipo[campo_actual] = placa
            elif campo_actual == "Tipo de Equipo":
                tipo = seleccionar_parametro('tipo_equipo', 'Tipo de Equipo')
                if not tipo: continue
                datos_equipo[campo_actual] = tipo
            elif campo_actual == "Marca":
                marca = seleccionar_parametro('marca_equipo', 'Marca')
                if not marca: continue
                datos_equipo[campo_actual] = marca
            elif campo_actual == "Modelo":
                modelo = input(Fore.YELLOW + "Ingrese el Modelo: " + Style.RESET_ALL).strip()
                if not validar_campo_general(modelo):
                    print(Fore.RED + "Modelo inválido. Solo se permiten letras, números y (- _ . ,).")
                    pausar_pantalla()
                    continue
                datos_equipo[campo_actual] = modelo
            elif campo_actual == "Número de serie":
                serial = input(Fore.YELLOW + "Ingrese el Número de serie: " + Style.RESET_ALL).strip()
                if not validar_serial(serial):
                    print(Fore.RED + "Número de serie inválido. No se permiten espacios ni símbolos.")
                    pausar_pantalla()
                    continue
                datos_equipo[campo_actual] = serial
            elif campo_actual == "Observaciones":
                observaciones = input(Fore.YELLOW + "Ingrese Observaciones (opcional): " + Style.RESET_ALL).strip() or "Ninguna"
                datos_equipo[campo_actual] = observaciones
            indice_actual += 1

        mostrar_encabezado("Resumen del Nuevo Equipo", color=Fore.CYAN)
        for campo, valor in datos_equipo.items():
            print(f"  {campo.ljust(20)}: {Fore.GREEN}{valor}{Style.RESET_ALL}")
        print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

        if not confirmar_con_placa(datos_equipo["Placa"]):
             return

        nuevo_equipo = Equipo(
            placa=datos_equipo["Placa"], tipo=datos_equipo["Tipo de Equipo"], marca=datos_equipo["Marca"],
            modelo=datos_equipo["Modelo"], serial=datos_equipo["Número de serie"], observaciones=datos_equipo["Observaciones"]
        )
        db_manager.insert_equipo(nuevo_equipo)
        registrar_movimiento_inventario(
            nuevo_equipo.placa, "Registro", f"Nuevo equipo registrado: {nuevo_equipo.tipo} {nuevo_equipo.marca} {nuevo_equipo.modelo}", usuario
        )
        print(Fore.GREEN + f"\n✅ ¡Equipo con placa {nuevo_equipo.placa} registrado exitosamente!")
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación de registro cancelada.")
    finally:
        pausar_pantalla()

# --- FIN DE MODIFICACIÓN PARA REGISTRO DE EQUIPO ---

# --- INICIO DE MODIFICACIÓN PARA ASIGNACIÓN DE EQUIPO ---

def _mostrar_formulario_asignacion(equipo: Equipo, campos: List[str], datos: Dict[str, str], indice_actual: int):
    """
    Muestra el formulario interactivo para asignar o prestar un equipo,
    incluyendo la información del equipo que se está gestionando.
    """
    mostrar_encabezado(f"Asignar/Prestar Equipo - Placa: {equipo.placa}", color=Fore.BLUE)
    
    # Mostrar información del equipo que se está gestionando
    print(Fore.CYAN + "--- Información del Equipo ---")
    print(f"  {'Placa:'.ljust(15)} {equipo.placa}")
    print(f"  {'Tipo:'.ljust(15)} {equipo.tipo}")
    print(f"  {'Marca:'.ljust(15)} {equipo.marca}")
    print(f"  {'Modelo:'.ljust(15)} {equipo.modelo}")
    print(Style.RESET_ALL)
    
    print(Fore.CYAN + "💡 Complete los siguientes campos. Puede presionar Ctrl+C para cancelar." + Style.RESET_ALL)
    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

    for i, campo in enumerate(campos):
        indicador = Fore.YELLOW + " -> " if i == indice_actual else "    "
        valor_mostrado = datos.get(campo, "")
        if valor_mostrado:
            valor_mostrado = f"{Fore.GREEN}{valor_mostrado}{Style.RESET_ALL}"
        print(f"{indicador}{campo.ljust(25)}: {valor_mostrado}")

    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

@requiere_permiso("gestionar_equipo")
def asignar_o_prestar_equipo(usuario: str, equipo: Equipo):
    """Función mejorada para asignar o prestar un equipo con una interfaz interactiva."""
    if equipo.estado != "Disponible":
        print(Fore.RED + f"❌ El equipo no está 'Disponible' (Estado actual: {equipo.estado}).")
        pausar_pantalla()
        return
    
    dominios_permitidos = db_manager.get_parametros_por_tipo('dominio_correo', solo_activos=True)
    if not dominios_permitidos:
        print(Fore.RED + "❌ No se puede asignar un equipo. No hay 'Dominios de Correo' configurados.")
        pausar_pantalla()
        return

    campos_base = ["Tipo de Operación", "Nombre de la Persona", "Email de la Persona", "Observación"]
    datos_asignacion = {campo: "" for campo in campos_base}
    indice_actual = 0

    try:
        while indice_actual < len(campos_base):
            campos_actuales = list(datos_asignacion.keys())
            campo_actual = campos_actuales[indice_actual]
            # Pasamos el objeto 'equipo' a la función de visualización
            _mostrar_formulario_asignacion(equipo, campos_actuales, datos_asignacion, indice_actual)

            if campo_actual == "Tipo de Operación":
                print(Fore.GREEN + "\nSeleccione el tipo de operación:")
                print("1. Asignar")
                print("2. Prestar")
                tipo_input = input(Fore.YELLOW + "Opción: " + Style.RESET_ALL).strip()
                if tipo_input == "1":
                    datos_asignacion[campo_actual] = "Asignación"
                    if "Fecha de Devolución" in datos_asignacion:
                        del datos_asignacion["Fecha de Devolución"]
                        campos_base.remove("Fecha de Devolución")
                elif tipo_input == "2":
                    datos_asignacion[campo_actual] = "Préstamo"
                    if "Fecha de Devolución" not in datos_asignacion:
                        # Insertamos el campo en la posición correcta para el flujo
                        datos_asignacion["Fecha de Devolución"] = ""
                        campos_base.insert(4, "Fecha de Devolución")
                else:
                    print(Fore.RED + "Opción inválida.")
                    pausar_pantalla()
                    continue
            
            elif campo_actual == "Nombre de la Persona":
                nombre_input = input(Fore.YELLOW + "¿Quién recibirá el equipo? Nombre completo: " + Style.RESET_ALL).strip()
                nombre_asignado = formatear_y_validar_nombre(nombre_input)
                if not nombre_asignado:
                    print(Fore.RED + "Nombre inválido. Debe contener al menos nombre y apellido.")
                    pausar_pantalla()
                    continue
                datos_asignacion[campo_actual] = nombre_asignado

            elif campo_actual == "Email de la Persona":
                email_asignado = input(Fore.YELLOW + "Ingrese el correo corporativo del usuario: " + Style.RESET_ALL).strip().lower()
                if not validar_email(email_asignado):
                    print(Fore.RED + "Ingrese un correo corporativo válido.")
                    pausar_pantalla()
                    continue
                try:
                    dominio_email = email_asignado.split('@')[1]
                    dominios_activos = [d['valor'] for d in dominios_permitidos]
                    if dominio_email not in dominios_activos:
                        print(Fore.RED + f"❌ Dominio '{dominio_email}' no permitido.")
                        print(Fore.CYAN + "Dominios permitidos: " + ", ".join(dominios_activos))
                        pausar_pantalla()
                        continue
                except IndexError:
                    print(Fore.RED + "Ingrese un correo corporativo válido.")
                    pausar_pantalla()
                    continue
                datos_asignacion[campo_actual] = email_asignado

            elif campo_actual == "Observación":
                observacion = input(Fore.YELLOW + "Ingrese una Observación (obligatoria): " + Style.RESET_ALL).strip()
                if not observacion:
                    print(Fore.RED + "La observación es obligatoria.")
                    pausar_pantalla()
                    continue
                datos_asignacion[campo_actual] = observacion

            elif campo_actual == "Fecha de Devolución":
                fecha_str = input(Fore.YELLOW + "¿Hasta qué fecha se prestará el equipo? (DD/MM/AAAA): " + Style.RESET_ALL).strip()
                fecha_dt = validar_formato_fecha(fecha_str)
                if not fecha_dt or fecha_dt.date() <= datetime.now().date():
                    print(Fore.RED + "Fecha inválida o no es posterior a la fecha actual.")
                    pausar_pantalla()
                    continue
                datos_asignacion[campo_actual] = fecha_str
            
            indice_actual += 1

        # Resumen final y confirmación
        mostrar_encabezado("Resumen de la Operación", color=Fore.CYAN)
        print(f"  {'Equipo (Placa):'.ljust(25)}: {Fore.YELLOW}{equipo.placa}{Style.RESET_ALL}")
        for campo, valor in datos_asignacion.items():
            print(f"  {campo.ljust(25)}: {Fore.GREEN}{valor}{Style.RESET_ALL}")
        print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

        if not confirmar_con_placa(equipo.placa):
            return

        # Actualización del equipo y registro del log
        es_prestamo = datos_asignacion["Tipo de Operación"] == "Préstamo"
        equipo.estado = "En préstamo" if es_prestamo else "Asignado"
        equipo.asignado_a = datos_asignacion["Nombre de la Persona"]
        equipo.email_asignado = datos_asignacion["Email de la Persona"]
        equipo.fecha_devolucion_prestamo = datos_asignacion.get("Fecha de Devolución")
        
        detalles_log = f"{datos_asignacion['Tipo de Operación']} a {equipo.asignado_a}. Obs: {datos_asignacion['Observación']}"
        if es_prestamo:
            detalles_log += f". Devolución: {equipo.fecha_devolucion_prestamo}"

        db_manager.update_equipo(equipo)
        registrar_movimiento_inventario(equipo.placa, datos_asignacion["Tipo de Operación"], detalles_log, usuario)
        print(Fore.GREEN + f"\n✅ El equipo {equipo.placa} fue exitosamente asignado a {equipo.asignado_a}.")
        print(Fore.CYAN + f"🔄 Nuevo estado del equipo: '{equipo.estado}'")


    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
    finally:
        pausar_pantalla()

# --- FIN DE MODIFICACIÓN PARA ASIGNACIÓN DE EQUIPO ---


# --- FUNCIONES DE UTILIDAD Y VALIDACIÓN (Sin cambios) ---
def validar_placa_unica(placa: str) -> bool:
    return db_manager.get_equipo_by_placa(placa) is None

def validar_email(email: str) -> bool:
    # Expresión regular mejorada para validar emails
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def validar_placa_formato(placa: str) -> bool:
    return len(placa) >= 4 and placa.isalnum()

def validar_formato_fecha(fecha_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y")
    except ValueError:
        return None
        
def calcular_antiguedad(fecha_str: str) -> str:
    """Calcula la diferencia entre una fecha dada y hoy, en años, meses y días."""
    if not fecha_str:
        return "N/A"
    try:
        fecha_inicio = datetime.strptime(fecha_str.split(" ")[0], "%Y-%m-%d")
        hoy = datetime.now()
        diferencia = abs(hoy - fecha_inicio)
        
        anios = diferencia.days // 365
        meses = (diferencia.days % 365) // 30
        dias = (diferencia.days % 365) % 30
        
        return f"{anios} años, {meses} meses, {dias} días"
    except (ValueError, IndexError):
        return "Fecha inválida"

def validar_campo_general(texto: str) -> bool:
    if not texto: return False
    return re.match(r'^[A-Za-z0-9\s\-_.,()]+$', texto) is not None

def validar_serial(serial: str) -> bool:
    if not serial: return False
    return serial.isalnum()

def formatear_y_validar_nombre(nombre: str) -> Optional[str]:
    """
    Valida que el nombre tenga al menos dos palabras y lo formatea a tipo título.
    Devuelve el nombre formateado o None si no es válido.
    """
    partes = nombre.strip().split()
    if len(partes) < 2:
        return None
    # Pone en mayúscula la primera letra de cada palabra y las une con un espacio
    return ' '.join(p.capitalize() for p in partes)

# --- NUEVA FUNCIÓN DE AYUDA PARA FORMATEO DE TEXTO ---
def format_wrapped_text(label: str, text: str, width: int = 90) -> str:
    """
    Formatea un texto largo para que se ajuste a la consola con una indentación
    consistente después de la etiqueta.
    """
    label_width = len(label)
    subsequent_indent = ' ' * label_width
    
    wrapper = textwrap.TextWrapper(
        initial_indent=label,
        width=width,
        subsequent_indent=subsequent_indent,
        break_long_words=False,
        replace_whitespace=False
    )
    return wrapper.fill(text)
    
# --- FUNCIONES PRINCIPALES DE INVENTARIO ---
def seleccionar_parametro(tipo_parametro: Optional[str], nombre_amigable: str, lista_opciones: Optional[List[str]] = None, valor_actual: Optional[str] = None) -> Optional[str]:
    """Función mejorada para seleccionar un parámetro, con opción de mantener el valor actual."""
    parametros = lista_opciones if lista_opciones is not None else [p['valor'] for p in db_manager.get_parametros_por_tipo(tipo_parametro, solo_activos=True)]
    
    while True:
        print(Fore.GREEN + f"\nSeleccione un {nombre_amigable}:")
        if valor_actual:
            print(Fore.CYAN + f"-> Valor actual: {valor_actual}. Deje en blanco y presione Enter para mantenerlo." + Style.RESET_ALL)
        
        for i, param in enumerate(parametros, 1):
            print(f"{i}. {param}")
        print()

        seleccion = input(Fore.YELLOW + "Opción: " + Style.RESET_ALL).strip()
        
        if not seleccion and valor_actual:
            return valor_actual

        try:
            idx = int(seleccion) - 1
            if 0 <= idx < len(parametros):
                return parametros[idx]
            else:
                print(Fore.RED + "Selección fuera de rango.")
        except ValueError:
            print(Fore.RED + "Por favor, ingrese un número.")


@requiere_permiso("gestionar_equipo")
def gestionar_equipos(usuario: str):
    mostrar_encabezado("Gestión de Equipos", color=Fore.BLUE)
    try:
        print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para regresar." + Style.RESET_ALL)
        
        # 1. Equipos nuevos
        equipos_nuevos = db_manager.get_new_equipos()
        if equipos_nuevos:
            print(Fore.GREEN + "\n--- Equipos Nuevos (sin gestión) ---" + Style.RESET_ALL)
            for equipo in equipos_nuevos:
                print(f"  - Placa: {equipo['placa']}, Tipo: {equipo['tipo']}, Marca: {equipo['marca']} {Fore.CYAN}(New){Style.RESET_ALL}")
        
        # 2. Equipos disponibles (no nuevos)
        equipos_disponibles = db_manager.get_available_not_new_equipos()
        if equipos_disponibles:
            print(Fore.CYAN + "\n--- Equipos Disponibles (con historial) ---" + Style.RESET_ALL)
            for equipo in equipos_disponibles:
                print(f"  - Placa: {equipo['placa']}, Tipo: {equipo['tipo']}, Marca: {equipo['marca']}")

        # 3. Último equipo gestionado por el usuario
        ultimo_gestionado_log = db_manager.get_last_movimientos_by_user(usuario, limit=1)
        if ultimo_gestionado_log:
            ultimo_equipo = ultimo_gestionado_log[0]
            print(Fore.MAGENTA + "\n--- Último Equipo Gestionado por ti ---" + Style.RESET_ALL)
            fecha_dt = datetime.strptime(ultimo_equipo['fecha'], '%Y-%m-%d %H:%M:%S')
            print(f"  - Placa: {ultimo_equipo['equipo_placa']}, Acción: {ultimo_equipo['accion']}, Fecha: {fecha_dt.strftime('%d/%m/%Y')}")

        print("-" * 50)

        while True:
            placa = input(Fore.YELLOW + "\nIngrese la placa del equipo a gestionar: " + Style.RESET_ALL).strip().upper()
            
            equipo_data = db_manager.get_equipo_by_placa(placa)

            if not equipo_data:
                print(Fore.RED + "❌ No se encontró un equipo con esa placa. Intente de nuevo.")
                continue
            
            equipo = Equipo(**equipo_data)
            menu_gestion_especifica(usuario, equipo)
            break 

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación de gestión cancelada.")
        pausar_pantalla()

# gestion_inventario.py

def menu_gestion_especifica(usuario: str, equipo: Equipo):
    while True:
        # La llamada a mostrar_encabezado se encarga de limpiar la pantalla al inicio de cada ciclo.
        mostrar_encabezado(f"Gestionando Equipo - PLACA: {equipo.placa}", color=Fore.GREEN)
        
        print(Fore.CYAN + "--- Información del Equipo ---")
        print(f"  {'Tipo:'.ljust(25)} {equipo.tipo}")
        print(f"  {'Marca:'.ljust(25)} {equipo.marca}")
        print(f"  {'Modelo:'.ljust(25)} {equipo.modelo}")
        print(f"  {'Serial:'.ljust(25)} {equipo.serial}")
        
        print(Fore.CYAN + "\n--- Estado y Asignación ---")
        
        ultimo_movimiento = db_manager.get_last_movimiento_by_placa(equipo.placa)
        fecha_estado = ""
        if ultimo_movimiento:
            fecha_obj = datetime.strptime(ultimo_movimiento['fecha'], "%Y-%m-%d %H:%M:%S")
            fecha_estado = f" / Desde el {fecha_obj.strftime('%d/%m/%Y')}"

        print(f"  {'Estado actual:'.ljust(25)} {equipo.estado}{fecha_estado}")

        if equipo.asignado_a:
            print(f"  {'Asignado a:'.ljust(25)} {equipo.asignado_a} ({equipo.email_asignado})")
        if equipo.fecha_devolucion_prestamo:
            print(f"  {'Fecha devolución (Préstamo):'.ljust(25)} {equipo.fecha_devolucion_prestamo}")
        
        if equipo.estado in ["En mantenimiento", "Pendiente Devolución a Proveedor", "Devuelto a Proveedor", "Renovación"]:
            print(Fore.YELLOW + f"⚠️  Este equipo está '{equipo.estado}'. Las acciones de gestión están limitadas.")
            opciones_limitadas = [
                "Ver Detalles Completos del Equipo",
                "Ver Historial del Equipo (Excel)",
                "Volver al menú anterior"
            ]
            mostrar_menu(opciones_limitadas, "Opciones de Consulta")
            opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
            if opcion == '1':
                mostrar_detalles_equipo(equipo)
            elif opcion == '2':
                generar_excel_historico_equipo(usuario, equipo)
            elif opcion == '3':
                break
            else:
                print(Fore.RED + "❌ Opción no válida.")
                pausar_pantalla()
            continue
        
        opciones_gestion = []
        if equipo.estado == "Disponible":
            opciones_gestion.extend([
                "Asignar/Prestar equipo",
                "Registrar para mantenimiento",
                "Registrar para devolución a Proveedor",
            ])
        elif equipo.estado in ["Asignado", "En préstamo"]:
            opciones_gestion.extend([
                "Devolver equipo al inventario",
                "Registrar para mantenimiento",
            ])
        if equipo.estado == "Asignado":
            opciones_gestion.append("Renovación de equipo")

        opciones_gestion.extend([
            "Ver Detalles Completos del Equipo",
            "Ver Historial del Equipo (Excel)",
            "Editar información del equipo",
            "Eliminar equipo",
            "Volver al menú anterior"
        ])
        
        mostrar_menu(opciones_gestion, titulo="Opciones disponibles para este equipo")
        opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()

        try:
            opcion_idx = int(opcion) - 1
            if 0 <= opcion_idx < len(opciones_gestion):
                opcion_texto = opciones_gestion[opcion_idx]
                
                if "Asignar/Prestar equipo" in opcion_texto: asignar_o_prestar_equipo(usuario, equipo)
                elif "Devolver equipo al inventario" in opcion_texto: devolver_equipo(usuario, equipo)
                elif "Registrar para mantenimiento" in opcion_texto: registrar_mantenimiento(usuario, equipo)
                elif "Registrar para devolución a Proveedor" in opcion_texto: registrar_devolucion_a_proveedor(usuario, equipo)
                elif "Renovación de equipo" in opcion_texto:
                    if registrar_renovacion(usuario, equipo): return
                elif "Ver Detalles Completos del Equipo" in opcion_texto: mostrar_detalles_equipo(equipo)
                elif "Ver Historial del Equipo (Excel)" in opcion_texto: generar_excel_historico_equipo(usuario, equipo)
                elif "Editar información del equipo" in opcion_texto: editar_equipo(usuario, equipo)
                elif "Eliminar equipo" in opcion_texto:
                    if eliminar_equipo(usuario, equipo): return
                elif "Volver al menú anterior" in opcion_texto: break
            else:
                print(Fore.RED + "❌ Opción no válida. Por favor, intente de nuevo.")
                pausar_pantalla()
        except ValueError:
            print(Fore.RED + "❌ Entrada no válida. Por favor, intente de nuevo.")
            pausar_pantalla()
        
        equipo_data_actualizado = db_manager.get_equipo_by_placa(equipo.placa)
        if not equipo_data_actualizado: break
        equipo = Equipo(**equipo_data_actualizado)

def mostrar_detalles_equipo(equipo: Equipo):
    """Muestra una vista detallada y contextual de la información de un equipo."""
    os.system('cls' if os.name == 'nt' else 'clear')
    mostrar_encabezado(f"Detalles Completos del Equipo: Placa {equipo.placa}", color=Fore.CYAN)

    # --- Sección 1: Información General ---
    print(Fore.CYAN + "--- Información del Equipo ---" + Style.RESET_ALL)
    print(f"  {'Placa:'.ljust(28)} {equipo.placa}")
    print(f"  {'Tipo:'.ljust(28)} {equipo.tipo}")
    print(f"  {'Marca:'.ljust(28)} {equipo.marca}")
    print(f"  {'Modelo:'.ljust(28)} {equipo.modelo}")
    print(f"  {'Serial:'.ljust(28)} {equipo.serial}")
    print(f"  {'Fecha de Registro:'.ljust(28)} {equipo.fecha_registro}")

    # --- Sección 2: Estado y Asignación (Contextual) ---
    print(Fore.CYAN + "\n--- Estado y Asignación ---" + Style.RESET_ALL)
    
    ultimo_movimiento = db_manager.get_last_movimiento_by_placa(equipo.placa)
    fecha_estado = ""
    if ultimo_movimiento:
        fecha_obj = datetime.strptime(ultimo_movimiento['fecha'], "%Y-%m-%d %H:%M:%S")
        fecha_estado = f" / Desde el {fecha_obj.strftime('%d/%m/%Y')}"

    print(f"  {'Estado Actual:'.ljust(28)} {equipo.estado}{fecha_estado}")

    if equipo.asignado_a:
        print(f"  {'Asignado a:'.ljust(28)} {equipo.asignado_a} ({equipo.email_asignado or 'Sin email'})")

    if equipo.estado == "En préstamo" and equipo.fecha_devolucion_prestamo:
        print(f"  {'Fecha Devolución Préstamo:'.ljust(28)} {equipo.fecha_devolucion_prestamo}")
    
    if equipo.estado == "Renovación" and equipo.renovacion_placa_asociada:
        print(Fore.CYAN + "\n--- Detalles de la Renovación ---" + Style.RESET_ALL)
        print(f"  {'Equipo de reemplazo:'.ljust(28)} {equipo.renovacion_placa_asociada}")
        print(f"  {'Fecha Máx. de Entrega:'.ljust(28)} {equipo.fecha_entrega_renovacion}")
        
        log_renovacion = db_manager.get_last_log_by_action(equipo.placa, 'Inicio Renovación')
        if log_renovacion:
            label = f"  {'Observaciones:'.ljust(28)}"
            print(format_wrapped_text(label, log_renovacion['detalles']))

    # --- Sección 3: Información Contextual por Estado ---
    log_mantenimiento = db_manager.get_last_log_by_action(equipo.placa, 'Mantenimiento')
    if equipo.estado == "En mantenimiento" and log_mantenimiento:
        print(Fore.CYAN + "\n--- Detalles del Mantenimiento ---" + Style.RESET_ALL)
        fecha_evento = datetime.strptime(log_mantenimiento['fecha'], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        print(f"  {'Fecha de Registro:'.ljust(28)} {fecha_evento}")
        print(f"  {'Registrado por:'.ljust(28)} {log_mantenimiento['usuario']}")
        
        label = f"  {'Detalles:'.ljust(28)}"
        print(format_wrapped_text(label, log_mantenimiento['detalles']))

    log_devolucion = db_manager.get_last_log_by_action(equipo.placa, 'Registro Devolución Proveedor')
    if equipo.estado == "Pendiente Devolución a Proveedor" and log_devolucion:
        print(Fore.CYAN + "\n--- Detalles de Devolución a Proveedor ---" + Style.RESET_ALL)
        fecha_evento = datetime.strptime(log_devolucion['fecha'], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        print(f"  {'Fecha de Registro:'.ljust(28)} {fecha_evento}")
        print(f"  {'Registrado por:'.ljust(28)} {log_devolucion['usuario']}")
        print(f"  {'Motivo:'.ljust(28)} {equipo.motivo_devolucion}")
        print(f"  {'Fecha Programada:'.ljust(28)} {equipo.fecha_devolucion_proveedor}")
        
        label = f"  {'Observaciones:'.ljust(28)}"
        print(format_wrapped_text(label, equipo.observaciones))

    log_devolucion_completada = db_manager.get_last_log_by_action(equipo.placa, 'Devolución a Proveedor Completada')
    if equipo.estado == "Devuelto a Proveedor" and log_devolucion_completada:
        print(Fore.CYAN + "\n--- Detalles de la Devolución Completada ---" + Style.RESET_ALL)
        fecha_evento = datetime.strptime(log_devolucion_completada['fecha'], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        print(f"  {'Fecha de Ejecución:'.ljust(28)} {fecha_evento}")
        print(f"  {'Confirmado por:'.ljust(28)} {log_devolucion_completada['usuario']}")
        print(f"  {'Motivo Original:'.ljust(28)} {equipo.motivo_devolucion}")
        
        label = f"  {'Observaciones Finales:'.ljust(28)}"
        print(format_wrapped_text(label, log_devolucion_completada['detalles']))

    # --- Sección 4: Últimos Movimientos ---
    print(Fore.CYAN + "\n--- Últimos 5 Movimientos ---" + Style.RESET_ALL)
    ultimos_movimientos = db_manager.get_log_by_placa(equipo.placa, limit=5)
    if not ultimos_movimientos:
        print("  No hay movimientos registrados para este equipo.")
    else:
        print(f"  {Fore.YELLOW}{'FECHA':<20} {'ACCIÓN':<30} {'USUARIO':<15}{Style.RESET_ALL}")
        print(f"  {'-'*18} {'-'*28} {'-'*13}")
        for mov in ultimos_movimientos:
            fecha_obj = datetime.strptime(mov['fecha'], "%Y-%m-%d %H:%M:%S")
            fecha_formateada = fecha_obj.strftime("%d/%m/%Y %H:%M")
            print(f"  {fecha_formateada:<20} {mov['accion']:<30} {mov['usuario']:<15}")

    pausar_pantalla()

def _mostrar_formulario_devolucion_inventario(equipo: Equipo, campos: List[str], datos: Dict[str, str], indice_actual: int):
    """
    Muestra el formulario interactivo para la devolución de un equipo al inventario.
    """
    mostrar_encabezado(f"Devolver Equipo al Inventario - Placa: {equipo.placa}", color=Fore.BLUE)

    # Mostrar información del equipo que se devuelve
    print(Fore.CYAN + "--- Información del Equipo ---")
    print(f"  {'Placa:'.ljust(25)} {equipo.placa}")
    print(f"  {'Tipo:'.ljust(25)} {equipo.tipo}")
    print(f"  {'Actualmente asignado a:'.ljust(25)} {equipo.asignado_a or 'N/A'}")
    print(Style.RESET_ALL)

    print(Fore.CYAN + "💡 Complete el siguiente campo. Puede presionar Ctrl+C para cancelar." + Style.RESET_ALL)
    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

    for i, campo in enumerate(campos):
        indicador = Fore.YELLOW + " -> " if i == indice_actual else "    "
        valor_mostrado = datos.get(campo, "")
        if valor_mostrado:
            valor_mostrado = f"{Fore.GREEN}{valor_mostrado}{Style.RESET_ALL}"
        print(f"{indicador}{campo.ljust(30)}: {valor_mostrado}")

    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

@requiere_permiso("gestionar_equipo")
def devolver_equipo(usuario: str, equipo: Equipo):
    """
    Función mejorada para devolver un equipo al inventario con una interfaz interactiva.
    """
    if equipo.estado not in ["Asignado", "En préstamo"]:
        print(Fore.RED + "❌ El equipo no está asignado ni en préstamo.")
        pausar_pantalla()
        return

    campos_requeridos = ["Motivo u observación de la devolución"]
    datos_devolucion = {campo: "" for campo in campos_requeridos}
    indice_actual = 0

    try:
        while indice_actual < len(campos_requeridos):
            campo_actual = campos_requeridos[indice_actual]
            _mostrar_formulario_devolucion_inventario(equipo, campos_requeridos, datos_devolucion, indice_actual)

            if campo_actual == "Motivo u observación de la devolución":
                observacion = input(Fore.YELLOW + "Ingrese el motivo (obligatorio): " + Style.RESET_ALL).strip()
                if not observacion:
                    print(Fore.RED + "La observación es obligatoria para la devolución. Intente de nuevo.")
                    pausar_pantalla()
                    continue
                datos_devolucion[campo_actual] = observacion
            
            indice_actual += 1

        mostrar_encabezado("Resumen de la Devolución", color=Fore.CYAN)
        print(f"  {'Equipo (Placa):'.ljust(25)} {equipo.placa}")
        print(f"  {'Se retirará de:'.ljust(25)} {equipo.asignado_a or 'N/A'}")
        print(f"  {'Estado anterior:'.ljust(25)} {equipo.estado}")
        print(f"  {'Nuevo estado:'.ljust(25)} {Fore.GREEN}Disponible{Style.RESET_ALL}")
        print(f"  {'Observación:'.ljust(25)} {datos_devolucion['Motivo u observación de la devolución']}")
        print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

        if not confirmar_con_placa(equipo.placa):
            return

        detalles_previos = f"Devuelto por {equipo.asignado_a or 'N/A'}. Motivo: {datos_devolucion['Motivo u observación de la devolución']}"
        equipo.estado = "Disponible"
        equipo.asignado_a = None
        equipo.email_asignado = None
        equipo.fecha_devolucion_prestamo = None
        
        db_manager.update_equipo(equipo)
        registrar_movimiento_inventario(equipo.placa, "Devolución a Inventario", detalles_previos, usuario)
        print(Fore.GREEN + f"\n✅ ¡Devolución confirmada! Equipo {equipo.placa} ahora está 'Disponible'.")

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
    finally:
        pausar_pantalla()

def _mostrar_formulario_edicion(equipo: Equipo, campos: List[str], datos: Dict[str, str], indice_actual: int):
    """
    Muestra el formulario interactivo para editar la información de un equipo.
    """
    mostrar_encabezado(f"Editando Equipo: {equipo.placa}", color=Fore.BLUE)
    print(Fore.CYAN + "💡 Modifique los campos necesarios. Deje en blanco para mantener el valor actual." + Style.RESET_ALL)
    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

    for i, campo in enumerate(campos):
        indicador = Fore.YELLOW + " -> " if i == indice_actual else "    "
        valor_actual = getattr(equipo, campo.lower().replace(" ", "_").replace("ú", "u"))
        valor_mostrado = datos.get(campo, "")
        if valor_mostrado:
            valor_mostrado = f"{Fore.GREEN}{valor_mostrado}{Style.RESET_ALL}"
        else:
            valor_mostrado = f"{Fore.CYAN}(Actual: {valor_actual}){Style.RESET_ALL}"
        print(f"{indicador}{campo.ljust(20)}: {valor_mostrado}")

    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)


@requiere_permiso("gestionar_equipo")
def editar_equipo(usuario: str, equipo: Equipo):
    """Función mejorada para editar un equipo con una interfaz interactiva."""
    campos_editables = ["Tipo", "Marca", "Modelo", "Serial"]
    datos_nuevos = {campo: "" for campo in campos_editables}
    indice_actual = 0

    try:
        while indice_actual < len(campos_editables):
            campo_actual = campos_editables[indice_actual]
            # Mapeo de nombres de campo a los nombres de los parámetros en la BD
            mapa_parametros = {"Tipo": "tipo_equipo", "Marca": "marca_equipo"}

            _mostrar_formulario_edicion(equipo, campos_editables, datos_nuevos, indice_actual)

            if campo_actual in ["Tipo", "Marca"]:
                tipo_parametro = mapa_parametros[campo_actual]
                valor_actual_equipo = getattr(equipo, campo_actual.lower())
                nuevo_valor = seleccionar_parametro(tipo_parametro, campo_actual, valor_actual=valor_actual_equipo)
                if not nuevo_valor:  # Si el usuario cancela la selección
                    continue
                datos_nuevos[campo_actual] = nuevo_valor
            else:
                valor_actual_equipo = getattr(equipo, campo_actual.lower())
                prompt = f"Ingrese el nuevo {campo_actual} ({Fore.CYAN}{valor_actual_equipo}{Fore.YELLOW}): {Style.RESET_ALL}"
                nuevo_valor_input = input(Fore.YELLOW + prompt).strip() or valor_actual_equipo

                if campo_actual == "Modelo" and not validar_campo_general(nuevo_valor_input):
                    print(Fore.RED + "Modelo inválido. Solo se permiten letras, números, espacios y (- _ . ,).")
                    pausar_pantalla()
                    continue
                elif campo_actual == "Serial" and not validar_serial(nuevo_valor_input):
                    print(Fore.RED + "Número de serie inválido. No se permiten espacios ni símbolos.")
                    pausar_pantalla()
                    continue
                datos_nuevos[campo_actual] = nuevo_valor_input
            
            indice_actual += 1

        cambios = []
        if equipo.tipo != datos_nuevos["Tipo"]: cambios.append(f"Tipo: '{equipo.tipo}' -> '{datos_nuevos['Tipo']}'")
        if equipo.marca != datos_nuevos["Marca"]: cambios.append(f"Marca: '{equipo.marca}' -> '{datos_nuevos['Marca']}'")
        if equipo.modelo != datos_nuevos["Modelo"]: cambios.append(f"Modelo: '{equipo.modelo}' -> '{datos_nuevos['Modelo']}'")
        if equipo.serial != datos_nuevos["Serial"]: cambios.append(f"Serial: '{equipo.serial}' -> '{datos_nuevos['Serial']}'")

        if not cambios:
            print(Fore.YELLOW + "\nNo se detectaron cambios.")
            pausar_pantalla()
            return

        while True:
            motivo_edicion = input(Fore.YELLOW + "Motivo de la edición (obligatorio): " + Style.RESET_ALL).strip()
            if motivo_edicion:
                break
            print(Fore.RED + "El motivo de la edición es obligatorio.")

        mostrar_encabezado("Resumen de Cambios", color=Fore.CYAN)
        for cambio in cambios:
            print(f"  - {cambio}")
        print(f"  - {Fore.YELLOW}Motivo:{Style.RESET_ALL} {motivo_edicion}")
        print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

        if not confirmar_con_placa(equipo.placa):
            return

        equipo.tipo, equipo.marca, equipo.modelo, equipo.serial = datos_nuevos["Tipo"], datos_nuevos["Marca"], datos_nuevos["Modelo"], datos_nuevos["Serial"]
        db_manager.update_equipo(equipo)
        detalles_log = f"Cambios: {'; '.join(cambios)}. Motivo: {motivo_edicion}"
        registrar_movimiento_inventario(equipo.placa, "Edición", detalles_log, usuario)
        print(Fore.GREEN + f"\n✅ ¡Equipo {equipo.placa} actualizado exitosamente!")

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación de edición cancelada.")
    finally:
        pausar_pantalla()

@requiere_permiso("gestionar_equipo")
def registrar_renovacion(usuario: str, equipo_actual: Equipo) -> bool:
    """Inicia y procesa la renovación de un equipo por uno nuevo."""
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        mostrar_encabezado("Proceso de Renovación de Equipo", color=Fore.YELLOW)
        
        print(Fore.CYAN + "💡 Este proceso requiere que el nuevo equipo ya esté registrado en el sistema.")
        
        # Mostrar equipos disponibles
        equipos_nuevos = db_manager.get_new_equipos()
        if equipos_nuevos:
            print(Fore.GREEN + "\n--- Equipos Nuevos (sin gestión) ---" + Style.RESET_ALL)
            for equipo in equipos_nuevos:
                print(f"  - Placa: {equipo['placa']}, Tipo: {equipo['tipo']}, Marca: {equipo['marca']}")
        
        equipos_disponibles = db_manager.get_available_not_new_equipos()
        if equipos_disponibles:
            print(Fore.CYAN + "\n--- Equipos Disponibles (con historial) ---" + Style.RESET_ALL)
            for equipo in equipos_disponibles:
                print(f"  - Placa: {equipo['placa']}, Tipo: {equipo['tipo']}, Marca: {equipo['marca']}")

        justificacion = ""
        while True:
            placa_nuevo_equipo = input(Fore.YELLOW + "\nIngrese la placa del NUEVO equipo para este usuario: " + Style.RESET_ALL).strip().upper()
            if not placa_nuevo_equipo: continue
            
            equipo_nuevo_data = db_manager.get_equipo_by_placa(placa_nuevo_equipo)
            if not equipo_nuevo_data:
                print(Fore.RED + f"\nLa placa '{placa_nuevo_equipo}' no existe.")
                print(Fore.YELLOW + "Por favor, vaya a 'Registrar nuevo equipo', créelo y vuelva a ejecutar esta operación.")
                return False
            
            if equipo_nuevo_data['estado'] != 'Disponible':
                print(Fore.RED + f"El equipo '{placa_nuevo_equipo}' no está 'Disponible' (Estado actual: {equipo_nuevo_data['estado']}).")
                continue
            
            # Verificación si el equipo es nuevo (solo 1 movimiento)
            num_movimientos = db_manager.count_movimientos_by_placa(placa_nuevo_equipo)
            if num_movimientos > 1:
                print(Fore.YELLOW + f"⚠️  ADVERTENCIA: El equipo '{placa_nuevo_equipo}' no es nuevo (tiene {num_movimientos} movimientos).")
                confirmacion = input("¿Desea continuar de todas formas? (S/N): ").strip().upper()
                if confirmacion != 'S':
                    print("Operación cancelada.")
                    return False
                
                while True:
                    justificacion = input(Fore.YELLOW + "Por favor, ingrese una justificación para usar este equipo: " + Style.RESET_ALL).strip()
                    if justificacion:
                        break
                    print(Fore.RED + "La justificación es obligatoria.")

            equipo_nuevo = Equipo(**equipo_nuevo_data)
            break
            
        print(Fore.YELLOW + textwrap.dedent("""
            \n⚠️  ATENCIÓN: Este proceso implica realizar el cambio del equipo por otro.
            Este equipo se enviará al proveedor. Si va a ser utilizado nuevamente
            deberá ser reactivado en 'Registrar nuevo equipo'."""))

        antiguedad_equipo = calcular_antiguedad(equipo_actual.fecha_registro)
        log_asignacion = db_manager.get_last_log_by_action(equipo_actual.placa, 'Asignación')
        fecha_asignacion_usuario = log_asignacion['fecha'] if log_asignacion else "No registrada"
        antiguedad_usuario = calcular_antiguedad(fecha_asignacion_usuario)

        print(Fore.CYAN + "\n--- Resumen de la Acción ---")
        print(f"  Datos del equipo actual (Placa: {equipo_actual.placa})")
        print(f"  Fecha de registro: {equipo_actual.fecha_registro} (Antigüedad: {antiguedad_equipo})")
        print(f"  Asignado a {equipo_actual.asignado_a} desde {fecha_asignacion_usuario} (Antigüedad: {antiguedad_usuario})")
        print("-" * 50)

        if not confirmar_con_placa(equipo_actual.placa): return False
            
        while True:
            fecha_max_entrega_str = input(Fore.YELLOW + "Fecha máxima de entrega del equipo actual (DD/MM/AAAA): " + Style.RESET_ALL).strip()
            if validar_formato_fecha(fecha_max_entrega_str):
                break
            print(Fore.RED + "Formato de fecha inválido.")

        observaciones = input(Fore.YELLOW + "Observaciones sobre la renovación: " + Style.RESET_ALL).strip() or "Sin observaciones."
        if justificacion:
            observaciones = f"Justificación equipo no nuevo: {justificacion}. {observaciones}"

        os.system('cls' if os.name == 'nt' else 'clear')
        mostrar_encabezado("Confirmación Final de Renovación", color=Fore.RED)
        print(f"  - Equipo actual a devolver: {equipo_actual.placa} ({equipo_actual.modelo})")
        print(f"  - Nuevo equipo a asignar:   {equipo_nuevo.placa} ({equipo_nuevo.modelo})")
        print(f"  - Usuario:                  {equipo_actual.asignado_a}")
        print(Fore.RED + f"  - Fecha máx. de entrega:    {fecha_max_entrega_str}")
        print(f"  - Observaciones:            {observaciones}")
        print("-" * 60)
        
        print(Fore.YELLOW + "Para confirmar la operación, ingrese ambas placas.")
        conf_placa_actual = input(f"  > Ingrese placa del equipo actual ({equipo_actual.placa}): ").strip().upper()
        conf_placa_nueva = input(f"  > Ingrese placa del nuevo equipo ({equipo_nuevo.placa}): ").strip().upper()

        if conf_placa_actual != equipo_actual.placa or conf_placa_nueva != equipo_nuevo.placa:
            print(Fore.RED + "\n❌ Las placas no coinciden. Operación cancelada.")
            return False

        # Ambos equipos se bloquean en estado "Renovación"
        # Actualizar equipo actual (el que se devuelve)
        equipo_actual.estado = "Renovación"
        equipo_actual.fecha_entrega_renovacion = fecha_max_entrega_str
        equipo_actual.renovacion_placa_asociada = equipo_nuevo.placa
        db_manager.update_equipo(equipo_actual)
        registrar_movimiento_inventario(equipo_actual.placa, "Inicio Renovación", f"Reemplazado por {equipo_nuevo.placa}. Obs: {observaciones}", usuario)

        # Actualizar equipo nuevo (el que se asignará)
        equipo_nuevo.estado = "Renovación"
        equipo_nuevo.renovacion_placa_asociada = equipo_actual.placa
        db_manager.update_equipo(equipo_nuevo)
        registrar_movimiento_inventario(equipo_nuevo.placa, "Inicio Renovación", f"Reemplazo de {equipo_actual.placa}. Obs: {observaciones}", usuario)

        print(Fore.GREEN + "\n✅ Renovación registrada. Pendiente de aprobación por un Administrador.")
        return True

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación de renovación cancelada.")
        return False
    finally:
        pausar_pantalla()

# MODIFICADO: Se ha corregido el título y la lógica de presentación.
@requiere_permiso("gestionar_pendientes")
def menu_gestionar_pendientes(usuario: str):
    while True:
        # Se elimina la limpieza de pantalla redundante. mostrar_encabezado ya lo hace.
        mostrar_encabezado("Gestionar Mantenimientos, Devoluciones y Renovaciones")
        
        equipos = db_manager.get_all_equipos()
        mantenimientos_pendientes = len([e for e in equipos if e.get('estado') == "En mantenimiento"])
        devoluciones_pendientes = len([e for e in equipos if e.get('estado') == "Pendiente Devolución a Proveedor"])
        renovaciones_pendientes = len([e for e in equipos if e.get('estado') == "Renovación" and e.get('fecha_entrega_renovacion')])

        def get_color_indicator(count):
            if count == 0: return Fore.GREEN
            elif count <= 2: return Fore.YELLOW
            return Fore.RED

        color_mantenimiento = get_color_indicator(mantenimientos_pendientes)
        color_devoluciones = get_color_indicator(devoluciones_pendientes)
        color_renovaciones = get_color_indicator(renovaciones_pendientes)
        
        texto_menu_mantenimiento = f"Gestionar Equipos en Mantenimiento {color_mantenimiento}({mantenimientos_pendientes}){Style.RESET_ALL}"
        texto_menu_devoluciones = f"Gestionar Devoluciones a Proveedor {color_devoluciones}({devoluciones_pendientes}){Style.RESET_ALL}"
        texto_menu_renovaciones = f"Gestionar Renovaciones Pendientes {color_renovaciones}({renovaciones_pendientes}){Style.RESET_ALL}"
        
        opciones_disponibles = [
            texto_menu_mantenimiento, 
            texto_menu_devoluciones, 
            texto_menu_renovaciones, 
            "Volver"
        ]
        
        # El título del menú se pasa directamente a mostrar_menu
        mostrar_menu(opciones_disponibles, titulo="")
        
        opcion_input = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
        
        opciones_map = {str(i+1): texto for i, texto in enumerate(opciones_disponibles)}
        opcion_texto = opciones_map.get(opcion_input)

        if opcion_texto and "Mantenimiento" in opcion_texto:
            gestionar_mantenimientos(usuario)
        elif opcion_texto and "Devoluciones" in opcion_texto:
            gestionar_devoluciones_proveedor(usuario)
        elif opcion_texto and "Renovaciones" in opcion_texto:
            gestionar_renovaciones(usuario)
        elif opcion_texto == "Volver":
            break
        else:
            print(Fore.RED + "Opción no válida.")
            pausar_pantalla()
        


        
def _mostrar_formulario_mantenimiento(equipo: Equipo, campos: List[str], datos: Dict[str, str], indice_actual: int):
    """
    Muestra el formulario interactivo para registrar un mantenimiento,
    incluyendo la información del equipo que se está gestionando.
    """
    mostrar_encabezado(f"Registrar Mantenimiento - Placa: {equipo.placa}", color=Fore.BLUE)
    
    # Mostrar información del equipo
    print(Fore.CYAN + "--- Información del Equipo ---")
    print(f"  {'Placa:'.ljust(15)} {equipo.placa}")
    print(f"  {'Tipo:'.ljust(15)} {equipo.tipo}")
    print(f"  {'Marca:'.ljust(15)} {equipo.marca}")
    print(f"  {'Modelo:'.ljust(15)} {equipo.modelo}")
    print(Style.RESET_ALL)
    
    print(Fore.CYAN + "💡 Complete los siguientes campos. Puede presionar Ctrl+C para cancelar." + Style.RESET_ALL)
    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

    for i, campo in enumerate(campos):
        indicador = Fore.YELLOW + " -> " if i == indice_actual else "    "
        valor_mostrado = datos.get(campo, "")
        if valor_mostrado:
            valor_mostrado = f"{Fore.GREEN}{valor_mostrado}{Style.RESET_ALL}"
        print(f"{indicador}{campo.ljust(25)}: {valor_mostrado}")

    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)


@requiere_permiso("gestionar_equipo")
def registrar_mantenimiento(usuario: str, equipo: Equipo):
    """Función mejorada para registrar un mantenimiento con una interfaz interactiva."""
    
    campos_requeridos = ["Tipo de Mantenimiento", "Observaciones"]
    datos_mantenimiento = {campo: "" for campo in campos_requeridos}
    indice_actual = 0

    try:
        while indice_actual < len(campos_requeridos):
            campo_actual = campos_requeridos[indice_actual]
            _mostrar_formulario_mantenimiento(equipo, campos_requeridos, datos_mantenimiento, indice_actual)

            if campo_actual == "Tipo de Mantenimiento":
                tipos_mantenimiento = ["Preventivo", "Correctivo", "Mejora"]
                tipo_seleccionado = seleccionar_parametro(None, "Tipo de Mantenimiento", lista_opciones=tipos_mantenimiento)
                if not tipo_seleccionado: # Si el usuario no selecciona nada
                    continue
                datos_mantenimiento[campo_actual] = tipo_seleccionado

            elif campo_actual == "Observaciones":
                observaciones = input(Fore.YELLOW + "Ingrese las Observaciones del mantenimiento: " + Style.RESET_ALL).strip()
                if not observaciones:
                    print(Fore.RED + "Las observaciones son obligatorias.")
                    pausar_pantalla()
                    continue
                datos_mantenimiento[campo_actual] = observaciones
            
            indice_actual += 1

        # Resumen final y confirmación
        mostrar_encabezado("Resumen del Mantenimiento", color=Fore.CYAN)
        print(f"  {'Equipo (Placa):'.ljust(25)}: {Fore.GREEN}{equipo.placa}{Style.RESET_ALL}")
        for campo, valor in datos_mantenimiento.items():
            print(f"  {campo.ljust(25)}: {Fore.GREEN}{valor}{Style.RESET_ALL}")
        print(f"  {'Nuevo estado:'.ljust(25)}: {Fore.GREEN}En mantenimiento{Style.RESET_ALL}")
        print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)
        
        if not confirmar_con_placa(equipo.placa):
            return

        # Actualización del equipo y registro del log
        equipo.estado_anterior = equipo.estado
        equipo.estado = "En mantenimiento"
        db_manager.update_equipo(equipo)
        
        detalles = f"Tipo: {datos_mantenimiento['Tipo de Mantenimiento']}. Obs: {datos_mantenimiento['Observaciones']}. Estado anterior: {equipo.estado_anterior}"
        registrar_movimiento_inventario(equipo.placa, "Mantenimiento", detalles, usuario)
        
        print(Fore.GREEN + f"\n✅ Mantenimiento registrado. El equipo {equipo.placa} ha cambiado su estado a 'En mantenimiento'.")

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
    finally:
        pausar_pantalla()

def _mostrar_formulario_devolucion(equipo: Equipo, campos: List[str], datos: Dict[str, str], indice_actual: int):
    """
    Muestra el formulario interactivo para registrar la devolución de un equipo a proveedor.
    """
    mostrar_encabezado(f"Devolución a Proveedor - Placa: {equipo.placa}", color=Fore.BLUE)
    print(Fore.CYAN + "--- Información del Equipo ---")
    print(f"  {'Placa:'.ljust(15)} {equipo.placa}")
    print(f"  {'Tipo:'.ljust(15)} {equipo.tipo}")
    print(f"  {'Marca:'.ljust(15)} {equipo.marca}")
    print(Style.RESET_ALL)
    
    print(Fore.CYAN + "💡 Complete los siguientes campos. Puede presionar Ctrl+C para cancelar." + Style.RESET_ALL)
    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

    for i, campo in enumerate(campos):
        indicador = Fore.YELLOW + " -> " if i == indice_actual else "    "
        valor_mostrado = datos.get(campo, "")
        if valor_mostrado:
            valor_mostrado = f"{Fore.GREEN}{valor_mostrado}{Style.RESET_ALL}"
        print(f"{indicador}{campo.ljust(35)}: {valor_mostrado}")

    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)


@requiere_permiso("devolver_a_proveedor")
def registrar_devolucion_a_proveedor(usuario: str, equipo: Equipo):
    """Función mejorada para registrar la devolución a proveedor con una interfaz interactiva y validaciones de fecha."""
    if equipo.estado != "Disponible":
        print(Fore.RED + f"❌ El equipo debe estar 'Disponible' (Estado actual: {equipo.estado}).")
        pausar_pantalla()
        return

    campos_requeridos = ["Motivo de la Devolución", "Fecha de devolución a proveedor", "Observaciones adicionales"]
    datos_devolucion = {campo: "" for campo in campos_requeridos}
    indice_actual = 0

    try:
        while indice_actual < len(campos_requeridos):
            campo_actual = campos_requeridos[indice_actual]
            _mostrar_formulario_devolucion(equipo, campos_requeridos, datos_devolucion, indice_actual)

            if campo_actual == "Motivo de la Devolución":
                motivos = ["Ya no se requiere", "Por daño", "Por hurto"]
                motivo = seleccionar_parametro(None, "Motivo de la Devolución", lista_opciones=motivos)
                if not motivo: continue
                datos_devolucion[campo_actual] = motivo
            
            elif campo_actual == "Fecha de devolución a proveedor":
                fecha_str = input(Fore.YELLOW + "¿Cuándo se entregó/entregará al proveedor? (DD/MM/AAAA): " + Style.RESET_ALL).strip()
                fecha_dt = validar_formato_fecha(fecha_str)

                if not fecha_dt:
                    print(Fore.RED + "Formato de fecha inválido.")
                    pausar_pantalla()
                    continue

                hoy = datetime.now()
                # Comparamos solo la parte de la fecha, ignorando la hora
                if fecha_dt.date() < hoy.date():
                    print(Fore.YELLOW + "\n⚠️ La fecha ingresada es anterior a hoy.")
                    confirmacion = input("¿Confirma que el equipo YA FUE ENTREGADO al proveedor? (S/N): ").strip().upper()
                    if confirmacion != 'S':
                        print(Fore.CYAN + "Operación cancelada. Por favor, revise la fecha.")
                        pausar_pantalla()
                        continue
                
                elif (fecha_dt.date() - hoy.date()).days > 30:
                    print(Fore.YELLOW + f"\n⚠️ La fecha ingresada es a más de 30 días en el futuro ({fecha_str}).")
                    confirmacion = input("¿Está seguro de que esta fecha es correcta? (S/N): ").strip().upper()
                    if confirmacion != 'S':
                        print(Fore.CYAN + "Operación cancelada. Por favor, revise la fecha.")
                        pausar_pantalla()
                        continue
                
                datos_devolucion[campo_actual] = fecha_str

            elif campo_actual == "Observaciones adicionales":
                observaciones = input(Fore.YELLOW + "Ingrese las observaciones (obligatorio): " + Style.RESET_ALL).strip()
                if not observaciones:
                    print(Fore.RED + "Las observaciones son obligatorias.")
                    pausar_pantalla()
                    continue
                datos_devolucion[campo_actual] = observaciones
            
            indice_actual += 1
        
        mostrar_encabezado("Resumen de Devolución a Proveedor", color=Fore.CYAN)
        print(f"  {'Equipo (Placa):'.ljust(35)} {equipo.placa}")
        for campo, valor in datos_devolucion.items():
            print(f"  {campo.ljust(35)}: {Fore.GREEN}{valor}{Style.RESET_ALL}")
        print(f"  {'Nuevo estado:'.ljust(35)} {Fore.GREEN}Pendiente Devolución a Proveedor{Style.RESET_ALL}")
        print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

        if not confirmar_con_placa(equipo.placa):
            return

        estado_anterior = equipo.estado
        equipo.estado = "Pendiente Devolución a Proveedor"
        equipo.fecha_devolucion_proveedor = datos_devolucion["Fecha de devolución a proveedor"]
        equipo.motivo_devolucion = datos_devolucion["Motivo de la Devolución"]
        equipo.observaciones = datos_devolucion["Observaciones adicionales"]
        
        db_manager.update_equipo(equipo)
        detalles = f"Motivo: {equipo.motivo_devolucion}. Fecha prog.: {equipo.fecha_devolucion_proveedor}. Obs: {equipo.observaciones}. Estado anterior: {estado_anterior}"
        registrar_movimiento_inventario(equipo.placa, "Registro Devolución Proveedor", detalles, usuario)
        print(Fore.GREEN + f"\n✅ Equipo {equipo.placa} registrado para devolución a proveedor.")
        print(Fore.GREEN + f"\n👨‍💼 Un administrador deberá continuar con la gestión.")

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
    finally:
        pausar_pantalla()

@requiere_permiso("eliminar_equipo")
def eliminar_equipo(usuario: str, equipo: Equipo) -> bool:
    try:
        print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para cancelar." + Style.RESET_ALL)
        
        num_movimientos = db_manager.count_movimientos_by_placa(equipo.placa)
        
        if num_movimientos > 1:
            print(Fore.RED + f"\n❌ No se puede eliminar el equipo {equipo.placa}.")
            print(Fore.YELLOW + f"   Motivo: El equipo tiene {num_movimientos} movimientos históricos registrados.")
            print(Fore.YELLOW + "   Un equipo solo puede ser eliminado si no ha tenido gestión (asignación, mantenimiento, etc.).")
            pausar_pantalla()
            return False
        
        while True:
            motivo = input(Fore.RED + "Motivo de la eliminación (obligatorio): " + Style.RESET_ALL).strip()
            if motivo:
                break
            print(Fore.RED + "El motivo no puede estar vacío.")

        print(Fore.RED + f"\n⚠️ ¿Seguro de eliminar el equipo {equipo.placa}? Esta acción es irreversible.")

        if not confirmar_con_placa(equipo.placa):
            return False

        db_manager.delete_equipo(equipo.placa)
        registrar_movimiento_inventario(equipo.placa, "Eliminación", f"Equipo eliminado. Motivo: {motivo}", usuario)
        print(Fore.GREEN + f"\n✅ Equipo {equipo.placa} eliminado.")
        pausar_pantalla()
        return True
            
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
        pausar_pantalla()
        return False

@requiere_permiso("gestionar_pendientes")
def menu_gestionar_pendientes(usuario: str):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        equipos = db_manager.get_all_equipos()
        mantenimientos_pendientes = len([e for e in equipos if e.get('estado') == "En mantenimiento"])
        devoluciones_pendientes = len([e for e in equipos if e.get('estado') == "Pendiente Devolución a Proveedor"])
        renovaciones_pendientes = len([e for e in equipos if e.get('estado') == "Renovación"])

        def get_color_indicator(count):
            if count == 0: return Fore.GREEN
            elif count <= 2: return Fore.YELLOW
            return Fore.RED

        color_mantenimiento = get_color_indicator(mantenimientos_pendientes)
        color_devoluciones = get_color_indicator(devoluciones_pendientes)
        color_renovaciones = get_color_indicator(renovaciones_pendientes)
        
        texto_menu_mantenimiento = f"Gestionar Equipos en Mantenimiento {color_mantenimiento}({mantenimientos_pendientes}){Style.RESET_ALL}"
        texto_menu_devoluciones = f"Gestionar Devoluciones a Proveedor {color_devoluciones}({devoluciones_pendientes}){Style.RESET_ALL}"
        texto_menu_renovaciones = f"Gestionar Renovaciones Pendientes {color_renovaciones}({renovaciones_pendientes}){Style.RESET_ALL}"
        
        opciones_disponibles = [
            texto_menu_mantenimiento, 
            texto_menu_devoluciones, 
            texto_menu_renovaciones, 
            "Volver"
        ]
        
        mostrar_menu(opciones_disponibles, titulo="Gestionar Mantenimientos, Devoluciones y Renovaciones")
        
        opcion_input = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
        
        opciones_map = {str(i+1): texto for i, texto in enumerate(opciones_disponibles)}
        opcion_texto = opciones_map.get(opcion_input)

        if opcion_texto and "Mantenimiento" in opcion_texto:
            gestionar_mantenimientos(usuario)
        elif opcion_texto and "Devoluciones" in opcion_texto:
            gestionar_devoluciones_proveedor(usuario)
        elif opcion_texto and "Renovaciones" in opcion_texto:
            gestionar_renovaciones(usuario)
        elif opcion_texto == "Volver":
            break
        else:
            print(Fore.RED + "Opción no válida.")
            pausar_pantalla()


# gestion_inventario.py

def _mostrar_formulario_mantenimiento_a_devolucion(equipo: Equipo, campos: List[str], datos: Dict[str, str], indice_actual: int):
    """
    Muestra un formulario interactivo para registrar la devolución a proveedor
    de un equipo que no fue reparable en mantenimiento.
    """
    mostrar_encabezado(f"Equipo no Reparable - Devolver a Proveedor", color=Fore.YELLOW)
    
    print(Fore.CYAN + "--- Información del Equipo ---")
    print(f"  {'Placa:'.ljust(25)} {equipo.placa}")
    if equipo.estado_anterior in ["Asignado", "En préstamo"]:
        print(Fore.YELLOW + f"  {'Importante:'.ljust(25)} El equipo estaba asignado a '{equipo.asignado_a}'.")
        print(Fore.YELLOW + f"  {''.ljust(27)} Esta acción lo retirará del usuario.")
    print(Style.RESET_ALL)
    
    print(Fore.CYAN + "💡 Complete los campos para registrar la devolución. Puede presionar Ctrl+C para cancelar." + Style.RESET_ALL)
    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)

    for i, campo in enumerate(campos):
        indicador = Fore.YELLOW + " -> " if i == indice_actual else "    "
        valor_mostrado = datos.get(campo, "")
        if valor_mostrado:
            valor_mostrado = f"{Fore.GREEN}{valor_mostrado}{Style.RESET_ALL}"
        print(f"{indicador}{campo.ljust(35)}: {valor_mostrado}")

    print(Fore.WHITE + "─" * 80 + Style.RESET_ALL)


def gestionar_mantenimientos(usuario: str):
    """Flujo mejorado para gestionar equipos en mantenimiento con formularios interactivos."""
    try:
        while True:
            equipos_pendientes = [Equipo(**e) for e in db_manager.get_all_equipos() if e.get('estado') == "En mantenimiento"]
            if not equipos_pendientes:
                print(Fore.YELLOW + "\nNo hay equipos en mantenimiento para gestionar.")
                pausar_pantalla()
                break

            mostrar_encabezado("Gestionar Equipos en Mantenimiento", color=Fore.BLUE)
            print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para regresar." + Style.RESET_ALL)
            print(Fore.WHITE + "\n--- Equipos en Mantenimiento ---" + Style.RESET_ALL)
            for i, equipo in enumerate(equipos_pendientes, 1):
                print(f"{Fore.YELLOW}{i}.{Style.RESET_ALL} Placa: {equipo.placa}, Tipo: {equipo.tipo}, Marca: {equipo.marca}")
            print(Fore.WHITE + "---------------------------------" + Style.RESET_ALL)

            seleccion = input(Fore.YELLOW + "\nSeleccione el equipo a gestionar: " + Style.RESET_ALL).strip()
            
            try:
                indice = int(seleccion) - 1
                if not (0 <= indice < len(equipos_pendientes)):
                    print(Fore.RED + "❌ Número no válido."); continue
                
                equipo_a_gestionar = equipos_pendientes[indice]
                
                ultimo_movimiento = db_manager.get_last_movimiento_by_placa(equipo_a_gestionar.placa)

                mostrar_encabezado(f"Gestionando Mantenimiento: Placa {equipo_a_gestionar.placa}", color=Fore.YELLOW)
                
                print(Fore.CYAN + "--- Detalles del Equipo ---")
                print(f"  {'Placa:'.ljust(25)} {equipo_a_gestionar.placa}")
                print(f"  {'Tipo:'.ljust(25)} {equipo_a_gestionar.tipo}")
                print(f"  {'Marca:'.ljust(25)} {equipo_a_gestionar.marca}")

                print(Fore.CYAN + "\n--- Detalles de la Solicitud de Mantenimiento ---")
                if ultimo_movimiento and ultimo_movimiento['accion'] == 'Mantenimiento':
                    fecha_evento = datetime.strptime(ultimo_movimiento['fecha'], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
                    print(f"  {'Fecha del Evento:'.ljust(25)} {fecha_evento}")
                    print(f"  {'Usuario que Registró:'.ljust(25)} {ultimo_movimiento['usuario']}")
                    print(f"  {'Detalles:'.ljust(25)} {ultimo_movimiento['detalles']}")
                
                print(Style.RESET_ALL + "-" * 80)

                mostrar_menu(["Mantenimiento completado", "Equipo no reparable (Devolver a proveedor)"], "Acciones Disponibles")
                accion = input(Fore.YELLOW + "Seleccione una acción: " + Style.RESET_ALL).strip()

                if accion == '1':
                    observacion = input(Fore.YELLOW + "Observaciones de la finalización del mantenimiento (obligatorio): " + Style.RESET_ALL).strip()
                    if not observacion:
                        print(Fore.RED + "La observación es obligatoria."); continue

                    nuevo_estado = equipo_a_gestionar.estado_anterior or "Disponible"
                    if not confirmar_con_placa(equipo_a_gestionar.placa): continue

                    equipo_a_gestionar.estado = nuevo_estado
                    equipo_a_gestionar.estado_anterior = None
                    db_manager.update_equipo(equipo_a_gestionar)
                    registrar_movimiento_inventario(equipo_a_gestionar.placa, "Mantenimiento Completado", f"Estado restaurado a '{nuevo_estado}'. Obs: {observacion}", usuario)
                    print(Fore.GREEN + f"\n✅ Equipo {equipo_a_gestionar.placa} ahora está '{nuevo_estado}'.")

                elif accion == '2':
                    campos_devolucion = ["Observación del retiro (si aplica)", "Motivo de la Devolución", "Fecha de devolución a proveedor", "Observaciones para la devolución"]
                    datos_devolucion = {campo: "" for campo in campos_devolucion}
                    
                    if equipo_a_gestionar.estado_anterior not in ["Asignado", "En préstamo"]:
                        datos_devolucion["Observación del retiro (si aplica)"] = "N/A - Equipo no estaba asignado"
                        
                    indice_actual = 0
                    while indice_actual < len(campos_devolucion):
                        campo_actual = campos_devolucion[indice_actual]
                        _mostrar_formulario_mantenimiento_a_devolucion(equipo_a_gestionar, campos_devolucion, datos_devolucion, indice_actual)

                        if campo_actual == "Observación del retiro (si aplica)" and datos_devolucion[campo_actual]:
                            indice_actual += 1
                            continue

                        if campo_actual == "Observación del retiro (si aplica)":
                            obs_retiro = input(Fore.YELLOW + "Observaciones del retiro al usuario (obligatorio): " + Style.RESET_ALL).strip()
                            if not obs_retiro:
                                print(Fore.RED + "La observación del retiro es obligatoria."); pausar_pantalla(); continue
                            datos_devolucion[campo_actual] = obs_retiro
                        
                        elif campo_actual == "Motivo de la Devolución":
                            motivos = ["Por daño", "No reparable", "Costo de reparación elevado"]
                            motivo = seleccionar_parametro(None, "Motivo de la Devolución", lista_opciones=motivos)
                            if not motivo: continue
                            datos_devolucion[campo_actual] = motivo
                        
                        elif campo_actual == "Fecha de devolución a proveedor":
                            fecha_str = input(Fore.YELLOW + "Fecha de devolución (DD/MM/AAAA): " + Style.RESET_ALL).strip()
                            if not validar_formato_fecha(fecha_str):
                                print(Fore.RED + "Formato de fecha inválido."); pausar_pantalla(); continue
                            datos_devolucion[campo_actual] = fecha_str
                        
                        elif campo_actual == "Observaciones para la devolución":
                            obs_devolucion = input(Fore.YELLOW + "Observaciones para el proveedor (obligatorio): " + Style.RESET_ALL).strip()
                            if not obs_devolucion:
                                print(Fore.RED + "Las observaciones son obligatorias."); pausar_pantalla(); continue
                            datos_devolucion[campo_actual] = obs_devolucion
                        
                        indice_actual += 1
                    
                    if not confirmar_con_placa(equipo_a_gestionar.placa): continue

                    # Actualizar y registrar
                    if datos_devolucion["Observación del retiro (si aplica)"] != "N/A - Equipo no estaba asignado":
                        registrar_movimiento_inventario(equipo_a_gestionar.placa, "Devolución a Inventario", f"Retirado de {equipo_a_gestionar.asignado_a}. Motivo: {datos_devolucion['Observación del retiro (si aplica)']}", usuario)

                    equipo_a_gestionar.estado = "Pendiente Devolución a Proveedor"
                    equipo_a_gestionar.estado_anterior = "En mantenimiento"
                    equipo_a_gestionar.asignado_a = None
                    equipo_a_gestionar.email_asignado = None
                    equipo_a_gestionar.fecha_devolucion_prestamo = None
                    equipo_a_gestionar.fecha_devolucion_proveedor = datos_devolucion["Fecha de devolución a proveedor"]
                    equipo_a_gestionar.motivo_devolucion = datos_devolucion["Motivo de la Devolución"]
                    equipo_a_gestionar.observaciones = datos_devolucion["Observaciones para la devolución"]
                    db_manager.update_equipo(equipo_a_gestionar)

                    detalles_log = f"Motivo: {datos_devolucion['Motivo de la Devolución']}. Fecha prog.: {datos_devolucion['Fecha de devolución a proveedor']}. Obs: {datos_devolucion['Observaciones para la devolución']}. Proceso iniciado desde Mantenimiento."
                    registrar_movimiento_inventario(equipo_a_gestionar.placa, "Registro Devolución Proveedor", detalles_log, usuario)
                    print(Fore.GREEN + "\n✅ ¡Operación completada! El equipo ha sido retirado y marcado para devolución.")
                else: 
                    print(Fore.RED + "❌ Acción no válida.")

            except (ValueError, IndexError):
                print(Fore.RED + "❌ Entrada inválida. Ingrese un número.")
            pausar_pantalla()
            
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Regresando al menú anterior.")
        pausar_pantalla()

def gestionar_devoluciones_proveedor(usuario: str):
    """Flujo mejorado para confirmar o rechazar devoluciones a proveedor."""
    mostrar_encabezado("Gestionar Devoluciones a Proveedor", color=Fore.BLUE)
    try:
        while True:
            equipos_pendientes = [Equipo(**e) for e in db_manager.get_all_equipos() if e.get('estado') == "Pendiente Devolución a Proveedor"]
            if not equipos_pendientes:
                print(Fore.YELLOW + "\nNo hay devoluciones pendientes para gestionar.")
                pausar_pantalla()
                break

            os.system('cls' if os.name == 'nt' else 'clear')
            mostrar_encabezado("Gestionar Devoluciones a Proveedor", color=Fore.BLUE)
            print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para regresar." + Style.RESET_ALL)
            print(Fore.WHITE + "\n--- Devoluciones Pendientes ---" + Style.RESET_ALL)
            for i, equipo in enumerate(equipos_pendientes, 1):
                print(f"{Fore.YELLOW}{i}.{Style.RESET_ALL} Placa: {equipo.placa}, Fecha Prog.: {equipo.fecha_devolucion_proveedor}, Motivo: {equipo.motivo_devolucion}")
            print(Fore.WHITE + "---------------------------------" + Style.RESET_ALL)

            seleccion = input(Fore.YELLOW + "Seleccione el equipo a gestionar: " + Style.RESET_ALL).strip()
            
            try:
                indice = int(seleccion) - 1
                if not (0 <= indice < len(equipos_pendientes)):
                    print(Fore.RED + "❌ Número no válido."); continue
                
                equipo_a_gestionar = equipos_pendientes[indice]

                ultimo_movimiento = db_manager.get_last_movimiento_by_placa(equipo_a_gestionar.placa)

                os.system('cls' if os.name == 'nt' else 'clear')
                mostrar_encabezado(f"Gestionando Devolución: Placa {equipo_a_gestionar.placa}", color=Fore.YELLOW)
                
                print(Fore.CYAN + "--- Detalles del Equipo ---")
                print(f"  {'Placa:'.ljust(25)} {equipo_a_gestionar.placa}")
                print(f"  {'Tipo:'.ljust(25)} {equipo_a_gestionar.tipo}")
                print(f"  {'Marca:'.ljust(25)} {equipo_a_gestionar.marca}")
                print(f"  {'Modelo:'.ljust(25)} {equipo_a_gestionar.modelo}")
                print(f"  {'Serial:'.ljust(25)} {equipo_a_gestionar.serial}")

                print(Fore.CYAN + "\n--- Detalles de la Solicitud de Devolución ---")
                
                if equipo_a_gestionar.motivo_devolucion == "Renovación":
                     print(Fore.YELLOW + "Este equipo está siendo devuelto como parte de un proceso de renovación.")
                     print(f"  Equipo de reemplazo: {equipo_a_gestionar.renovacion_placa_asociada}")
                
                if ultimo_movimiento:
                    fecha_evento = datetime.strptime(ultimo_movimiento['fecha'], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
                    print(f"  {'Fecha del Evento:'.ljust(25)} {fecha_evento}")
                    print(f"  {'Usuario que Registró:'.ljust(25)} {ultimo_movimiento['usuario']}")
                    print(f"  {'Motivo:'.ljust(25)} {equipo_a_gestionar.motivo_devolucion}")
                    print(f"  {'Fecha Programada:'.ljust(25)} {equipo_a_gestionar.fecha_devolucion_proveedor}")
                    print(f"  {'Observaciones:'.ljust(25)} {equipo_a_gestionar.observaciones}")
                else:
                    print(Fore.YELLOW + "No se encontraron detalles específicos del registro de devolución.")

                print(Style.RESET_ALL + "-" * 50)

                mostrar_menu(["Confirmar Devolución", "Rechazar Devolución", "Cancelar"], "Acciones Disponibles")
                accion = input(Fore.YELLOW + "Seleccione una acción: " + Style.RESET_ALL).strip()

                if accion == '1': # Confirmar Devolución
                    while True:
                        observacion = input(Fore.YELLOW + "Observaciones de la confirmación (ej: nro. de guía): " + Style.RESET_ALL).strip()
                        if observacion: break
                        print(Fore.RED + "La observación es obligatoria.")
                    
                    if not confirmar_con_placa(equipo_a_gestionar.placa): continue

                    equipo_a_gestionar.estado = "Devuelto a Proveedor"
                    equipo_a_gestionar.observaciones = observacion
                    equipo_a_gestionar.asignado_a = None
                    equipo_a_gestionar.email_asignado = None
                    db_manager.update_equipo(equipo_a_gestionar)
                    registrar_movimiento_inventario(equipo_a_gestionar.placa, "Devolución a Proveedor Completada", f"Devolución confirmada. Obs: {observacion}", usuario)
                    print(Fore.GREEN + f"\n✅ Equipo {equipo_a_gestionar.placa} marcado como 'Devuelto a Proveedor'.")

                elif accion == '2': # Rechazar Devolución
                    while True:
                        observacion = input(Fore.YELLOW + "Motivo del rechazo de la devolución: " + Style.RESET_ALL).strip()
                        if observacion: break
                        print(Fore.RED + "El motivo del rechazo es obligatorio.")
                    
                    if not confirmar_con_placa(equipo_a_gestionar.placa): continue
                    
                    equipo_a_gestionar.estado = "Disponible"
                    equipo_a_gestionar.estado_anterior = "Pendiente Devolución a Proveedor"
                    equipo_a_gestionar.observaciones = observacion
                    db_manager.update_equipo(equipo_a_gestionar)
                    registrar_movimiento_inventario(equipo_a_gestionar.placa, "Rechazo Devolución Proveedor", f"Devolución rechazada. Motivo: {observacion}", usuario)
                    print(Fore.GREEN + f"\n✅ Devolución rechazada. Equipo {equipo_a_gestionar.placa} vuelve a estar 'Disponible'.")

                elif accion == '3': # Cancelar
                    print(Fore.YELLOW + "Operación cancelada.")
                
                else:
                    print(Fore.RED + "❌ Acción no válida.")

            except ValueError:
                print(Fore.RED + "❌ Entrada inválida. Ingrese un número.")
            pausar_pantalla()

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Regresando al menú anterior.")
        pausar_pantalla()
        
# gestion_inventario.py
@requiere_permiso("gestionar_pendientes")
def gestionar_renovaciones(usuario: str):
    """Flujo para que un administrador apruebe o rechace renovaciones."""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        mostrar_encabezado("Gestionar Renovaciones Pendientes", color=Fore.BLUE)

        # Se muestra solo un registro por renovación (el equipo a devolver)
        equipos_pendientes = [Equipo(**e) for e in db_manager.get_all_equipos() if e.get('estado') == "Renovación" and e.get('fecha_entrega_renovacion')]
        if not equipos_pendientes:
            print(Fore.YELLOW + "\nNo hay renovaciones pendientes para gestionar.")
            pausar_pantalla()
            return

        print(Fore.CYAN + "💡 Puede presionar Ctrl+C para regresar." + Style.RESET_ALL)
        print(Fore.WHITE + "\n--- Renovaciones Pendientes de Aprobación ---" + Style.RESET_ALL)
        for i, equipo in enumerate(equipos_pendientes, 1):
            print(f"{Fore.YELLOW}{i}.{Style.RESET_ALL} Placa: {equipo.placa}, Usuario: {equipo.asignado_a}, Fecha Máx. Entrega: {equipo.fecha_entrega_renovacion}")
        print(Fore.WHITE + "-------------------------------------------" + Style.RESET_ALL)

        try:
            seleccion = input(Fore.YELLOW + "\nSeleccione el equipo a gestionar: " + Style.RESET_ALL).strip()
            if not seleccion: continue
            
            indice = int(seleccion) - 1
            if not (0 <= indice < len(equipos_pendientes)):
                print(Fore.RED + "❌ Número no válido."); continue
            
            equipo_actual = equipos_pendientes[indice]
            equipo_nuevo = Equipo(**db_manager.get_equipo_by_placa(equipo_actual.renovacion_placa_asociada))
            log_solicitud = db_manager.get_last_log_by_action(equipo_actual.placa, "Inicio Renovación")

            os.system('cls' if os.name == 'nt' else 'clear')
            mostrar_encabezado(f"Aprobando Renovación: Placa {equipo_actual.placa}", color=Fore.YELLOW)
            print(Fore.YELLOW + "Apruebe esta acción una vez se haya concretado la transacción con el usuario.")
            
            print(Fore.CYAN + "\n--- Detalles del Equipo Actual ---")
            print(f"  Placa: {equipo_actual.placa} ({equipo_actual.modelo})")
            print(f"  Registrado: {equipo_actual.fecha_registro} ({calcular_antiguedad(equipo_actual.fecha_registro)})")
            print(Fore.RED + f"  Fecha máxima para entregar equipo: {equipo_actual.fecha_entrega_renovacion}")

            print(Fore.CYAN + "\n--- Detalles del Equipo Nuevo ---")
            print(f"  Placa: {equipo_nuevo.placa} ({equipo_nuevo.modelo})")
            # MODIFICADO: Se elimina el cálculo de antigüedad para el equipo nuevo
            print(f"  Registrado: {equipo_nuevo.fecha_registro}")

            print(Fore.CYAN + "\n--- Datos del Usuario Involucrado ---")
            print(f"  Nombre: {equipo_actual.asignado_a}")
            print(f"  Email:  {equipo_actual.email_asignado}")

            if log_solicitud:
                print(Fore.CYAN + "\n--- Información de la Solicitud ---")
                print(f"  Solicitado por: {log_solicitud['usuario']}")
                print(f"  Observaciones: {log_solicitud['detalles']}")
            
            mostrar_menu(["Aprobar Renovación", "Rechazar Renovación", "Volver"], "Acciones Disponibles")
            accion = input(Fore.YELLOW + "Seleccione una acción: " + Style.RESET_ALL).strip()

            if accion == '1': # Aprobar
                fecha_max_entrega_actualizada = input(Fore.YELLOW + f"Modificar fecha máx. de entrega ({equipo_actual.fecha_entrega_renovacion}) o presione Enter para mantener: " + Style.RESET_ALL).strip()
                if fecha_max_entrega_actualizada and not validar_formato_fecha(fecha_max_entrega_actualizada):
                    print(Fore.RED + "Formato de fecha inválido."); continue
                if not fecha_max_entrega_actualizada:
                    fecha_max_entrega_actualizada = equipo_actual.fecha_entrega_renovacion

                obs = input(Fore.YELLOW + "Observaciones de la aprobación (opcional): " + Style.RESET_ALL).strip() or "Aprobado por administrador."
                if not confirmar_con_placa(equipo_actual.placa): continue
                
                # Guardar datos del usuario ANTES de desvincular
                usuario_asignado = equipo_actual.asignado_a
                email_usuario = equipo_actual.email_asignado

                # 1. Desvincular equipo actual y enviarlo a proveedor
                equipo_actual.estado = "Pendiente Devolución a Proveedor"
                equipo_actual.motivo_devolucion = "Renovación"
                equipo_actual.fecha_devolucion_proveedor = fecha_max_entrega_actualizada
                equipo_actual.observaciones = f"Renovación Aprobada. {obs}"
                equipo_actual.asignado_a = None
                equipo_actual.email_asignado = None
                db_manager.update_equipo(equipo_actual)
                registrar_movimiento_inventario(equipo_actual.placa, "Renovación Aprobada", f"Equipo desvinculado y listo para devolver. Obs: {obs}", usuario)

                # 2. Asignar equipo nuevo
                equipo_nuevo.estado = "Asignado"
                equipo_nuevo.asignado_a = usuario_asignado
                equipo_nuevo.email_asignado = email_usuario
                db_manager.update_equipo(equipo_nuevo)
                registrar_movimiento_inventario(equipo_nuevo.placa, "Asignación por Renovación Aprobada", f"Asignado a {usuario_asignado} como reemplazo de {equipo_actual.placa}", usuario)

                print(Fore.GREEN + f"\n✅ Renovación para {equipo_actual.placa} aprobada.")

            elif accion == '2': # Rechazar
                obs = input(Fore.YELLOW + "Motivo del rechazo (obligatorio): " + Style.RESET_ALL).strip()
                if not obs:
                    print(Fore.RED + "El motivo es obligatorio."); continue
                if not confirmar_con_placa(equipo_actual.placa): continue
                
                # Revertir equipo nuevo a Disponible
                equipo_nuevo.estado = "Disponible"
                equipo_nuevo.renovacion_placa_asociada = None
                db_manager.update_equipo(equipo_nuevo)
                registrar_movimiento_inventario(equipo_nuevo.placa, "Renovación Rechazada", f"Vuelve a inventario. Motivo: {obs}", usuario)

                # Revertir equipo actual a Asignado
                equipo_actual.estado = "Asignado"
                equipo_actual.renovacion_placa_asociada = None
                equipo_actual.fecha_entrega_renovacion = None
                db_manager.update_equipo(equipo_actual)
                registrar_movimiento_inventario(equipo_actual.placa, "Renovación Rechazada", f"Vuelve a ser 'Asignado'. Motivo: {obs}", usuario)
                print(Fore.GREEN + "\n✅ Renovación rechazada. Los estados de los equipos han sido revertidos.")

            elif accion == '3':
                continue
            
            else:
                print(Fore.RED + "❌ Acción no válida.")

        except (ValueError, IndexError):
            print(Fore.RED + "❌ Entrada inválida.")
        finally:
            pausar_pantalla()
            
            
            
def _mostrar_resultados_busqueda(usuario: str, resultados: List[Dict]):
    """Muestra los resultados de una búsqueda de forma paginada."""
    if not resultados:
        print(Fore.YELLOW + "\nNo se encontraron equipos que coincidan con los criterios de búsqueda.")
        pausar_pantalla()
        return

    page = 1
    page_size = 15
    total_pages = (len(resultados) + page_size - 1) // page_size

    while True:
        mostrar_encabezado("Resultados de la Búsqueda")
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        pagina_resultados = resultados[start_index:end_index]

        print(f"{Fore.CYAN}{'#':<4} {'PLACA':<15} {'TIPO':<20} {'ESTADO':<25} {'ASIGNADO A'}{Style.RESET_ALL}")
        print(Fore.CYAN + "="*90 + Style.RESET_ALL)

        for i, equipo in enumerate(pagina_resultados, start=start_index + 1):
            estado_color = Fore.WHITE
            if equipo['estado'] == "Disponible": estado_color = Fore.GREEN
            elif equipo['estado'] in ["Asignado", "En préstamo"]: estado_color = Fore.YELLOW
            else: estado_color = Fore.MAGENTA

            asignado_a = equipo.get('asignado_a') or 'N/A'
            print(f"{i:<4} {equipo['placa']:<15} {equipo['tipo']:<20} {estado_color}{equipo['estado']:<25}{Style.RESET_ALL} {asignado_a}")
        
        print("\n" + Fore.WHITE + f"Página {page} de {total_pages} ({len(resultados)} resultados totales)" + Style.RESET_ALL)
        
        prompt = (f"{Fore.CYAN}Presione (s) siguiente, (a) anterior, (g) para gestionar un equipo, (x) para volver: {Style.RESET_ALL}")
        opcion = input(prompt).strip().lower()

        if opcion == 's' and page < total_pages:
            page += 1
        elif opcion == 'a' and page > 1:
            page -= 1
        elif opcion == 'g':
            try:
                num_equipo = int(input(Fore.YELLOW + "Ingrese el número (#) del equipo que desea gestionar: " + Style.RESET_ALL))
                if 1 <= num_equipo <= len(resultados):
                    equipo_seleccionado = Equipo(**resultados[num_equipo - 1])
                    menu_gestion_especifica(usuario, equipo_seleccionado)
                else:
                    print(Fore.RED + "Número fuera de rango.")
                    pausar_pantalla()
            except ValueError:
                print(Fore.RED + "Entrada no válida. Debe ser un número.")
                pausar_pantalla()
        elif opcion == 'x':
            break


@requiere_permiso("ver_inventario")
def menu_busqueda_avanzada(usuario: str):
    """Menú para realizar búsquedas avanzadas de equipos."""
    while True:
        opciones = [
            "Buscar por Placa",
            "Buscar por Estado",
            "Buscar por Persona Asignada",
            "Buscar por Tipo de Equipo",
            "Buscar por Marca",
            "Volver al Menú de Gestión"
        ]
        mostrar_menu(opciones, titulo="Búsqueda Avanzada de Equipos")
        
        opcion = input(Fore.YELLOW + "Seleccione un criterio de búsqueda (o 'x' para volver): " + Style.RESET_ALL).strip()

        if opcion.lower() == 'x' or opcion == '6':
            break
        
        criterios_map = {
            '1': ('placa', 'la placa'),
            '2': ('estado', 'el estado'),
            '3': ('asignado_a', 'la persona asignada'),
            '4': ('tipo', 'el tipo de equipo'),
            '5': ('marca', 'la marca')
        }

        if opcion in criterios_map:
            campo_db, nombre_campo = criterios_map[opcion]
            valor_busqueda = input(Fore.YELLOW + f"Ingrese {nombre_campo} a buscar: " + Style.RESET_ALL).strip()
            
            if valor_busqueda:
                filtros = {campo_db: valor_busqueda}
                resultados = db_manager.buscar_equipos(filtros)
                _mostrar_resultados_busqueda(usuario, resultados)
            else:
                print(Fore.RED + "El término de búsqueda no puede estar vacío.")
                pausar_pantalla()
        else:
            print(Fore.RED + "Opción no válida.")
            pausar_pantalla()            