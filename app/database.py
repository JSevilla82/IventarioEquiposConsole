# app/database.py
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from colorama import Fore, Style

class DatabaseManager:
    """
    Gestiona todas las operaciones de la base de datos SQLite de forma centralizada.
    """
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Conecta a la base de datos y configura el modo de fila."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            print(Fore.RED + f"❌ Error al conectar a la base de datos: {e}" + Style.RESET_ALL); exit()

    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.conn: self.conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Ejecuta una consulta SQL."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        """Confirma los cambios en la base de datos."""
        self.conn.commit()

    def create_tables(self):
        """Crea las tablas de la base de datos si no existen."""
        cursor = self.conn.cursor()
        
        cursor.execute('CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY, nombre_rol TEXT UNIQUE NOT NULL)')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, nombre_completo TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, fecha_registro TEXT NOT NULL,
                cambio_clave_requerido INTEGER DEFAULT 1, is_active INTEGER DEFAULT 1
            )''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER, role_id INTEGER, PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users (id), FOREIGN KEY (role_id) REFERENCES roles (id)
            )''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY, user_id INTEGER, timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT, accion TEXT NOT NULL,
                detalles TEXT NOT NULL, usuario TEXT NOT NULL, fecha TEXT NOT NULL
            )''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parametros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                valor TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                UNIQUE(tipo, valor)
            )''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                placa_inicial TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            )''')
        
        self.commit()
        self.inicializar_roles()

    def inicializar_roles(self):
        from .config import ROLES
        for rol in ROLES:
            try: self.execute_query("INSERT INTO roles (nombre_rol) VALUES (?)", (rol,))
            except sqlite3.IntegrityError: pass
        self.commit()

    def inicializar_admin_si_no_existe(self) -> Tuple[bool, Optional[str]]:
        from .auth import hash_contrasena, generar_contrasena_temporal
        if self.execute_query("SELECT COUNT(id) as count FROM users").fetchone()['count'] == 0:
            admin_pass = generar_contrasena_temporal()
            user_data = ("Administrador Principal", "admin@local.host", "admin", hash_contrasena(admin_pass), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            cursor = self.execute_query('INSERT INTO users (nombre_completo, email, username, password_hash, fecha_registro) VALUES (?, ?, ?, ?, ?)', user_data)
            user_id = cursor.lastrowid
            role_id = self.get_role_id_by_name("Administrador")
            if user_id and role_id:
                self.execute_query("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
            self.commit()
            return True, admin_pass
        return False, None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        query = "SELECT u.*, r.nombre_rol FROM users u JOIN user_roles ur ON u.id = ur.user_id JOIN roles r ON ur.role_id = r.id WHERE u.username = ?"
        row = self.execute_query(query, (username,)).fetchone()
        return dict(row) if row else None

    def get_role_id_by_name(self, role_name: str) -> Optional[int]:
        row = self.execute_query("SELECT id FROM roles WHERE nombre_rol = ?", (role_name,)).fetchone()
        return row['id'] if row else None

    def log_login_attempt(self, user_id: int):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute_query("INSERT INTO login_logs (user_id, timestamp) VALUES (?, ?)", (user_id, timestamp))
        self.commit()
        
    def get_all_users_with_roles(self) -> List[Dict]:
        query = "SELECT u.*, r.nombre_rol FROM users u JOIN user_roles ur ON u.id = ur.user_id JOIN roles r ON ur.role_id = r.id ORDER BY u.nombre_completo"
        return [dict(row) for row in self.execute_query(query).fetchall()]
        
    def get_last_login_for_user(self, user_id: int) -> Optional[str]:
        row = self.execute_query("SELECT timestamp FROM login_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,)).fetchone()
        return row['timestamp'] if row else None

    def check_if_email_exists(self, email: str) -> bool:
        return self.execute_query("SELECT id FROM users WHERE email = ?", (email,)).fetchone() is not None

    def add_new_user(self, user_data: dict, role_name: str) -> bool:
        try:
            cursor = self.execute_query('INSERT INTO users (nombre_completo, email, username, password_hash, fecha_registro) VALUES (?, ?, ?, ?, ?)',
                                       (user_data['nombre_completo'], user_data['email'], user_data['username'], user_data['password_hash'], user_data['fecha_registro']))
            user_id = cursor.lastrowid
            role_id = self.get_role_id_by_name(role_name)
            if user_id and role_id:
                self.execute_query("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
            self.commit()
            return True
        except sqlite3.IntegrityError: return False

    def update_user_status(self, user_id: int, is_active: bool):
        self.execute_query("UPDATE users SET is_active = ? WHERE id = ?", (int(is_active), user_id)); self.commit()

    def update_user_fullname(self, user_id: int, new_name: str):
        self.execute_query("UPDATE users SET nombre_completo = ? WHERE id = ?", (new_name, user_id)); self.commit()

    def update_user_password(self, user_id: int, new_hash: str, require_change: bool):
        self.execute_query("UPDATE users SET password_hash = ?, cambio_clave_requerido = ? WHERE id = ?", (new_hash, int(require_change), user_id)); self.commit()

    def update_user_role(self, user_id: int, new_role_id: int):
        self.execute_query("UPDATE user_roles SET role_id = ? WHERE user_id = ?", (new_role_id, user_id)); self.commit()
        
    def registrar_movimiento_sistema(self, accion: str, detalles: str, usuario: str):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute_query("INSERT INTO log_sistema (accion, detalles, usuario, fecha) VALUES (?, ?, ?, ?)", (accion, detalles, usuario, fecha))
        self.commit()

    def get_log_sistema_paginated(self, page: int, page_size: int) -> Tuple[List[Dict], int]:
        offset = (page - 1) * page_size
        total_rows = self.execute_query("SELECT COUNT(id) FROM log_sistema").fetchone()[0]
        total_pages = (total_rows + page_size - 1) // page_size if total_rows > 0 else 1
        logs = self.execute_query("SELECT * FROM log_sistema ORDER BY fecha DESC LIMIT ? OFFSET ?", (page_size, offset)).fetchall()
        return [dict(row) for row in logs], total_pages
        
    def get_parametros_por_tipo(self, tipo: str) -> List[Dict]:
        cursor = self.execute_query("SELECT * FROM parametros WHERE tipo = ? ORDER BY valor", (tipo,))
        return [dict(row) for row in cursor.fetchall()]

    def add_parametro(self, tipo: str, valor: str) -> bool:
        try:
            self.execute_query('INSERT INTO parametros (tipo, valor) VALUES (?, ?)', (tipo, valor))
            self.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_parametro(self, parametro_id: int, nuevo_valor: str) -> bool:
        try:
            self.execute_query('UPDATE parametros SET valor = ? WHERE id = ?', (nuevo_valor, parametro_id))
            self.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_parametro_status(self, parametro_id: int, is_active: bool):
        self.execute_query('UPDATE parametros SET is_active = ? WHERE id = ?', (int(is_active), parametro_id))
        self.commit()

    def delete_parametro(self, parametro_id: int):
        self.execute_query('DELETE FROM parametros WHERE id = ?', (parametro_id,))
        self.commit()

    def get_all_proveedores(self) -> List[Dict]:
        cursor = self.execute_query("SELECT * FROM proveedores ORDER BY nombre")
        return [dict(row) for row in cursor.fetchall()]

    def add_proveedor(self, nombre: str, placa_inicial: str) -> bool:
        try:
            self.execute_query('INSERT INTO proveedores (nombre, placa_inicial) VALUES (?, ?)', (nombre, placa_inicial))
            self.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_proveedor(self, proveedor_id: int, nuevo_nombre: str, nueva_placa: str) -> bool:
        try:
            self.execute_query('UPDATE proveedores SET nombre = ?, placa_inicial = ? WHERE id = ?', (nuevo_nombre, nueva_placa, proveedor_id))
            self.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_proveedor_status(self, proveedor_id: int, is_active: bool):
        self.execute_query('UPDATE proveedores SET is_active = ? WHERE id = ?', (int(is_active), proveedor_id))
        self.commit()

    def delete_proveedor(self, proveedor_id: int):
        self.execute_query('DELETE FROM proveedores WHERE id = ?', (proveedor_id,))
        self.commit()

    def is_parametro_in_use(self, parametro_id: int) -> bool:
        # Lógica futura para verificar si un equipo usa este parámetro.
        # SELECT 1 FROM equipos WHERE tipo_id = ? OR marca_id = ? LIMIT 1
        return False

    def is_proveedor_in_use(self, proveedor_id: int) -> bool:
        # Lógica futura para verificar si un equipo usa este proveedor.
        # SELECT 1 FROM equipos WHERE proveedor_id = ? LIMIT 1
        return False