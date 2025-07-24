# database.py
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
from colorama import Fore, Style

# --- MODELOS DE DATOS ---
class Equipo:
    def __init__(self, placa: str, tipo: str, marca: str, modelo: str, serial: str,
                 estado: str = "Disponible", asignado_a: Optional[str] = None,
                 email_asignado: Optional[str] = None, observaciones: Optional[str] = None,
                 fecha_registro: Optional[str] = None,
                 fecha_devolucion_prestamo: Optional[str] = None,
                 fecha_devolucion_proveedor: Optional[str] = None,
                 motivo_devolucion: Optional[str] = None):
        self.placa = placa
        self.tipo = tipo
        self.marca = marca
        self.modelo = modelo
        self.serial = serial
        self.estado = estado
        self.asignado_a = asignado_a
        self.email_asignado = email_asignado
        self.observaciones = observaciones
        self.fecha_registro = fecha_registro if fecha_registro else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.fecha_devolucion_prestamo = fecha_devolucion_prestamo
        self.fecha_devolucion_proveedor = fecha_devolucion_proveedor
        self.motivo_devolucion = motivo_devolucion

    def to_dict(self) -> Dict:
        return self.__dict__

class MovimientoHistorico:
    def __init__(self, equipo_placa: str, accion: str, detalles: str, usuario: str, fecha: Optional[str] = None):
        self.equipo_placa = equipo_placa
        self.accion = accion
        self.detalles = detalles
        self.usuario = usuario
        self.fecha = fecha if fecha else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict:
        return self.__dict__

class Usuario:
    def __init__(self, nombre_usuario: str, contrasena_hash: str, rol: str, nombre_completo: Optional[str] = None, cambio_clave_requerido: bool = True, is_active: bool = True):
        self.nombre_usuario = nombre_usuario
        self.contrasena_hash = contrasena_hash
        self.rol = rol
        self.nombre_completo = nombre_completo
        self.cambio_clave_requerido = cambio_clave_requerido
        self.is_active = is_active

    def to_dict(self) -> Dict:
        return self.__dict__

