# app/validators.py
import re

def validar_campo_general(valor: str) -> bool:
    """Permite letras, números y los caracteres especiales comunes (- _ . ,)."""
    return bool(re.match(r"^[a-zA-Z0-9-_.,\s]+$", valor))

def validar_placa_formato(placa: str) -> bool:
    """Mínimo 4 caracteres, solo letras, números y guion medio."""
    if len(placa) < 4:
        return False
    return bool(re.match(r"^[A-Z0-9-]+$", placa))

def validar_serial(serial: str) -> bool:
    """No permite espacios ni símbolos, solo letras y números."""
    return bool(re.match(r"^[a-zA-Z0-9]+$", serial))

def validar_capacidad_almacenamiento(cadena: str, tipo_componente: str) -> bool:
    """Valida la capacidad de RAM o Disco Duro con límites realistas."""
    cadena = cadena.upper().strip()
    match = re.match(r"^(\d+)\s*(GB|TB)$", cadena)
    if not match: return False
    valor_numerico, unidad = int(match.group(1)), match.group(2)
    capacidad_en_gb = valor_numerico * 1024 if unidad == "TB" else valor_numerico
    if tipo_componente == "RAM" and not (1 <= capacidad_en_gb <= 256): return False
    if tipo_componente == "Disco" and not (128 <= capacidad_en_gb <= 20480): return False
    return True

# --- NUEVA FUNCIÓN ---
def formatear_observacion(texto: str) -> str:
    """
    Formatea el texto de las observaciones.
    - Si está vacío, devuelve "Ninguna".
    - Si no, pone la primera letra en mayúscula y el resto en minúscula.
    """
    if not texto.strip():
        return "Ninguna"
    return texto.strip().capitalize()