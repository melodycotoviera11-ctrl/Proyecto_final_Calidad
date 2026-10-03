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

def formatear_id_reservacion(id_interno):
    """
    Convierte el ID entero utilizado internamente por SQLite
    al formato público requerido: R0001, R0002, etc.
    """
    return f"R{int(id_interno):04d}"


def normalizar_id_reservacion(id_reservacion):
    """
    Convierte un ID recibido al entero utilizado internamente.

    Acepta:
        1
        "1"
        "R0001"
        "r0001"

    Devuelve:
        1
    """

    if isinstance(id_reservacion, bool):
        raise ValueError(
            "El ID de la reservación debe tener formato R0001."
        )

    if id_reservacion is None:
        raise ValueError(
            "El ID de la reservación debe tener formato R0001."
        )

    texto = str(
        id_reservacion
    ).strip().upper()

    if texto.startswith("R"):
        texto = texto[1:]

    if not texto.isdigit():
        raise ValueError(
            "El ID de la reservación debe tener formato R0001."
        )

    id_interno = int(texto)

    if id_interno <= 0:
        raise ValueError(
            "El ID de la reservación debe tener formato R0001."
        )

    return id_interno

_SELECT_DETALLE = """
    SELECT 'R' || printf('%04d', r.id),
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


def registrar_auditoria(
    conexion,
    tipo_accion,
    entidad,
    identificador,
):
    """
    Inserta un registro en la tabla auditoria usando la misma conexión,
    para que se confirme o se revierta junto con la operación (RF-17).

    Los identificadores de reservación se almacenan con formato R0001.
    """

    if entidad == "reservación":
        try:
            identificador = formatear_id_reservacion(
                normalizar_id_reservacion(
                    identificador
                )
            )

        except ValueError:
            identificador = str(
                identificador
            )

    conexion.execute(
        """
        INSERT INTO auditoria
            (fecha_hora, tipo_accion, entidad, identificador)
        VALUES (?, ?, ?, ?)
        """,
        (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            tipo_accion,
            entidad,
            str(identificador),
        ),
    )


def insertar_reservacion(
    conexion,
    datos,
    serie_id=None,
):
    """
    Inserta una reservación ya validada con estado activa.

    SQLite mantiene internamente un ID entero AUTOINCREMENT,
    mientras que la aplicación utiliza el formato público
    R0001, R0002, etc.
    """

    cursor = conexion.execute(
        """
        INSERT INTO reservaciones
            (
                carne,
                codigo_sala,
                fecha,
                hora_inicio,
                duracion,
                cantidad_personas,
                estado,
                serie_id
            )
        VALUES (?, ?, ?, ?, ?, ?, 'activa', ?)
        """,
        (
            datos["carne"],
            datos["codigo_sala"],
            v.fecha_a_texto(
                datos["fecha"]
            ),
            v.formatear_hora(
                datos["hora_inicio"]
            ),
            datos["duracion"],
            datos["cantidad_personas"],
            serie_id,
        ),
    )

    id_interno = cursor.lastrowid

    id_reservacion = formatear_id_reservacion(
        id_interno
    )

    registrar_auditoria(
        conexion,
        "creación",
        "reservación",
        id_reservacion,
    )

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

def consultar_auditoria():
    """
    RF-17. Consulta el historial de auditoría.

    Devuelve los registros ordenados del más reciente
    al más antiguo.

    Cada fila contiene:
        id,
        fecha_hora,
        tipo_accion,
        entidad,
        identificador.
    """

    conexion = None

    try:
        conexion = obtener_conexion()

        return conexion.execute(
            """
            SELECT
                id,
                fecha_hora,
                tipo_accion,
                entidad,
                identificador
            FROM auditoria
            ORDER BY id DESC
            """
        ).fetchall()

    except sqlite3.Error as error:

        raise RuntimeError(
            "No fue posible consultar el historial de auditoría."
        ) from error

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


def cancelar_reservacion(id_reservacion):
    """
    RF-09. Cancela una reservación activa mediante su ID.

    La aplicación utiliza identificadores con formato R0001,
    mientras SQLite conserva internamente el número entero.
    """

    try:
        id_interno = normalizar_id_reservacion(
            id_reservacion
        )

        id_publico = formatear_id_reservacion(
            id_interno
        )

    except ValueError as error:
        return (
            False,
            str(error),
            None,
        )

    conexion = None

    try:
        conexion = obtener_conexion()

        conexion.execute(
            "BEGIN IMMEDIATE"
        )

        try:
            reservacion = conexion.execute(
                """
                SELECT id, estado
                FROM reservaciones
                WHERE id = ?
                """,
                (id_interno,),
            ).fetchone()

            if reservacion is None:
                conexion.rollback()

                return (
                    False,
                    (
                        "No existe una reservación "
                        f"con el ID {id_publico}."
                    ),
                    None,
                )

            if reservacion[1] == "cancelada":
                conexion.rollback()

                return (
                    False,
                    (
                        f"La reservación con ID {id_publico} "
                        "ya se encuentra cancelada."
                    ),
                    None,
                )

            conexion.execute(
                """
                UPDATE reservaciones
                SET estado = 'cancelada'
                WHERE id = ?
                """,
                (id_interno,),
            )

            registrar_auditoria(
                conexion,
                "cancelación",
                "reservación",
                id_publico,
            )

            conexion.commit()

        except Exception:
            conexion.rollback()
            raise

        return (
            True,
            (
                f"La reservación con ID {id_publico} "
                "se canceló correctamente."
            ),
            id_publico,
        )

    except sqlite3.Error:
        return (
            False,
            (
                "No fue posible cancelar la reservación. "
                "Intente de nuevo."
            ),
            None,
        )

    finally:
        if conexion is not None:
            conexion.close()

def modificar_reservacion(
    id_reservacion,
    codigo_sala,
    fecha,
    hora_inicio,
    duracion,
    cantidad_personas,
    ahora=None,
):
    """
    RF-13. Modifica una reservación activa.

    Se pueden modificar la sala, fecha, hora de inicio,
    duración y cantidad de personas.

    El ID y el estudiante permanecen sin cambios.
    """

    try:
        id_interno = normalizar_id_reservacion(
            id_reservacion
        )

        id_publico = formatear_id_reservacion(
            id_interno
        )

    except ValueError as error:
        return (
            False,
            str(error),
            None,
        )

    conexion = None

    try:
        conexion = obtener_conexion()

        conexion.execute(
            "BEGIN IMMEDIATE"
        )

        try:
            reservacion = conexion.execute(
                """
                SELECT id, carne, estado
                FROM reservaciones
                WHERE id = ?
                """,
                (id_interno,),
            ).fetchone()

            if reservacion is None:
                conexion.rollback()

                return (
                    False,
                    (
                        "No existe una reservación "
                        f"con el ID {id_publico}."
                    ),
                    None,
                )

            if reservacion[2] != "activa":
                conexion.rollback()

                return (
                    False,
                    (
                        f"La reservación con ID {id_publico} "
                        "está cancelada y no puede modificarse."
                    ),
                    None,
                )

            carne = reservacion[1]

            datos = validar_reservacion(
                conexion,
                carne,
                codigo_sala,
                fecha,
                hora_inicio,
                duracion,
                cantidad_personas,
                ahora,
                excluir_id=id_interno,
            )

            conexion.execute(
                """
                UPDATE reservaciones
                SET codigo_sala = ?,
                    fecha = ?,
                    hora_inicio = ?,
                    duracion = ?,
                    cantidad_personas = ?
                WHERE id = ?
                """,
                (
                    datos["codigo_sala"],
                    v.fecha_a_texto(
                        datos["fecha"]
                    ),
                    v.formatear_hora(
                        datos["hora_inicio"]
                    ),
                    datos["duracion"],
                    datos["cantidad_personas"],
                    id_interno,
                ),
            )

            registrar_auditoria(
                conexion,
                "modificación",
                "reservación",
                id_publico,
            )

            conexion.commit()

        except Exception:
            conexion.rollback()
            raise

        return (
            True,
            (
                f"La reservación con ID {id_publico} "
                "se modificó correctamente."
            ),
            id_publico,
        )

    except ValueError as error:
        return (
            False,
            str(error),
            None,
        )

    except sqlite3.Error:
        return (
            False,
            (
                "No fue posible modificar la reservación. "
                "Intente de nuevo."
            ),
            None,
        )

    finally:
        if conexion is not None:
            conexion.close()