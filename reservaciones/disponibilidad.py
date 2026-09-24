"""
RF-08. Consultar disponibilidad de una sala.

La consulta es de solo lectura: no crea, modifica ni elimina registros.
Reglas aplicadas: RN-02, RN-03, RN-04, RN-05, RN-06, RN-08, RN-09,
RN-10 y RN-12 (las canceladas no bloquean horarios).
"""

import sqlite3
from datetime import datetime

from database.conexion import obtener_conexion
from reservaciones import validaciones as v
from reservaciones.reglas import buscar_conflictos, describir_conflictos, obtener_sala


def consultar_disponibilidad(codigo_sala, fecha, hora_inicio, duracion, ahora=None):
    """
    Devuelve (exito, mensaje, disponible):
        - datos inválidos o sala inexistente -> (False, motivo, None)
        - sala fuera de servicio             -> (True, motivo, False)
        - conflicto con reservación activa   -> (True, detalle, False)
        - sin conflicto                      -> (True, confirmación, True)
    """
    if ahora is None:
        ahora = datetime.now()

    try:
        datos = v.validar_datos_de_horario(
            codigo_sala, fecha, hora_inicio, duracion, ahora,
        )
    except ValueError as error:
        return False, str(error), None

    conexion = None

    try:
        conexion = obtener_conexion()

        try:
            sala = obtener_sala(conexion, datos["codigo_sala"])
        except ValueError as error:
            return False, str(error), None

        if sala["estado"] != "disponible":
            return (
                True,
                f"La sala {sala['codigo']} no está disponible: se encuentra "
                "fuera de servicio.",
                False,
            )

        conflictos = buscar_conflictos(
            conexion, sala["codigo"], datos["fecha"],
            datos["hora_inicio"], datos["duracion"],
        )

        if conflictos:
            return (
                True,
                "No disponible. "
                + describir_conflictos(sala["codigo"], datos["fecha"], conflictos),
                False,
            )

        return (
            True,
            f"La sala {sala['codigo']} ({sala['nombre']}, capacidad "
            f"{sala['capacidad']}) está disponible el "
            f"{v.fecha_a_texto(datos['fecha'])} de "
            f"{v.formatear_hora(datos['hora_inicio'])} a "
            f"{v.formatear_hora(datos['hora_inicio'] + datos['duracion'])}.",
            True,
        )

    except sqlite3.Error:
        return False, "No fue posible consultar la disponibilidad de la sala.", None

    finally:
        if conexion is not None:
            conexion.close()
