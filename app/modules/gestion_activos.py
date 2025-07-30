# app/modules/gestion_activos.py
import textwrap
from colorama import Fore, Style
from datetime import datetime
from .. import ui
from ..database import DatabaseManager
from ..validators import (validar_campo_general, validar_placa_formato, 
                          validar_serial, validar_capacidad_almacenamiento, 
                          formatear_observacion)
from .configuracion import menu_configuracion_sistema

# --- FUNCIONES AUXILIARES PARA EL FORMULARIO ---

def _seleccionar_parametro(db: DatabaseManager, tipo: str, titulo: str, lista_opciones: list = None, solo_activos=True):
    """
    Muestra una lista de opciones para que el usuario elija.
    Siempre enumera a partir de 1 y añade un espacio antes de la opción.
    """
    items = []
    if lista_opciones:
        items = lista_opciones
    elif tipo == 'proveedor':
        items = [p['nombre'] for p in db.get_all_proveedores(solo_activos=solo_activos)]
    else: # tipo_equipo, marca_equipo
        items = [p['valor'] for p in db.get_parametros_por_tipo(tipo, solo_activos=solo_activos)]

    print(Fore.CYAN + f"\n{titulo}:")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")
    
    print() # Espacio para mejorar la legibilidad
    
    try:
        seleccion_idx = int(ui.solicitar_input(Fore.YELLOW + "Opción: ")) - 1
        if 0 <= seleccion_idx < len(items):
            return items[seleccion_idx]
        return None
    except (ValueError, IndexError):
        return None

