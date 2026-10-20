import sqlite3
import os
from pathlib import Path
class DatabaseManager:
    def __init__(self, db_name="proyecto_ed1.db"):
        db_name = os.environ.get("ED1_DB_PATH", db_name)
        if db_name != ":memory:":
            Path(db_name).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.crear_tablas()
    def crear_tablas(self):
        # Tabla para Undo/Redo de la lista
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_lista (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accion TEXT NOT NULL,
                valor TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Tabla para la bitácora de llamadas
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bitacora_llamadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_funcion TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Tabla para el estado de Hanói
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS estado_hanoi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                torre TEXT NOT NULL,
                disco INTEGER NOT NULL,
                posicion INTEGER NOT NULL
            )
        """)
        self.conn.commit()
    def guardar_accion_lista(self, accion, valor):
        self.cursor.execute(
            "INSERT INTO historial_lista (accion, valor) VALUES (?, ?)",
            (accion, valor)
        )
        self.conn.commit()
    def guardar_llamada(self, nombre_funcion):
        self.cursor.execute(
            "INSERT INTO bitacora_llamadas (nombre_funcion) VALUES (?)",
            (nombre_funcion,)
        )
        self.conn.commit()
    def guardar_estado_hanoi(self, torres_dict):
        # Borramos el estado anterior y guardamos el nuevo
        self.cursor.execute("DELETE FROM estado_hanoi")
        for torre, discos in torres_dict.items():
            for posicion, disco in enumerate(discos, start=1):
                self.cursor.execute(
                    "INSERT INTO estado_hanoi (torre, disco, posicion) VALUES (?, ?, ?)",
                    (torre, disco, posicion)
                )
        self.conn.commit()

    def cerrar(self):
        self.conn.close()