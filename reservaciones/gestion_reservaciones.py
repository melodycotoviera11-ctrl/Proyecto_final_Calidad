"""
Gestión de reservaciones: RF-05 (crear), RF-06 (consultar) y
RF-07 (buscar por estudiante).

Este módulo concentra el acceso a datos de reservaciones; la interfaz
gráfica solo llama a estas funciones y nunca ejecuta SQL (RNF-07).
"""

import sqlite3
from datetime import datetime

from database.conexion import obtener_conexion
from reservaciones import validaciones as v
from reservaciones.reglas import validar_reservacion

# Orden de las columnas que devuelven consultar_reservaciones() y
# buscar_por_estudiante(). Lo usan la interfaz y los reportes.
COLUMNAS_RESERVACION = (
    "id",
    "carne",
    "estudiante",
    "codigo_sala",
    "sala",
    "fecha",
    "hora_inicio",
    "hora_fin",
    "cantidad_personas",
    "estado",
)

_SELECT_DETALLE = """
    SELECT r.id,
           r.carne,
           e.nombre_completo,
           r.codigo_sala,
           s.nombre,
           r.fecha,
           r.hora_inicio,
           printf('%02d:00', CAST(substr(r.hora_inicio, 1, 2) AS INTEGER) + r.duracion),
           r.cantidad_personas,
           r.estado
    FROM reservaciones r
    LEFT JOIN estudiantes e ON e.carne = r.carne
    LEFT JOIN salas s ON s.codigo = r.codigo_sala
"""

_ORDEN_DETALLE = " ORDER BY r.fecha ASC, r.hora_inicio ASC, r.id ASC"


def registrar_auditoria(conexion, tipo_accion, entidad, identificador):
    """
    Inserta un registro en la tabla auditoria usando la MISMA conexión,
    para que se confirme o se revierta junto con la operación (RF-17).

    Nota de integración: si P4 publica una función propia para RF-17,
    basta con reemplazar el cuerpo de esta función por esa llamada.
    """
    conexion.execute(
        """
        INSERT INTO auditoria (fecha_hora, tipo_accion, entidad, identificador)
        VALUES (?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tipo_accion,
            entidad,
            str(identificador),
        ),
    )


def insertar_reservacion(conexion, datos, serie_id=None):
    """
    Inserta una reservación YA VALIDADA con estado 'activa' y registra la
    auditoría. No confirma la transacción: eso le corresponde a quien llama.
    Pensada también para RF-14 (serie recurrente, usando serie_id).

    El ID se genera con AUTOINCREMENT, por lo que nunca se reutiliza,
    ni siquiera el de una reservación cancelada (RN-13).
    """
    cursor = conexion.execute(
        """
        INSERT INTO reservaciones
            (carne, codigo_sala, fecha, hora_inicio, duracion,
             cantidad_personas, estado, serie_id)
        VALUES (?, ?, ?, ?, ?, ?, 'activa', ?)
        """,
        (
            datos["carne"],
            datos["codigo_sala"],
            v.fecha_a_texto(datos["fecha"]),
            v.formatear_hora(datos["hora_inicio"]),
            datos["duracion"],
            datos["cantidad_personas"],
            serie_id,
        ),
    )

    id_reservacion = cursor.lastrowid
    registrar_auditoria(conexion, "creación", "reservación", id_reservacion)

    return id_reservacion


def crear_reservacion(carne, codigo_sala, fecha, hora_inicio, duracion,
                      cantidad_personas, ahora=None):
    """
    RF-05. Valida todas las reglas de negocio y, si se cumplen, almacena la
    reservación con estado activa.

    Devuelve (exito, mensaje, id_reservacion). Si falla una regla,
    id_reservacion es None y la base de datos no se modifica.
    """
    conexion = None

    try:
        conexion = obtener_conexion()

        # BEGIN IMMEDIATE bloquea escrituras concurrentes: la verificación de
        # superposición y la inserción ocurren en una sola transacción.
        conexion.execute("BEGIN IMMEDIATE")

        try:
            datos = validar_reservacion(
                conexion, carne, codigo_sala, fecha, hora_inicio,
                duracion, cantidad_personas, ahora,
            )
            id_reservacion = insertar_reservacion(conexion, datos)
            conexion.commit()

        except Exception:
            conexion.rollback()
            raise

        mensaje = (
            f"Reservación creada correctamente con el ID {id_reservacion}: "
            f"sala {datos['codigo_sala']}, {v.fecha_a_texto(datos['fecha'])}, "
            f"{v.formatear_hora(datos['hora_inicio'])} a "
            f"{v.formatear_hora(datos['hora_inicio'] + datos['duracion'])}."
        )
        return True, mensaje, id_reservacion

    except ValueError as error:
        return False, str(error), None

    except sqlite3.Error:
        return False, "No fue posible guardar la reservación. Intente de nuevo.", None

    finally:
        if conexion is not None:
            conexion.close()


def consultar_reservaciones():
    """
    RF-06. Devuelve todas las reservaciones (activas y canceladas) ordenadas
    por fecha y hora. Cada fila sigue el orden de COLUMNAS_RESERVACION.
    Si no hay registros devuelve una lista vacía.
    """
    conexion = None

    try:
        conexion = obtener_conexion()
        return conexion.execute(_SELECT_DETALLE + _ORDEN_DETALLE).fetchall()

    except sqlite3.Error as error:
        raise RuntimeError("No fue posible consultar las reservaciones.") from error

    finally:
        if conexion is not None:
            conexion.close()


def buscar_por_estudiante(carne):
    """
    RF-07. Busca las reservaciones (activas y canceladas) de un estudiante
    sin distinguir mayúsculas y minúsculas en el carné.

    Devuelve (exito, mensaje, reservaciones):
        - carné vacío o inexistente  -> (False, motivo, [])
        - estudiante sin reservaciones -> (True, aviso, [])
        - con reservaciones           -> (True, resumen, filas)
    """
    try:
        carne = v.normalizar_carne(carne)
    except ValueError as error:
        return False, str(error), []

    conexion = None

    try:
        conexion = obtener_conexion()

        estudiante = conexion.execute(
            "SELECT carne, nombre_completo FROM estudiantes WHERE carne = ?",
            (carne,),
        ).fetchone()

        if estudiante is None:
            return (
                False,
                f"El carné {carne} no corresponde a ningún estudiante registrado.",
                [],
            )

        filas = conexion.execute(
            _SELECT_DETALLE + " WHERE r.carne = ? COLLATE NOCASE" + _ORDEN_DETALLE,
            (estudiante[0],),
        ).fetchall()

        if not filas:
            return (
                True,
                f"El estudiante {estudiante[1]} ({estudiante[0]}) no posee reservaciones.",
                [],
            )

        if len(filas) == 1:
            resumen = "Se encontró 1 reservación"
        else:
            resumen = f"Se encontraron {len(filas)} reservaciones"

        return True, f"{resumen} de {estudiante[1]} ({estudiante[0]}).", filas

    except sqlite3.Error:
        return False, "No fue posible buscar las reservaciones del estudiante.", []

    finally:
        if conexion is not None:
            conexion.close()