def _procesar_paso_formulario(db: DatabaseManager, campo_actual: str, datos_equipo: dict, prompts: dict, placa_inicial_proveedor: str):
    """
    Procesa la lógica para un único campo del formulario.
    Devuelve la nueva placa inicial y un booleano indicando si el paso fue exitoso.
    """
    # --- Lógica para campos de selección ---
    if campo_actual == "Proveedor":
        seleccion = _seleccionar_parametro(db, 'proveedor', 'Seleccione un Proveedor')
        if not seleccion: return placa_inicial_proveedor, False
        datos_equipo[campo_actual] = seleccion
        proveedor_info = db.get_proveedor_by_name(seleccion)
        return proveedor_info.get('placa_inicial', ''), True
    
    if campo_actual == "Tipo de Equipo":
        seleccion = _seleccionar_parametro(db, 'tipo_activo', 'Seleccione un Tipo de Equipo')
        if not seleccion: return placa_inicial_proveedor, False
        datos_equipo[campo_actual] = seleccion
        return placa_inicial_proveedor, True

    if campo_actual == "Marca":
        seleccion = _seleccionar_parametro(db, 'marca_equipo', 'Seleccione una Marca')
        if not seleccion: return placa_inicial_proveedor, False
        datos_equipo[campo_actual] = seleccion
        return placa_inicial_proveedor, True

    if campo_actual == "Capacidad Memoria RAM":
        seleccion = _seleccionar_parametro(db, None, "Seleccione la Capacidad de RAM", lista_opciones=["4GB", "8GB", "16GB", "32GB", "Otro"])
        if seleccion == "Otro":
            valor_otro = ui.solicitar_input(Fore.YELLOW + "Ingrese la capacidad (ej: 64GB): ")
            if not validar_capacidad_almacenamiento(valor_otro, "RAM"):
                print(Fore.RED + "❌ Capacidad no válida. Use formato como '8GB' (max 256GB)."); ui.pausar_pantalla()
                return placa_inicial_proveedor, False
            datos_equipo[campo_actual] = valor_otro.upper().strip()
        elif seleccion:
            datos_equipo[campo_actual] = seleccion
        else: 
            return placa_inicial_proveedor, False
        return placa_inicial_proveedor, True

    if campo_actual == "Capacidad Disco Duro":
        seleccion = _seleccionar_parametro(db, None, "Seleccione la Capacidad del Disco", lista_opciones=["256GB", "512GB", "1TB", "Otro"])
        if seleccion == "Otro":
            valor_otro = ui.solicitar_input(Fore.YELLOW + "Ingrese la capacidad (ej: 2TB): ")
            if not validar_capacidad_almacenamiento(valor_otro, "Disco"):
                print(Fore.RED + "❌ Capacidad no válida. Use formato como '500GB' (max 20TB)."); ui.pausar_pantalla()
                return placa_inicial_proveedor, False
            datos_equipo[campo_actual] = valor_otro.upper().strip()
        elif seleccion:
            datos_equipo[campo_actual] = seleccion
        else: 
            return placa_inicial_proveedor, False
        return placa_inicial_proveedor, True

    if campo_actual == "Sistema Operativo":
        seleccion = _seleccionar_parametro(db, None, "Seleccione el Sistema Operativo", lista_opciones=["Windows 10", "Windows 11", "Linux", "macOS", "Otro"])
        if seleccion == "Otro":
            datos_equipo[campo_actual] = ui.solicitar_input(Fore.YELLOW + "Ingrese el SO: ")
        elif seleccion:
            datos_equipo[campo_actual] = seleccion
        else: 
            return placa_inicial_proveedor, False
        return placa_inicial_proveedor, True

    # --- Lógica para campos de texto libre ---
    prompt_texto = prompts.get(campo_actual, f"Ingrese {campo_actual}")
    
    if campo_actual == "Placa":
        prompt_placa = Fore.YELLOW + "Ingrese la Placa: " + Style.RESET_ALL + (placa_inicial_proveedor or "")
        placa_complemento = ui.solicitar_input(prompt_placa).upper()
        placa_completa = placa_inicial_proveedor + placa_complemento
        if not validar_placa_formato(placa_completa):
            print(Fore.RED + "Formato de placa inválido."); ui.pausar_pantalla()
            return placa_inicial_proveedor, False
        
        equipo_existente = db.get_equipo_by_placa(placa_completa)
        if equipo_existente:
            if equipo_existente['estado'] == "Devuelto a Proveedor":
                if ui.solicitar_input(f"⚠️ Placa existente devuelta. ¿Reactivar? (s/n): ").lower() == 's':
                    db.update_equipo_estado(placa_completa, "Disponible")
                    print(Fore.GREEN + "✅ Equipo reactivado exitosamente.")
                    # Como la operación terminó, indicamos éxito pero no hay que continuar el formulario
                    return placa_inicial_proveedor, "TERMINADO" 
                else:
                    return placa_inicial_proveedor, False # No exitoso, pide otra placa
            else:
                print(Fore.RED + "❌ Esta placa ya está registrada y activa."); ui.pausar_pantalla()
                return placa_inicial_proveedor, False
        datos_equipo[campo_actual] = placa_completa
        return placa_inicial_proveedor, True

    # --- Otros campos de texto ---
    valor = ui.solicitar_input(Fore.YELLOW + f"{prompt_texto}: ")
    if campo_actual == "Observaciones":
        datos_equipo[campo_actual] = formatear_observacion(valor)
    else:
        valor_procesado = valor.upper()
        if campo_actual == "Modelo" and not validar_campo_general(valor_procesado):
            print(Fore.RED + "Modelo inválido."); ui.pausar_pantalla()
            return placa_inicial_proveedor, False
        if campo_actual == "Número de serie" and not validar_serial(valor_procesado):
            print(Fore.RED + "Serial inválido."); ui.pausar_pantalla()
            return placa_inicial_proveedor, False
        datos_equipo[campo_actual] = valor_procesado
    
    return placa_inicial_proveedor, True

# --- FUNCIÓN PRINCIPAL DE REGISTRO ---

