import sqlite3
from datetime import datetime

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


def validar_sala(codigo, nombre, capacidad, estado):
    """
    Valida y normaliza los datos de una sala.
    """

    if not isinstance(codigo, str):
        raise ValueError("El código de la sala es obligatorio.")

    codigo = codigo.strip().upper()

    if not codigo:
        raise ValueError("El código de la sala es obligatorio.")

    if not isinstance(nombre, str):
        raise ValueError("El nombre de la sala es obligatorio.")

    nombre = nombre.strip()

    if not nombre:
        raise ValueError("El nombre de la sala es obligatorio.")

    if isinstance(capacidad, bool):
        raise ValueError(
            "La capacidad debe ser un número entero mayor que cero."
        )

    if isinstance(capacidad, int):
        capacidad = capacidad
    elif isinstance(capacidad, str):
        texto_capacidad = capacidad.strip()

        if not texto_capacidad.isdigit():
            raise ValueError(
                "La capacidad debe ser un número entero mayor que cero."
            )

        capacidad = int(texto_capacidad)

    else:
        raise ValueError(
            "La capacidad debe ser un número entero mayor que cero."
        )

    if capacidad <= 0:
        raise ValueError(
            "La capacidad debe ser un número entero mayor que cero."
        )

    if not isinstance(estado, str):
        raise ValueError(
            "El estado de la sala debe ser disponible o fuera de servicio."
        )

    estado = estado.strip().lower().replace(" ", "_")

    if estado not in ("disponible", "fuera_de_servicio"):
        raise ValueError(
            "El estado de la sala debe ser disponible o fuera de servicio."
        )

    return codigo, nombre, capacidad, estado


def registrar_sala(codigo, nombre, capacidad, estado="disponible"):
    """
    RF-12. Registra una nueva sala.

    Devuelve:
        (True, mensaje) si se registra correctamente.
        (False, mensaje) si los datos son inválidos o el código ya existe.
    """

    try:
        codigo, nombre, capacidad, estado = validar_sala(
            codigo,
            nombre,
            capacidad,
            estado,
        )

    except ValueError as error:
        return False, str(error)

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion:
            conexion.execute(
                """
                INSERT INTO salas
                    (codigo, nombre, capacidad, estado)
                VALUES (?, ?, ?, ?)
                """,
                (
                    codigo,
                    nombre,
                    capacidad,
                    estado,
                ),
            )

        return True, f"La sala {codigo} se registró correctamente."

    except sqlite3.IntegrityError:
        return False, f"El código {codigo} ya se encuentra registrado."

    except sqlite3.Error:
        return False, "No fue posible registrar la sala."

    finally:
        if conexion is not None:
            conexion.close()


def modificar_sala(codigo, nombre, capacidad, estado, ahora=None):
    """
    RF-12. Modifica el nombre, capacidad y estado de una sala.

    El código se utiliza únicamente para identificar la sala
    y no puede modificarse.
    """

    try:
        codigo, nombre, capacidad, estado = validar_sala(
            codigo,
            nombre,
            capacidad,
            estado,
        )

    except ValueError as error:
        return False, str(error)

    if ahora is None:
        ahora = datetime.now()

    conexion = None

    try:
        conexion = obtener_conexion()

        sala = conexion.execute(
            """
            SELECT codigo, capacidad
            FROM salas
            WHERE codigo = ? COLLATE NOCASE
            """,
            (codigo,),
        ).fetchone()

        if sala is None:
            return False, f"La sala {codigo} no se encuentra registrada."

        # Comprobar reservaciones activas futuras de la sala.
        hoy = ahora.date().isoformat()
        minutos_actuales = ahora.hour * 60 + ahora.minute

        resultado = conexion.execute(
            """
            SELECT MAX(cantidad_personas)
            FROM reservaciones
            WHERE codigo_sala = ? COLLATE NOCASE
              AND estado = 'activa'
              AND (
                    fecha > ?
                    OR (
                        fecha = ?
                        AND CAST(substr(hora_inicio, 1, 2) AS INTEGER) * 60
                            > ?
                    )
              )
            """,
            (
                sala[0],
                hoy,
                hoy,
                minutos_actuales,
            ),
        ).fetchone()

        mayor_cantidad_reservada = resultado[0]

        if (
            mayor_cantidad_reservada is not None
            and capacidad < mayor_cantidad_reservada
        ):
            return (
                False,
                "La capacidad no puede reducirse por debajo de la cantidad "
                "de personas de una reservación activa futura.",
            )

        with conexion:
            conexion.execute(
                """
                UPDATE salas
                SET nombre = ?,
                    capacidad = ?,
                    estado = ?
                WHERE codigo = ?
                """,
                (
                    nombre,
                    capacidad,
                    estado,
                    sala[0],
                ),
            )

        return True, f"La sala {sala[0]} se modificó correctamente."

    except sqlite3.Error:
        return False, "No fue posible modificar la sala."

    finally:
        if conexion is not None:
            conexion.close()