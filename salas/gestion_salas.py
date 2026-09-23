
import sqlite3

from database.conexion import obtener_conexion


def consultar_salas():
    # lista de salas por código
    conexion = None

    try:
        conexion = obtener_conexion()

        cursor = conexion.execute("""
            SELECT codigo, nombre, capacidad, estado
            FROM salas
            ORDER BY codigo ASC
        """)

        return cursor.fetchall()

    except sqlite3.Error as error:
        raise RuntimeError(
            "No fue posible consultar las salas."
        ) from error

    finally:
        if conexion is not None:
            conexion.close()