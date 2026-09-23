import sqlite3
from pathlib import Path

RUTA_PROYECTO = Path(__file__).resolve().parent.parent

RUTA_BD = RUTA_PROYECTO / "database" / "reservaciones.db"


def obtener_conexion():
    conexion = sqlite3.connect(RUTA_BD)

    conexion.execute("PRAGMA foreign_keys = ON")

    return conexion