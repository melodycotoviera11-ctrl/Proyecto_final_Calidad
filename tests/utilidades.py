"""
Utilidades compartidas por las pruebas.

Cada prueba trabaja sobre una base de datos temporal creada con la
inicialización oficial del proyecto (RF-01), por lo que nunca se altera
database/reservaciones.db (RNF-10).
"""

import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import database.conexion as conexion_modulo
from database.inicializacion import inicializar_base_datos

# "Ahora" fijo para que las pruebas no dependan del reloj real.
AHORA = datetime(2026, 10, 5, 9, 30)          # lunes 5 de octubre, 09:30
HOY = "2026-10-05"
MANANA = "2026-10-06"
PASADO_MANANA = "2026-10-07"

ACTIVO = "A001234567"       # Andrea Solano (activa)
ACTIVO_2 = "B009876543"     # Carlos Méndez (activo)
INACTIVO = "C004567890"     # Daniela Rojas (inactiva)


class PruebaConBaseTemporal(unittest.TestCase):

    def setUp(self):
        self.directorio = Path(tempfile.mkdtemp())
        self.ruta_bd = self.directorio / "prueba.db"

        self.parche = mock.patch.object(conexion_modulo, "RUTA_BD", self.ruta_bd)
        self.parche.start()

        self.assertTrue(inicializar_base_datos(), "No se pudo crear la BD de prueba")

    def tearDown(self):
        self.parche.stop()
        shutil.rmtree(self.directorio, ignore_errors=True)

    # --- Acceso directo solo para preparar escenarios y verificar ---

    def sql(self, sentencia, parametros=()):
        conexion = sqlite3.connect(self.ruta_bd)
        try:
            with conexion:
                return conexion.execute(sentencia, parametros).fetchall()
        finally:
            conexion.close()

    def insertar_directo(self, carne, sala, fecha, hora, duracion=1,
                         cantidad=1, estado="activa"):
        conexion = sqlite3.connect(self.ruta_bd)
        try:
            with conexion:
                cursor = conexion.execute(
                    """
                    INSERT INTO reservaciones
                        (carne, codigo_sala, fecha, hora_inicio, duracion,
                         cantidad_personas, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (carne, sala, fecha, hora, duracion, cantidad, estado),
                )
                return cursor.lastrowid
        finally:
            conexion.close()

    def conteos(self):
        """Estado completo de las tablas que P2 podría modificar."""
        return (
            self.sql("SELECT * FROM reservaciones ORDER BY id"),
            self.sql("SELECT * FROM auditoria ORDER BY id"),
            self.sql("SELECT * FROM estudiantes ORDER BY carne"),
            self.sql("SELECT * FROM salas ORDER BY codigo"),
        )