def registrar_nuevo_activo(db: DatabaseManager, usuario_logueado: dict):
    """Función principal para registrar un nuevo equipo, con lógica refactorizada."""
    # 1. Validación de configuración inicial
    configuraciones_faltantes = []
    if not db.get_parametros_por_tipo('tipo_activo', solo_activos=True):
        configuraciones_faltantes.append({'nombre': 'Tipos de Equipo', 'opcion_menu': '1'})
    if not db.get_parametros_por_tipo('marca_equipo', solo_activos=True):
        configuraciones_faltantes.append({'nombre': 'Marcas', 'opcion_menu': '2'})
    if not db.get_all_proveedores(solo_activos=True):
        configuraciones_faltantes.append({'nombre': 'Proveedores', 'opcion_menu': '3'})
    
    if configuraciones_faltantes:
        ui.mostrar_encabezado("Configuración Requerida", usuario_logueado=usuario_logueado)
        print(Fore.RED + "❌ No se puede registrar un nuevo equipo. Faltan configuraciones.")
        for item in configuraciones_faltantes:
            print(Fore.YELLOW + f"   - No hay '{item['nombre']}' activos configurados.")
        
        if ui.solicitar_input(Fore.CYAN + "\n¿Desea ir al menú de configuración ahora? (s/n): ").lower() == 's':
            start_option = configuraciones_faltantes[0]['opcion_menu'] if len(configuraciones_faltantes) == 1 else None
            menu_configuracion_sistema(db, usuario_logueado, start_option=start_option)
        return

    # 2. Inicialización del formulario
    campos = [
        "Proveedor", "Placa", "Tipo de Equipo", "Marca", "Modelo", "Número de serie",
        "Capacidad Memoria RAM", "Capacidad Disco Duro", "Sistema Operativo", "Observaciones"
    ]
    prompts = {
        "Modelo": "Ingrese el Modelo del equipo", "Número de serie": "Digite el Número de Serie",
        "Observaciones": "Agregue observaciones (opcional)"
    }
    datos_equipo = {campo: "" for campo in campos}
    indice_actual = 0
    placa_inicial_proveedor = ""

    try:
        # 3. Bucle principal del formulario
        while indice_actual < len(campos):
            campo_actual = campos[indice_actual]
            ui.mostrar_formulario_interactivo("Registrar Nuevo Activo", campos, datos_equipo, indice_actual, usuario_logueado)

            placa_inicial_proveedor, exito = _procesar_paso_formulario(
                db, campo_actual, datos_equipo, prompts, placa_inicial_proveedor
            )

            if exito == "TERMINADO": # Caso especial de reactivación
                return
            elif exito:
                indice_actual += 1
            # Si no hay éxito, el bucle se repite para el mismo campo

        # 4. Resumen y confirmación
        ui.mostrar_encabezado("Resumen del Nuevo Equipo", usuario_logueado=usuario_logueado)
        
        ancho_etiqueta = 25
        indentacion_info = "  "
        ancho_total = 80
        ancho_disponible = ancho_total - len(indentacion_info) - ancho_etiqueta - len(": ")

        for campo, valor in datos_equipo.items():
            etiqueta = f"{indentacion_info}{campo.ljust(ancho_etiqueta)}: "
            if campo == "Observaciones" and len(valor) > ancho_disponible:
                lineas = textwrap.wrap(valor, width=ancho_disponible)
                print(f"{etiqueta}{Fore.GREEN}{lineas[0]}{Style.RESET_ALL}")
                for linea in lineas[1:]:
                    print(f"{' ' * len(etiqueta)}{Fore.GREEN}{linea}{Style.RESET_ALL}")
            else:
                print(f"{etiqueta}{Fore.GREEN}{valor}{Style.RESET_ALL}")
        
        print(Fore.WHITE + "─" * 80)
        print(Fore.CYAN + "\n💡 Verifique la información antes de confirmar.")
        confirmacion_placa = ui.solicitar_input(Fore.YELLOW + f"Para confirmar, escriba la placa del equipo ({datos_equipo['Placa']}): ").upper()

        if confirmacion_placa == datos_equipo['Placa']:
            datos_equipo['proveedor_id'] = db.get_proveedor_by_name(datos_equipo['Proveedor'])['id']
            datos_equipo['tipo_equipo_id'] = next(p['id'] for p in db.get_parametros_por_tipo('tipo_activo', True) if p['valor'] == datos_equipo['Tipo de Equipo'])
            datos_equipo['marca_id'] = next(p['id'] for p in db.get_parametros_por_tipo('marca_equipo', True) if p['valor'] == datos_equipo['Marca'])
            datos_equipo['ram_id'] = db.get_or_create_normalized_id('memorias_ram', 'capacidad', datos_equipo['Capacidad Memoria RAM'])
            datos_equipo['disco_duro_id'] = db.get_or_create_normalized_id('discos_duros', 'capacidad', datos_equipo['Capacidad Disco Duro'])
            datos_equipo['so_id'] = db.get_or_create_normalized_id('sistemas_operativos', 'nombre', datos_equipo['Sistema Operativo'])
            
            db.insert_equipo(datos_equipo, usuario_logueado['id'])
            db.registrar_movimiento_sistema("Registro de Activo", f"Nuevo equipo registrado: Placa {datos_equipo['Placa']}", usuario_logueado['username'])
            print(Fore.GREEN + f"\n✅ ¡Equipo con placa {datos_equipo['Placa']} registrado exitosamente!")
            
            if ui.solicitar_input(Fore.YELLOW + "\n¿Desea gestionar este equipo ahora? (s/n): ").lower() == 's':
                print(Fore.CYAN + "\nFuncionalidad de gestión específica en desarrollo...")

        else:
            print(Fore.RED + "\nLa placa no coincide. Registro cancelado.")

    except KeyboardInterrupt:
        print(Fore.CYAN + "\n\n🚫 Operación cancelada.")
    finally:
        ui.pausar_pantalla()
