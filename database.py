# database.py
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
from colorama import Fore, Style

# --- MODELOS DE DATOS ---
class Equipo:
    # MODIFICADO: Añadidos campos para renovación
    def __init__(self, placa: str, tipo: str, marca: str, modelo: str, serial: str,
                 estado: str = "Disponible", asignado_a: Optional[str] = None,
                 email_asignado: Optional[str] = None, observaciones: Optional[str] = None,
                 fecha_registro: Optional[str] = None,
                 fecha_devolucion_prestamo: Optional[str] = None,
                 fecha_devolucion_proveedor: Optional[str] = None,
                 motivo_devolucion: Optional[str] = None,
                 estado_anterior: Optional[str] = None,
                 renovacion_placa_asociada: Optional[str] = None,
                 fecha_entrega_renovacion: Optional[str] = None):
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
        self.estado_anterior = estado_anterior
        self.renovacion_placa_asociada = renovacion_placa_asociada
        self.fecha_entrega_renovacion = fecha_entrega_renovacion

    def to_dict(self) -> Dict:
        return self.__dict__

class LogInventario:
    def __init__(self, equipo_placa: str, accion: str, detalles: str, usuario: str, fecha: Optional[str] = None):
        self.equipo_placa = equipo_placa
        self.accion = accion
        self.detalles = detalles
        self.usuario = usuario
        self.fecha = fecha if fecha else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class LogSistema:
    def __init__(self, accion: str, detalles: str, usuario: str, fecha: Optional[str] = None):
        self.accion = accion
        self.detalles = detalles
        self.usuario = usuario
        self.fecha = fecha if fecha else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
            self.conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            print(Fore.RED + f"❌ Error al conectar a la base de datos: {e}" + Style.RESET_ALL)
            exit()

    def close(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        cursor = self.conn.cursor()
        # MODIFICADO: Añadidos campos para renovación en la tabla equipos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipos (
                placa TEXT PRIMARY KEY, tipo TEXT NOT NULL, marca TEXT NOT NULL,
                modelo TEXT NOT NULL, serial TEXT NOT NULL, estado TEXT NOT NULL,
                asignado_a TEXT, email_asignado TEXT, observaciones TEXT,
                fecha_registro TEXT, fecha_devolucion_prestamo TEXT, 
                fecha_devolucion_proveedor TEXT, motivo_devolucion TEXT,
                estado_anterior TEXT, renovacion_placa_asociada TEXT,
                fecha_entrega_renovacion TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT, equipo_placa TEXT NOT NULL,
                accion TEXT NOT NULL, detalles TEXT NOT NULL, usuario TEXT NOT NULL, fecha TEXT NOT NULL,
                FOREIGN KEY (equipo_placa) REFERENCES equipos (placa) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT, accion TEXT NOT NULL, 
                detalles TEXT NOT NULL, usuario TEXT NOT NULL, fecha TEXT NOT NULL
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
                ('motivo_devolucion', 'TEXT'),
                ('estado_anterior', 'TEXT'),
                ('renovacion_placa_asociada', 'TEXT'),
                ('fecha_entrega_renovacion', 'TEXT')
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
            INSERT INTO equipos (placa, tipo, marca, modelo, serial, estado, asignado_a, email_asignado, observaciones, fecha_registro, fecha_devolucion_prestamo, fecha_devolucion_proveedor, motivo_devolucion, estado_anterior, renovacion_placa_asociada, fecha_entrega_renovacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (equipo.placa, equipo.tipo, equipo.marca, equipo.modelo, equipo.serial, equipo.estado, equipo.asignado_a, equipo.email_asignado, equipo.observaciones, equipo.fecha_registro, equipo.fecha_devolucion_prestamo, equipo.fecha_devolucion_proveedor, equipo.motivo_devolucion, equipo.estado_anterior, equipo.renovacion_placa_asociada, equipo.fecha_entrega_renovacion))
        self.commit()

    def get_all_equipos(self) -> List[Dict]:
        cursor = self.execute_query('SELECT * FROM equipos')
        return [dict(row) for row in cursor.fetchall()]

    def get_equipos_activos(self) -> List[Dict]:
        cursor = self.execute_query("SELECT * FROM equipos WHERE estado != 'Devuelto a Proveedor'")
        return [dict(row) for row in cursor.fetchall()]

    def get_equipos_devueltos(self) -> List[Dict]:
        cursor = self.execute_query("SELECT * FROM equipos WHERE estado = 'Devuelto a Proveedor'")
        return [dict(row) for row in cursor.fetchall()]
        
    def get_new_equipos(self) -> List[Dict]:
        """Obtiene equipos que solo tienen un movimiento en el log (su registro)."""
        query = """
            SELECT e.* FROM equipos e
            JOIN (
                SELECT equipo_placa, COUNT(id) as count
                FROM log_inventario
                GROUP BY equipo_placa
            ) AS log_counts ON e.placa = log_counts.equipo_placa
            WHERE log_counts.count = 1 AND e.estado = 'Disponible'
        """
        cursor = self.execute_query(query)
        return [dict(row) for row in cursor.fetchall()]

    def get_available_not_new_equipos(self) -> List[Dict]:
        """Obtiene equipos disponibles que ya han tenido movimientos."""
        query = """
            SELECT e.* FROM equipos e
            JOIN (
                SELECT equipo_placa, COUNT(id) as count
                FROM log_inventario
                GROUP BY equipo_placa
            ) AS log_counts ON e.placa = log_counts.equipo_placa
            WHERE log_counts.count > 1 AND e.estado = 'Disponible'
        """
        cursor = self.execute_query(query)
        return [dict(row) for row in cursor.fetchall()]

    def get_equipo_by_placa(self, placa: str) -> Optional[Dict]:
        cursor = self.execute_query('SELECT * FROM equipos WHERE placa = ?', (placa,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_equipo(self, equipo: Equipo):
        self.execute_query('''
            UPDATE equipos SET tipo = ?, marca = ?, modelo = ?, serial = ?, estado = ?, asignado_a = ?,
            email_asignado = ?, observaciones = ?, fecha_devolucion_prestamo = ?, fecha_devolucion_proveedor = ?,
            motivo_devolucion = ?, estado_anterior = ?, renovacion_placa_asociada = ?, fecha_entrega_renovacion = ?
            WHERE placa = ?
        ''', (equipo.tipo, equipo.marca, equipo.modelo, equipo.serial, equipo.estado, equipo.asignado_a,
              equipo.email_asignado, equipo.observaciones, equipo.fecha_devolucion_prestamo,
              equipo.fecha_devolucion_proveedor, equipo.motivo_devolucion, equipo.estado_anterior, 
              equipo.renovacion_placa_asociada, equipo.fecha_entrega_renovacion, equipo.placa))
        self.commit()

    def delete_equipo(self, placa: str):
        self.execute_query('DELETE FROM equipos WHERE placa = ?', (placa,))
        self.commit()

    # --- Métodos para Logs ---
    def insert_log_inventario(self, log: LogInventario):
        self.execute_query('''
            INSERT INTO log_inventario (equipo_placa, accion, detalles, usuario, fecha) VALUES (?, ?, ?, ?, ?)
        ''', (log.equipo_placa, log.accion, log.detalles, log.usuario, log.fecha))
        self.commit()

    def count_movimientos_by_placa(self, placa: str) -> int:
        cursor = self.execute_query('SELECT COUNT(id) FROM log_inventario WHERE equipo_placa = ?', (placa,))
        result = cursor.fetchone()
        return result[0] if result else 0
        
    def get_log_by_placa(self, placa: str, limit: Optional[int] = None) -> List[Dict]:
        """Obtiene el historial de movimientos para una placa, con un límite opcional."""
        query = 'SELECT * FROM log_inventario WHERE equipo_placa = ? ORDER BY fecha DESC'
        if limit:
            query += f' LIMIT {limit}'
        cursor = self.execute_query(query, (placa,))
        return [dict(row) for row in cursor.fetchall()]

    def insert_log_sistema(self, log: LogSistema):
        self.execute_query('''
            INSERT INTO log_sistema (accion, detalles, usuario, fecha) VALUES (?, ?, ?, ?)
        ''', (log.accion, log.detalles, log.usuario, log.fecha))
        self.commit()

    def get_all_log_inventario(self) -> List[Dict]:
        cursor = self.execute_query('SELECT * FROM log_inventario ORDER BY fecha DESC')
        return [dict(row) for row in cursor.fetchall()]

    def get_all_log_sistema(self) -> List[Dict]:
        cursor = self.execute_query('SELECT * FROM log_sistema ORDER BY fecha DESC')
        return [dict(row) for row in cursor.fetchall()]

    def get_last_movimiento_by_placa(self, placa: str) -> Optional[Dict]:
        cursor = self.execute_query('SELECT * FROM log_inventario WHERE equipo_placa = ? ORDER BY fecha DESC LIMIT 1', (placa,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_last_log_by_action(self, placa: str, accion: str) -> Optional[Dict]:
        """Obtiene el último registro de log para una placa y acción específicas."""
        cursor = self.execute_query('SELECT * FROM log_inventario WHERE equipo_placa = ? AND accion = ? ORDER BY fecha DESC LIMIT 1', (placa, accion))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def get_last_movimientos_by_user(self, usuario: str, limit: int = 10) -> List[Dict]:
        """Obtiene los últimos movimientos de inventario realizados por un usuario específico."""
        query = """
            SELECT
                li.fecha,
                li.equipo_placa,
                e.marca,
                li.accion,
                li.detalles
            FROM
                log_inventario li
            LEFT JOIN
                equipos e ON li.equipo_placa = e.placa
            WHERE
                li.usuario = ?
            ORDER BY
                li.fecha DESC
            LIMIT ?
        """
        cursor = self.execute_query(query, (usuario, limit))
        return [dict(row) for row in cursor.fetchall()]

    def get_movimientos_en_rango_de_fechas(self, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
        """Obtiene todos los movimientos de inventario dentro de un rango de fechas."""
        query = """
            SELECT * FROM log_inventario
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC
        """
        cursor = self.execute_query(query, (fecha_inicio, fecha_fin))
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
        if tipo_parametro == 'dominio_correo':
            query = "SELECT 1 FROM equipos WHERE email_asignado LIKE ? LIMIT 1"
            cursor = self.execute_query(query, (f'%@{valor}',))
            return cursor.fetchone() is not None

        columna_equipo = tipo_parametro.split('_')[0]
        if columna_equipo not in ['tipo', 'marca']:
            return False
        
        query = f"SELECT 1 FROM equipos WHERE {columna_equipo} = ? LIMIT 1"
        cursor = self.execute_query(query, (valor,))
        return cursor.fetchone() is not None
        
    def delete_parametro(self, tipo: str, valor: str):
        self.execute_query('DELETE FROM parametros WHERE tipo = ? AND valor = ?', (tipo, valor))
        self.commit()

db_manager = DatabaseManager("inventario.db")

def registrar_movimiento_inventario(placa: str, accion: str, detalles: str, usuario: str):
    log = LogInventario(placa, accion, detalles, usuario)
    db_manager.insert_log_inventario(log)

def registrar_movimiento_sistema(accion: str, detalles: str, usuario: str):
    log = LogSistema(accion, detalles, usuario)
    db_manager.insert_log_sistema(log)