# gestion_inventario.py
import os
import re
import webbrowser
from datetime import datetime
from typing import Optional
import tempfile

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from colorama import Fore, Style

from database import db_manager, Equipo, registrar_movimiento
from ui import mostrar_encabezado, mostrar_menu, pausar_pantalla
from gestion_acceso import requiere_permiso

# --- FUNCIONES DE UTILIDAD Y VALIDACIÓN ---
def validar_placa_unica(placa: str) -> bool:
    return db_manager.get_equipo_by_placa(placa) is None

def validar_email(email: str) -> bool:
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

def validar_placa_formato(placa: str) -> bool:
    return len(placa) >= 4 and placa.isalnum()

def validar_formato_fecha(fecha_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y")
    except ValueError:
        return None

# --- FUNCIONES DE REPORTES (Excel) ---
@requiere_permiso("generar_reporte")
def generar_excel_inventario(usuario: str, filtro: Optional[str] = None, valor_filtro: Optional[str] = None) -> None:
    try:
        inventario = db_manager.get_all_equipos()

        if not inventario:
            print(Fore.YELLOW + "\nNo hay equipos para generar un reporte.")
            pausar_pantalla()
            return

        datos_a_exportar = inventario
        if filtro and valor_filtro:
            datos_a_exportar = [e for e in inventario if str(e.get(filtro, '')).lower() == valor_filtro.lower()]
        
        if not datos_a_exportar:
            print(Fore.YELLOW + f"\nNo se encontraron equipos con el filtro: {filtro} = '{valor_filtro}'.")
            pausar_pantalla()
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Inventario de Equipos"

        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        
        encabezados = ["PLACA", "TIPO", "MARCA", "MODELO", "SERIAL", "ESTADO", "ASIGNADO A", "EMAIL", "FECHA REGISTRO", "FECHA DEVOLUCIÓN (Préstamo)", "FECHA DEVOLUCIÓN (Proveedor)", "MOTIVO DEVOLUCIÓN", "OBSERVACIONES"]
        
        for col_num, encabezado in enumerate(encabezados, 1):
            col_letra = get_column_letter(col_num)
            celda = ws[f"{col_letra}1"]
            celda.value = encabezado
            celda.fill = header_fill
            celda.font = header_font
            celda.alignment = Alignment(horizontal='center')
            celda.border = border
            ws.column_dimensions[col_letra].width = 22

        colores_estado = {
            "Disponible": "C6EFCE", "Asignado": "FFEB9C", "En préstamo": "DDEBF7",
            "En mantenimiento": "FCE4D6", "Dado de baja": "FFC7CE",
            "Pendiente Devolución a Proveedor": "FFFFCC", "Devuelto a Proveedor": "CCE0B4"
        }

        for row_num, equipo in enumerate(datos_a_exportar, 2):
            ws.cell(row=row_num, column=1, value=equipo.get('placa', 'N/A')).border = border
            ws.cell(row=row_num, column=2, value=equipo.get('tipo', 'N/A')).border = border
            ws.cell(row=row_num, column=3, value=equipo.get('marca', 'N/A')).border = border
            ws.cell(row=row_num, column=4, value=equipo.get('modelo', 'N/A')).border = border
            ws.cell(row=row_num, column=5, value=equipo.get('serial', 'N/A')).border = border
            
            estado_celda = ws.cell(row=row_num, column=6, value=equipo.get('estado', 'N/A'))
            estado_celda.border = border
            color_hex = colores_estado.get(equipo.get('estado'))
            if color_hex:
                estado_celda.fill = PatternFill(start_color=color_hex, end_color=color_hex, fill_type="solid")

            ws.cell(row=row_num, column=7, value=equipo.get('asignado_a', '')).border = border
            ws.cell(row=row_num, column=8, value=equipo.get('email_asignado', '')).border = border
            ws.cell(row=row_num, column=9, value=equipo.get('fecha_registro', '')).border = border
            ws.cell(row=row_num, column=10, value=equipo.get('fecha_devolucion_prestamo', '')).border = border
            ws.cell(row=row_num, column=11, value=equipo.get('fecha_devolucion_proveedor', '')).border = border
            ws.cell(row=row_num, column=12, value=equipo.get('motivo_devolucion', '')).border = border
            ws.cell(row=row_num, column=13, value=equipo.get('observaciones', '')).border = border
        
        ws.freeze_panes = "A2"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            wb.save(tmp.name)
            ruta_temporal = tmp.name

        registrar_movimiento("SISTEMA", "Reporte Excel", f"Generado reporte de inventario con {len(datos_a_exportar)} equipos", usuario)
        print(Fore.GREEN + f"\n✅ Abriendo el reporte de inventario en Excel..." + Style.RESET_ALL)
        webbrowser.open(ruta_temporal)

    except Exception as e:
        print(Fore.RED + f"\n❌ Error al generar el reporte Excel: {str(e)}" + Style.RESET_ALL)
    finally:
        pausar_pantalla()

@requiere_permiso("generar_reporte")
def menu_reportes(usuario: str):
    while True:
        mostrar_menu([
            "Reporte completo",
            "Reporte por Estado (ej. Asignado, Disponible)",
            "Volver"
        ], titulo="Generar Reportes")
        opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
        if opcion == '1':
            generar_excel_inventario(usuario)
        elif opcion == '2':
            estado = input(Fore.YELLOW + "Ingrese el estado a filtrar: " + Style.RESET_ALL).strip().title()
            generar_excel_inventario(usuario, filtro='estado', valor_filtro=estado)
        elif opcion == '3':
            break
        else:
            print(Fore.RED + "Opción no válida.")

# --- FUNCIONES PRINCIPALES DE INVENTARIO ---
def seleccionar_parametro(tipo_parametro: str, nombre_amigable: str) -> Optional[str]:
    parametros_activos = [p['valor'] for p in db_manager.get_parametros_por_tipo(tipo_parametro, solo_activos=True)]
    
    while True:
        # --- CAMBIO DE COLOR ---
        print(Fore.GREEN + f"\nSeleccione un {nombre_amigable}:")
        for i, param in enumerate(parametros_activos, 1):
            print(f"{i}. {param}")
        
        # --- ESPACIO AÑADIDO ---
        print() 

        seleccion = input(Fore.YELLOW + "Opción: " + Style.RESET_ALL).strip()
        try:
            idx = int(seleccion) - 1
            if 0 <= idx < len(parametros_activos):
                return parametros_activos[idx]
            else:
                print(Fore.RED + "Selección fuera de rango.")
        except ValueError:
            print(Fore.RED + "Por favor, ingrese un número.")

@requiere_permiso("registrar_equipo")
def registrar_equipo(usuario: str):
    mostrar_encabezado("Registro de Nuevo Equipo", color=Fore.BLUE)
    
    tipos_existentes = db_manager.get_parametros_por_tipo('tipo_equipo', solo_activos=True)
    marcas_existentes = db_manager.get_parametros_por_tipo('marca_equipo', solo_activos=True)

    if not tipos_existentes or not marcas_existentes:
        print(Fore.RED + "❌ No se puede registrar un nuevo equipo.")
        if not tipos_existentes:
            print(Fore.YELLOW + "   - No hay 'Tipos de Equipo' activos configurados.")
        if not marcas_existentes:
            print(Fore.YELLOW + "   - No hay 'Marcas' activas configuradas.")
        print(Fore.CYAN + "Por favor, pida a un Administrador que configure estos parámetros en el módulo de 'Acceso y Sistema'.")
        pausar_pantalla()
        return

    try:
        print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para cancelar." + Style.RESET_ALL)
        while True:
            placa = input(Fore.YELLOW + "Placa del equipo: " + Style.RESET_ALL).strip().upper()
            if not validar_placa_formato(placa):
                print(Fore.RED + "⚠️ Formato de placa inválido (mín. 4 caracteres alfanuméricos).")
            elif not validar_placa_unica(placa):
                print(Fore.RED + "⚠️ Esta placa ya está registrada.")
            else:
                break
        
        tipo = seleccionar_parametro('tipo_equipo', 'Tipo de Equipo')
        marca = seleccionar_parametro('marca_equipo', 'Marca')
            
        modelo = input(Fore.YELLOW + "Modelo: " + Style.RESET_ALL).strip()
        serial = input(Fore.YELLOW + "Número de serie: " + Style.RESET_ALL).strip()
        observaciones = input(Fore.YELLOW + "Observaciones (opcional): " + Style.RESET_ALL).strip() or "Ninguna"

        if not all([placa, tipo, marca, modelo, serial]):
            print(Fore.RED + "\n❌ Error: Todos los campos son obligatorios excepto observaciones.")
            pausar_pantalla()
            return

        print("\n" + Fore.CYAN + "--- Resumen del Nuevo Equipo ---")
        print(f"  {'Placa:'.ljust(15)} {placa}")
        print(f"  {'Tipo:'.ljust(15)} {tipo}")
        print(f"  {'Marca:'.ljust(15)} {marca}")
        print(f"  {'Modelo:'.ljust(15)} {modelo}")
        print(f"  {'Serial:'.ljust(15)} {serial}")
        print(f"  {'Observaciones:'.ljust(15)} {observaciones}")
        print("--------------------------------" + Style.RESET_ALL)

        while True:
            confirmacion = input(Fore.YELLOW + f"\nPara confirmar, escriba la placa del equipo ({placa}): " + Style.RESET_ALL).strip().upper()
            if confirmacion == placa:
                nuevo_equipo = Equipo(placa=placa, tipo=tipo, marca=marca, modelo=modelo, serial=serial, observaciones=observaciones)
                db_manager.insert_equipo(nuevo_equipo)
                registrar_movimiento(placa, "Registro", f"Nuevo equipo registrado: {tipo} {marca} {modelo}", usuario)
                print(Fore.GREEN + f"\n✅ ¡Equipo con placa {placa} registrado exitosamente!")
                break
            else:
                print(Fore.RED + "La placa no coincide. Intente de nuevo.")

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación de registro cancelada.")
    finally:
        pausar_pantalla()

@requiere_permiso("gestionar_equipo")
def gestionar_equipos(usuario: str):
    mostrar_encabezado("Gestión de Equipos", color=Fore.BLUE)
    try:
        print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para regresar." + Style.RESET_ALL)
        while True:
            placa = input(Fore.YELLOW + "Ingrese la placa del equipo a gestionar: " + Style.RESET_ALL).strip().upper()
            
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

def menu_gestion_especifica(usuario: str, equipo: Equipo):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        mostrar_encabezado(f"Gestionando Equipo: {equipo.marca} {equipo.modelo} - PLACA: {equipo.placa}", color=Fore.GREEN)
        print(f"{Fore.CYAN}Estado actual:{Style.RESET_ALL} {equipo.estado}")
        if equipo.asignado_a: print(f"{Fore.CYAN}Asignado a:{Style.RESET_ALL} {equipo.asignado_a} ({equipo.email_asignado})")
        if equipo.fecha_devolucion_prestamo: print(f"{Fore.CYAN}Fecha devolución (Préstamo):{Style.RESET_ALL} {equipo.fecha_devolucion_prestamo}")
        print("-" * 80)

        opciones_gestion = [
            "Asignar/Prestar equipo", "Devolver equipo al inventario", "Registrar para mantenimiento",
            "Registrar para devolución a Proveedor", "Editar información del equipo", 
            "Eliminar equipo", "Volver al menú anterior"
        ]
        mostrar_menu(opciones_gestion, titulo=f"Opciones para {equipo.placa}")
        
        opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()

        opciones_validas = {
            "1": "asignar", "2": "devolver", "3": "mantenimiento",
            "4": "proveedor", "5": "editar", "6": "eliminar", "7": "volver"
        }
        accion = opciones_validas.get(opcion)

        if accion == "asignar": asignar_o_prestar_equipo(usuario, equipo)
        elif accion == "devolver": devolver_equipo(usuario, equipo)
        elif accion == "mantenimiento": registrar_mantenimiento(usuario, equipo)
        elif accion == "proveedor": registrar_devolucion_a_proveedor(usuario, equipo)
        elif accion == "editar": editar_equipo(usuario, equipo)
        elif accion == "eliminar":
            if eliminar_equipo(usuario, equipo): return 
        elif accion == "volver": break
        else:
            print(Fore.RED + "❌ Opción no válida. Por favor, intente de nuevo.")
            pausar_pantalla()
        
        equipo_data_actualizado = db_manager.get_equipo_by_placa(equipo.placa)
        if not equipo_data_actualizado: break
        equipo = Equipo(**equipo_data_actualizado)

@requiere_permiso("gestionar_equipo")
def asignar_o_prestar_equipo(usuario: str, equipo: Equipo):
    if equipo.estado != "Disponible":
        print(Fore.RED + f"❌ El equipo no está 'Disponible' (Estado actual: {equipo.estado}).")
        pausar_pantalla()
        return
    
    try:
        print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para cancelar." + Style.RESET_ALL)
        while True:
            tipo_asignacion_input = input(Fore.YELLOW + "Escriba 'A' para Asignación o 'P' para Préstamo: " + Style.RESET_ALL).strip().upper()
            if tipo_asignacion_input in ["A", "P"]:
                break
            print(Fore.RED + "Opción inválida. Intente de nuevo.")
        
        nombre_asignado = input(Fore.YELLOW + "Nombre de la persona: " + Style.RESET_ALL).strip()
        while True:
            email_asignado = input(Fore.YELLOW + "Email de la persona: " + Style.RESET_ALL).strip()
            if validar_email(email_asignado): break
            print(Fore.RED + "Email inválido. Intente de nuevo.")

        observacion_asignacion = input(Fore.YELLOW + "Observación de la asignación/préstamo: " + Style.RESET_ALL).strip() or "Sin observaciones"

        fecha_devolucion = None
        if tipo_asignacion_input == "P":
            tipo_movimiento = "Préstamo"
            while True:
                fecha_str = input(Fore.YELLOW + "Fecha de devolución (DD/MM/AAAA): " + Style.RESET_ALL).strip()
                if validar_formato_fecha(fecha_str):
                    fecha_devolucion = fecha_str
                    break
                print(Fore.RED + "Formato de fecha inválido. Intente de nuevo.")
        else:
            tipo_movimiento = "Asignación"

        print("\n" + Fore.CYAN + "--- Resumen de la Operación ---")
        print(f"  {'Acción:'.ljust(20)} {tipo_movimiento}")
        print(f"  {'Equipo (Placa):'.ljust(20)} {equipo.placa}")
        print(f"  {'Asignado a:'.ljust(20)} {nombre_asignado}")
        print(f"  {'Email:'.ljust(20)} {email_asignado}")
        if fecha_devolucion:
            print(f"  {'Fecha de Devolución:'.ljust(20)} {fecha_devolucion}")
        print(f"  {'Observación:'.ljust(20)} {observacion_asignacion}")
        print("--------------------------------" + Style.RESET_ALL)
        
        while True:
            confirmacion = input(Fore.YELLOW + f"\nPara confirmar, escriba la placa del equipo ({equipo.placa}): " + Style.RESET_ALL).strip().upper()
            if confirmacion == equipo.placa:
                equipo.estado = "En préstamo" if tipo_movimiento == "Préstamo" else "Asignado"
                detalles_movimiento = f"{tipo_movimiento} a {nombre_asignado}. Obs: {observacion_asignacion}"
                if fecha_devolucion:
                    detalles_movimiento += f". Devolución: {fecha_devolucion}"
                
                equipo.asignado_a = nombre_asignado
                equipo.email_asignado = email_asignado
                equipo.fecha_devolucion_prestamo = fecha_devolucion

                db_manager.update_equipo(equipo)
                registrar_movimiento(equipo.placa, "Asignación/Préstamo", detalles_movimiento, usuario)
                print(Fore.GREEN + f"\n✅ ¡Operación confirmada! Equipo {equipo.placa} ahora está '{equipo.estado}'.")
                break
            else:
                print(Fore.RED + "\nLa placa no coincide. Por favor, intente de nuevo.")

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
    finally:
        pausar_pantalla()

@requiere_permiso("gestionar_equipo")
def devolver_equipo(usuario: str, equipo: Equipo):
    if equipo.estado not in ["Asignado", "En préstamo"]:
        print(Fore.RED + "❌ El equipo no está asignado ni en préstamo.")
        pausar_pantalla()
        return

    try:
        print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para cancelar." + Style.RESET_ALL)
        while True:
            observacion_devolucion = input(Fore.YELLOW + "Motivo u observación de la devolución: " + Style.RESET_ALL).strip()
            if observacion_devolucion:
                break
            print(Fore.RED + "La observación es obligatoria para la devolución. Intente de nuevo.")
            
        print("\n" + Fore.CYAN + "--- Resumen de la Devolución ---")
        print(f"  {'Equipo (Placa):'.ljust(25)} {equipo.placa}")
        print(f"  {'Se retirará de:'.ljust(25)} {equipo.asignado_a or 'N/A'}")
        print(f"  {'Estado anterior:'.ljust(25)} {equipo.estado}")
        print(f"  {'Nuevo estado:'.ljust(25)} Disponible")
        print(f"  {'Observación de devolución:'.ljust(25)} {observacion_devolucion}")
        print("--------------------------------" + Style.RESET_ALL)

        while True:
            confirmacion = input(Fore.YELLOW + f"\nPara confirmar, escriba la placa del equipo ({equipo.placa}): " + Style.RESET_ALL).strip().upper()

            if confirmacion == equipo.placa:
                detalles_previos = f"Devuelto por {equipo.asignado_a or 'N/A'}. Motivo: {observacion_devolucion}"
                equipo.estado = "Disponible"
                equipo.asignado_a = None
                equipo.email_asignado = None
                equipo.fecha_devolucion_prestamo = None
                
                db_manager.update_equipo(equipo)
                registrar_movimiento(equipo.placa, "Devolución a Inventario", detalles_previos, usuario)
                print(Fore.GREEN + f"\n✅ ¡Devolución confirmada! Equipo {equipo.placa} ahora está 'Disponible'.")
                break
            else:
                print(Fore.RED + "\nLa placa no coincide. Por favor, intente de nuevo.")

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
    finally:
        pausar_pantalla()

@requiere_permiso("gestionar_equipo")
def editar_equipo(usuario: str, equipo: Equipo):
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        mostrar_encabezado(f"Editando Equipo: {equipo.placa}", color=Fore.BLUE)
        print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para cancelar." + Style.RESET_ALL)
        
        print(Fore.CYAN + "--- Información Actual del Equipo ---")
        print(f"  Tipo:          {equipo.tipo}")
        print(f"  Marca:         {equipo.marca}")
        print(f"  Modelo:        {equipo.modelo}")
        print(f"  Serial:        {equipo.serial}")
        print(f"  Observaciones: {equipo.observaciones or ''}")
        print("---------------------------------------" + Style.RESET_ALL)
        print("\nDeje el campo en blanco y presione Enter para mantener el valor actual.")

        tipo_nuevo = input(Fore.YELLOW + f"Tipo ({Fore.CYAN}{equipo.tipo}{Fore.YELLOW}): " + Style.RESET_ALL).strip() or equipo.tipo
        marca_nueva = input(Fore.YELLOW + f"Marca ({Fore.CYAN}{equipo.marca}{Fore.YELLOW}): " + Style.RESET_ALL).strip() or equipo.marca
        modelo_nuevo = input(Fore.YELLOW + f"Modelo ({Fore.CYAN}{equipo.modelo}{Fore.YELLOW}): " + Style.RESET_ALL).strip() or equipo.modelo
        serial_nuevo = input(Fore.YELLOW + f"Serie ({Fore.CYAN}{equipo.serial}{Fore.YELLOW}): " + Style.RESET_ALL).strip() or equipo.serial
        observaciones_nuevas = input(Fore.YELLOW + f"Observaciones ({Fore.CYAN}{equipo.observaciones or ''}{Fore.YELLOW}): " + Style.RESET_ALL).strip() or equipo.observaciones

        cambios = []
        if equipo.tipo != tipo_nuevo: cambios.append(f"Tipo: '{equipo.tipo}' -> '{tipo_nuevo}'")
        if equipo.marca != marca_nueva: cambios.append(f"Marca: '{equipo.marca}' -> '{marca_nueva}'")
        if equipo.modelo != modelo_nuevo: cambios.append(f"Modelo: '{equipo.modelo}' -> '{modelo_nuevo}'")
        if equipo.serial != serial_nuevo: cambios.append(f"Serial: '{equipo.serial}' -> '{serial_nuevo}'")
        if equipo.observaciones != observaciones_nuevas: cambios.append(f"Observaciones: '{equipo.observaciones or ''}' -> '{observaciones_nuevas}'")
        
        if not cambios:
            print(Fore.YELLOW + "\nNo se detectaron cambios.")
            pausar_pantalla()
            return

        print("\n" + Fore.CYAN + "--- Resumen de Cambios ---")
        for cambio in cambios:
            print(f"  - {cambio}")
        print("--------------------------" + Style.RESET_ALL)

        while True:
            confirmacion = input(Fore.YELLOW + f"\nPara confirmar los cambios, escriba la placa del equipo ({equipo.placa}): " + Style.RESET_ALL).strip().upper()
            if confirmacion == equipo.placa:
                equipo.tipo, equipo.marca, equipo.modelo, equipo.serial, equipo.observaciones = tipo_nuevo, marca_nueva, modelo_nuevo, serial_nuevo, observaciones_nuevas
                db_manager.update_equipo(equipo)
                registrar_movimiento(equipo.placa, "Edición", "; ".join(cambios), usuario)
                print(Fore.GREEN + f"\n✅ ¡Equipo {equipo.placa} actualizado exitosamente!")
                break
            else:
                print(Fore.RED + "La placa no coincide. Intente de nuevo.")

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación de edición cancelada.")
    finally:
        pausar_pantalla()
        
@requiere_permiso("gestionar_equipo")
def registrar_mantenimiento(usuario: str, equipo: Equipo):
    try:
        print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para cancelar." + Style.RESET_ALL)
        observaciones_mantenimiento = input(Fore.YELLOW + "Observaciones del mantenimiento: " + Style.RESET_ALL).strip()
        if not observaciones_mantenimiento:
            print(Fore.RED + "Las observaciones son obligatorias."); return
        
        estado_anterior = equipo.estado
        equipo.estado = "En mantenimiento"
        db_manager.update_equipo(equipo)
        registrar_movimiento(equipo.placa, "Mantenimiento", f"Observaciones: {observaciones_mantenimiento}. Estado anterior: {estado_anterior}", usuario)
        print(Fore.GREEN + f"\n✅ Mantenimiento registrado. Estado cambiado a 'En mantenimiento'.")
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
    finally:
        pausar_pantalla()

@requiere_permiso("devolver_a_proveedor")
def registrar_devolucion_a_proveedor(usuario: str, equipo: Equipo):
    try:
        print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para cancelar." + Style.RESET_ALL)
        while True:
            print("Motivo de la devolución:\n1. Por daño\n2. No se necesita más")
            motivo_opcion = input(Fore.YELLOW + "Seleccione el motivo: " + Style.RESET_ALL).strip()
            if motivo_opcion == '1':
                motivo = "Por daño"
                break
            elif motivo_opcion == '2':
                motivo = "No se necesita más"
                break
            else:
                print(Fore.RED + "Opción inválida.")

        while True:
            fecha_str = input(Fore.YELLOW + "Fecha de devolución a proveedor (DD/MM/AAAA): " + Style.RESET_ALL).strip()
            if validar_formato_fecha(fecha_str):
                fecha_devolucion = fecha_str
                break
            print(Fore.RED + "Formato de fecha inválido.")

        observaciones = input(Fore.YELLOW + "Observaciones adicionales: " + Style.RESET_ALL).strip()
        
        estado_anterior = equipo.estado
        equipo.estado = "Pendiente Devolución a Proveedor"
        equipo.fecha_devolucion_proveedor = fecha_devolucion
        equipo.motivo_devolucion = motivo
        equipo.observaciones = observaciones
        equipo.asignado_a = None
        equipo.email_asignado = None
        equipo.fecha_devolucion_prestamo = None

        db_manager.update_equipo(equipo)
        detalles = f"Motivo: {motivo}. Fecha prog.: {fecha_devolucion}. Obs: {observaciones}. Estado anterior: {estado_anterior}"
        registrar_movimiento(equipo.placa, "Registro Devolución Proveedor", detalles, usuario)
        print(Fore.GREEN + f"\n✅ Equipo {equipo.placa} registrado para devolución a proveedor.")
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
    finally:
        pausar_pantalla()

@requiere_permiso("eliminar_equipo")
def eliminar_equipo(usuario: str, equipo: Equipo) -> bool:
    try:
        print(Fore.CYAN + "💡 Puede presionar Ctrl+C en cualquier momento para cancelar." + Style.RESET_ALL)
        while True:
            confirmacion = input(Fore.RED + f"⚠️ ¿Seguro de eliminar el equipo {equipo.placa}? Esta acción es irreversible. (Escriba la placa para confirmar): " + Style.RESET_ALL).strip().upper()
            if confirmacion == equipo.placa:
                db_manager.delete_equipo(equipo.placa)
                registrar_movimiento(equipo.placa, "Eliminación", f"Equipo eliminado: {equipo.tipo} {equipo.marca}", usuario)
                print(Fore.GREEN + f"\n✅ Equipo {equipo.placa} eliminado.")
                pausar_pantalla()
                return True
            else:
                print(Fore.RED + "La placa no coincide. Eliminación cancelada.")
                pausar_pantalla()
                return False
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
        pausar_pantalla()
        return False

@requiere_permiso("gestionar_pendientes")
def menu_gestionar_pendientes(usuario: str):
    while True:
        mostrar_menu([
            "Gestionar Equipos en Mantenimiento",
            "Gestionar Devoluciones a Proveedor Pendientes",
            "Volver"
        ], titulo="Gestionar Mantenimientos y Devoluciones")
        opcion = input(Fore.YELLOW + "Seleccione una opción: " + Style.RESET_ALL).strip()
        if opcion == '1':
            gestionar_mantenimientos(usuario)
        elif opcion == '2':
            gestionar_devoluciones_proveedor(usuario)
        elif opcion == '3':
            break
        else:
            print(Fore.RED + "Opción no válida.")

def gestionar_mantenimientos(usuario: str):
    mostrar_encabezado("Gestionar Equipos en Mantenimiento", color=Fore.BLUE)
    try:
        while True:
            equipos_pendientes = [Equipo(**e) for e in db_manager.get_all_equipos() if e.get('estado') == "En mantenimiento"]
            if not equipos_pendientes:
                print(Fore.YELLOW + "\nNo hay equipos en mantenimiento para gestionar.")
                break

            os.system('cls' if os.name == 'nt' else 'clear')
            mostrar_encabezado("Gestionar Equipos en Mantenimiento", color=Fore.BLUE)
            print(Fore.WHITE + "\n--- Equipos en Mantenimiento ---" + Style.RESET_ALL)
            for i, equipo in enumerate(equipos_pendientes, 1):
                print(f"{Fore.YELLOW}{i}.{Style.RESET_ALL} Placa: {equipo.placa}, Tipo: {equipo.tipo}, Marca: {equipo.marca}")
            print(Fore.WHITE + "---------------------------------" + Style.RESET_ALL)

            seleccion = input(Fore.YELLOW + "Seleccione el equipo a gestionar (o '0' para salir): " + Style.RESET_ALL).strip()
            if seleccion == '0': break
            
            try:
                indice = int(seleccion) - 1
                if not (0 <= indice < len(equipos_pendientes)):
                    print(Fore.RED + "❌ Número no válido."); continue
                
                equipo_a_gestionar = equipos_pendientes[indice]
                print(f"\nGestionando: {equipo_a_gestionar.placa}")
                print("1. Mantenimiento completado (Pasa a 'Disponible')")
                print("2. Equipo no reparable (Registrar para devolución a proveedor)")
                print("0. Cancelar")
                accion = input(Fore.YELLOW + "Seleccione una acción: " + Style.RESET_ALL).strip()

                if accion == '1':
                    estado_anterior = equipo_a_gestionar.estado
                    equipo_a_gestionar.estado = "Disponible"
                    db_manager.update_equipo(equipo_a_gestionar)
                    registrar_movimiento(equipo_a_gestionar.placa, "Mantenimiento Completado", f"Estado cambiado de '{estado_anterior}' a 'Disponible'", usuario)
                    print(Fore.GREEN + f"\n✅ Equipo {equipo_a_gestionar.placa} ahora está 'Disponible'.")
                elif accion == '2':
                    print(Fore.CYAN + "\nRedirigiendo...")
                    pausar_pantalla()
                    registrar_devolucion_a_proveedor(usuario, equipo_a_gestionar)
                elif accion == '0': continue
                else: print(Fore.RED + "❌ Acción no válida.")
            except ValueError:
                print(Fore.RED + "❌ Entrada inválida. Ingrese un número.")
            pausar_pantalla()
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
    finally:
        pausar_pantalla()

def gestionar_devoluciones_proveedor(usuario: str):
    mostrar_encabezado("Gestionar Devoluciones a Proveedor", color=Fore.BLUE)
    try:
        while True:
            equipos_pendientes = [Equipo(**e) for e in db_manager.get_all_equipos() if e.get('estado') == "Pendiente Devolución a Proveedor"]
            if not equipos_pendientes:
                print(Fore.YELLOW + "\nNo hay devoluciones pendientes para gestionar.")
                break

            os.system('cls' if os.name == 'nt' else 'clear')
            mostrar_encabezado("Gestionar Devoluciones a Proveedor", color=Fore.BLUE)
            print(Fore.WHITE + "\n--- Devoluciones Pendientes ---" + Style.RESET_ALL)
            for i, equipo in enumerate(equipos_pendientes, 1):
                print(f"{Fore.YELLOW}{i}.{Style.RESET_ALL} Placa: {equipo.placa}, Fecha Prog.: {equipo.fecha_devolucion_proveedor}, Motivo: {equipo.motivo_devolucion}")
            print(Fore.WHITE + "---------------------------------" + Style.RESET_ALL)

            seleccion = input(Fore.YELLOW + "Seleccione el equipo a confirmar como devuelto (o '0' para salir): " + Style.RESET_ALL).strip()
            if seleccion == '0': break
            
            try:
                indice = int(seleccion) - 1
                if not (0 <= indice < len(equipos_pendientes)):
                    print(Fore.RED + "❌ Número no válido."); continue
                
                equipo_a_gestionar = equipos_pendientes[indice]
                confirm = input(Fore.YELLOW + f"¿Confirmar que el equipo {equipo_a_gestionar.placa} ha sido devuelto al proveedor? (S/N): " + Style.RESET_ALL).strip().upper()

                if confirm == 'S':
                    estado_anterior = equipo_a_gestionar.estado
                    equipo_a_gestionar.estado = "Devuelto a Proveedor"
                    db_manager.update_equipo(equipo_a_gestionar)
                    registrar_movimiento(equipo_a_gestionar.placa, "Devolución a Proveedor Completada", f"Estado cambiado de '{estado_anterior}' a 'Devuelto a Proveedor'", usuario)
                    print(Fore.GREEN + f"\n✅ Equipo {equipo_a_gestionar.placa} marcado como 'Devuelto a Proveedor'.")
                else:
                    print(Fore.YELLOW + "Operación cancelada.")
            except ValueError:
                print(Fore.RED + "❌ Entrada inválida. Ingrese un número.")
            pausar_pantalla()
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n🚫 Operación cancelada.")
    finally:
        pausar_pantalla()

@requiere_permiso("ver_inventario")
def ver_inventario_consola():
    mostrar_encabezado("Inventario Actual de Equipos")
    inventario = db_manager.get_all_equipos()
    if not inventario:
        print(Fore.YELLOW + "\nEl inventario está vacío.")
    else:
        print(f"{Fore.CYAN}{'PLACA':<12} {'TIPO':<15} {'MARCA':<15} {'MODELO':<20} {'ESTADO':<30} {'ASIGNADO A':<20}{Style.RESET_ALL}")
        print(Fore.CYAN + "="*112 + Style.RESET_ALL)
        for equipo in inventario:
            estado_color = Fore.WHITE
            if equipo['estado'] == "Disponible": estado_color = Fore.GREEN
            elif equipo['estado'] in ["Asignado", "En préstamo"]: estado_color = Fore.YELLOW
            elif equipo['estado'] == "En mantenimiento": estado_color = Fore.MAGENTA
            elif equipo['estado'] == "Pendiente Devolución a Proveedor": estado_color = Fore.LIGHTYELLOW_EX
            elif equipo['estado'] == "Devuelto a Proveedor": estado_color = Fore.LIGHTBLACK_EX
            elif equipo['estado'] == "Dado de baja": estado_color = Fore.RED
            asignado_a = equipo.get('asignado_a') or 'N/A'
            print(f"{equipo['placa']:<12} {equipo['tipo']:<15} {equipo['marca']:<15} {equipo['modelo']:<20} {estado_color}{equipo['estado']:<30}{Style.RESET_ALL} {asignado_a:<20}")
    pausar_pantalla()