# --- GESTOR DE BASE DE DATOS SQLITE ---
class DatabaseManager:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.conn = None
        self.connect()
        self.create_tables()
        self.add_missing_columns()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(Fore.RED + f"❌ Error al conectar a la base de datos: {e}" + Style.RESET_ALL)
            exit()

    def close(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipos (
                placa TEXT PRIMARY KEY, tipo TEXT NOT NULL, marca TEXT NOT NULL,
                modelo TEXT NOT NULL, serial TEXT NOT NULL, estado TEXT NOT NULL,
                asignado_a TEXT, email_asignado TEXT, observaciones TEXT,
                fecha_registro TEXT, fecha_devolucion_prestamo TEXT, 
                fecha_devolucion_proveedor TEXT, motivo_devolucion TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT, equipo_placa TEXT NOT NULL,
                accion TEXT NOT NULL, detalles TEXT NOT NULL, usuario TEXT NOT NULL, fecha TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                nombre_usuario TEXT PRIMARY KEY, contrasena_hash TEXT NOT NULL,
                rol TEXT NOT NULL, nombre_completo TEXT, 
                cambio_clave_requerido INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parametros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                valor TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                UNIQUE(tipo, valor)
            )
        ''')
        self.conn.commit()

    def add_missing_columns(self):
        columns_to_add = {
            'equipos': [
                ('fecha_devolucion_prestamo', 'TEXT'),
                ('fecha_devolucion_proveedor', 'TEXT'),
                ('motivo_devolucion', 'TEXT')
            ],
            'usuarios': [
                ('nombre_completo', 'TEXT'),
                ('cambio_clave_requerido', 'INTEGER NOT NULL DEFAULT 1'),
                ('is_active', 'INTEGER NOT NULL DEFAULT 1')
            ],
            'parametros': [
                ('is_active', 'INTEGER NOT NULL DEFAULT 1')
            ]
        }
        cursor = self.conn.cursor()
        for table, cols in columns_to_add.items():
            for col_name, col_type in cols:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    self.conn.commit()
                except sqlite3.OperationalError:
                    pass

    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        self.conn.commit()

    # --- Métodos para Equipos ---
    def insert_equipo(self, equipo: Equipo):
        self.execute_query('''
            INSERT INTO equipos (placa, tipo, marca, modelo, serial, estado, asignado_a, email_asignado, observaciones, fecha_registro, fecha_devolucion_prestamo, fecha_devolucion_proveedor, motivo_devolucion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (equipo.placa, equipo.tipo, equipo.marca, equipo.modelo, equipo.serial, equipo.estado, equipo.asignado_a, equipo.email_asignado, equipo.observaciones, equipo.fecha_registro, equipo.fecha_devolucion_prestamo, equipo.fecha_devolucion_proveedor, equipo.motivo_devolucion))
        self.commit()

    def get_all_equipos(self) -> List[Dict]:
        cursor = self.execute_query('SELECT * FROM equipos')
        return [dict(row) for row in cursor.fetchall()]

    def get_equipo_by_placa(self, placa: str) -> Optional[Dict]:
        cursor = self.execute_query('SELECT * FROM equipos WHERE placa = ?', (placa,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_equipo(self, equipo: Equipo):
        self.execute_query('''
            UPDATE equipos SET tipo = ?, marca = ?, modelo = ?, serial = ?, estado = ?, asignado_a = ?,
            email_asignado = ?, observaciones = ?, fecha_devolucion_prestamo = ?, fecha_devolucion_proveedor = ?,
            motivo_devolucion = ? WHERE placa = ?
        ''', (equipo.tipo, equipo.marca, equipo.modelo, equipo.serial, equipo.estado, equipo.asignado_a,
              equipo.email_asignado, equipo.observaciones, equipo.fecha_devolucion_prestamo,
              equipo.fecha_devolucion_proveedor, equipo.motivo_devolucion, equipo.placa))
        self.commit()

    def delete_equipo(self, placa: str):
        self.execute_query('DELETE FROM equipos WHERE placa = ?', (placa,))
        self.commit()

    # --- Métodos para Histórico ---
    def insert_movimiento(self, movimiento: MovimientoHistorico):
        self.execute_query('''
            INSERT INTO historico (equipo_placa, accion, detalles, usuario, fecha) VALUES (?, ?, ?, ?, ?)
        ''', (movimiento.equipo_placa, movimiento.accion, movimiento.detalles, movimiento.usuario, movimiento.fecha))
        self.commit()

    def get_all_historico(self) -> List[Dict]:
        cursor = self.execute_query('SELECT * FROM historico ORDER BY fecha DESC')
        return [dict(row) for row in cursor.fetchall()]

    # --- Métodos para Usuarios ---
    def insert_user(self, user: Usuario):
        self.execute_query('''
            INSERT INTO usuarios (nombre_usuario, contrasena_hash, rol, nombre_completo, cambio_clave_requerido, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user.nombre_usuario, user.contrasena_hash, user.rol, user.nombre_completo, int(user.cambio_clave_requerido), int(user.is_active)))
        self.commit()

    def get_user_by_username(self, nombre_usuario: str) -> Optional[Dict]:
        cursor = self.execute_query('SELECT * FROM usuarios WHERE nombre_usuario = ?', (nombre_usuario,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_user(self, user: Usuario):
        self.execute_query('''
            UPDATE usuarios SET contrasena_hash = ?, rol = ?, nombre_completo = ?, cambio_clave_requerido = ?, is_active = ?
            WHERE nombre_usuario = ?
        ''', (user.contrasena_hash, user.rol, user.nombre_completo, int(user.cambio_clave_requerido), int(user.is_active), user.nombre_usuario))
        self.commit()

    def get_all_users(self) -> List[Dict]:
        cursor = self.execute_query('SELECT nombre_usuario, rol, nombre_completo, cambio_clave_requerido, is_active FROM usuarios')
        return [dict(row) for row in cursor.fetchall()]

    # --- Métodos para Parámetros ---
    def add_parametro(self, tipo: str, valor: str):
        self.execute_query('INSERT INTO parametros (tipo, valor, is_active) VALUES (?, ?, 1)', (tipo, valor))
        self.commit()

    def get_parametros_por_tipo(self, tipo: str, solo_activos: bool = False) -> List[Dict]:
        query = 'SELECT valor, is_active FROM parametros WHERE tipo = ?'
        if solo_activos:
            query += ' AND is_active = 1'
        query += ' ORDER BY valor'
        cursor = self.execute_query(query, (tipo,))
        return [dict(row) for row in cursor.fetchall()]

    def update_parametro_status(self, tipo: str, valor: str, new_status: bool):
        self.execute_query('UPDATE parametros SET is_active = ? WHERE tipo = ? AND valor = ?', (int(new_status), tipo, valor))
        self.commit()

    def is_parametro_in_use(self, tipo_parametro: str, valor: str) -> bool:
        columna_equipo = tipo_parametro.split('_')[0]
        if columna_equipo not in ['tipo', 'marca']:
            return False
        query = f"SELECT 1 FROM equipos WHERE {columna_equipo} = ? LIMIT 1"
        cursor = self.execute_query(query, (valor,))
        return cursor.fetchone() is not None

    # --- *** MÉTODO AÑADIDO *** ---
    def delete_parametro(self, tipo: str, valor: str):
        """Elimina un parámetro de la base de datos."""
        self.execute_query('DELETE FROM parametros WHERE tipo = ? AND valor = ?', (tipo, valor))
        self.commit()

db_manager = DatabaseManager("inventario.db")

# --- FUNCIONES DE PERSISTENCIA ---
def registrar_movimiento(placa: str, accion: str, detalles: str, usuario: str):
    movimiento = MovimientoHistorico(placa, accion, detalles, usuario)
    db_manager.insert_movimiento(movimiento)