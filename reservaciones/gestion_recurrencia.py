"""
Lógica de negocio para RF-14: reservaciones recurrentes.

La interfaz no accede directamente a SQLite. Este módulo coordina:
    - Validación de la cantidad de ocurrencias.
    - Generación de fechas semanales.
    - Validación de cada ocurrencia.
    - Creación transaccional de toda la serie.
    - Asociación de las reservaciones mediante serie_id.

La lógica de validación y persistencia se reutiliza desde los módulos
existentes del proyecto.

Fase 6 (Grupo 4):
    - H-03: previsualizar_serie_recurrente() evalúa la serie completa sin
      guardar nada, para mostrar el resumen de conflictos y pedir
      confirmación antes de crearla. La creación usa la misma evaluación,
      por lo que la previsualización y el resultado real no pueden diferir.
    - H-09: cancelar_serie_desde_ocurrencia() cancela la ocurrencia
      seleccionada y las posteriores de su serie; antes se cancelaba desde
      la fecha actual sin considerar la ocurrencia elegida.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

from database.conexion import obtener_conexion
from reservaciones import validaciones as v
from reservaciones.gestion_reservaciones import (
    insertar_reservacion,
    normalizar_id_reservacion,
    registrar_auditoria,
)

from reservaciones.reglas import (
    MAXIMO_RESERVACIONES_VIGENTES,
    contar_reservaciones_vigentes,
    validar_reservacion,
)

MINIMO_OCURRENCIAS = 2
MAXIMO_OCURRENCIAS = 8


def validar_cantidad_ocurrencias(cantidad):
    """
    Valida que la cantidad de ocurrencias de una serie esté entre 2 y 8.

    Returns:
        int: cantidad normalizada.

    Raises:
        ValueError: si la cantidad no es un entero entre 2 y 8.
    """
    if isinstance(cantidad, bool):
        raise ValueError(
            "La cantidad de ocurrencias debe ser un número entero entre 2 y 8."
        )

    try:
        cantidad = int(str(cantidad).strip())
    except (ValueError, TypeError):
        raise ValueError(
            "La cantidad de ocurrencias debe ser un número entero entre 2 y 8."
        ) from None

    if cantidad < MINIMO_OCURRENCIAS or cantidad > MAXIMO_OCURRENCIAS:
        raise ValueError(
            "La cantidad de ocurrencias debe estar entre 2 y 8."
        )

    return cantidad


def generar_fechas_semanales(fecha_inicio, cantidad):
    """
    Genera las fechas de una serie con frecuencia semanal.

    La primera fecha corresponde a la fecha de inicio y cada ocurrencia
    posterior se encuentra exactamente 7 días después.

    Args:
        fecha_inicio: fecha inicial en formato AAAA-MM-DD.
        cantidad: cantidad de ocurrencias.

    Returns:
        list[date]: lista de fechas de la serie.

    Raises:
        ValueError: si la cantidad no está entre 2 y 8 o la fecha
                    inicial es inválida.
    """
    cantidad = validar_cantidad_ocurrencias(cantidad)

    fecha = v.validar_fecha(fecha_inicio)

    return [
        fecha + timedelta(weeks=i)
        for i in range(cantidad)
    ]


def _evaluar_serie(
    conexion,
    carne,
    codigo_sala,
    fechas,
    hora_inicio,
    duracion,
    cantidad_personas,
    ahora,
):
    """
    Evalúa todas las ocurrencias de una serie sin escribir en la base.

    Compartida por la previsualización (H-03) y por la creación, de modo
    que ambas apliquen exactamente las mismas reglas (RN-01 a RN-11).

    Returns:
        tuple: (datos_validados, ocurrencias, conflictos)
            datos_validados: datos normalizados de las ocurrencias válidas.
            ocurrencias: una entrada por fecha con número, fecha, horario,
                         estado ("disponible" o "conflicto") y motivo.
            conflictos: textos "AAAA-MM-DD: motivo" y, si corresponde, el
                        incumplimiento del límite de RN-11 para la serie.
    """

    datos_validados = []
    ocurrencias = []
    conflictos = []

    # Revisar todas las ocurrencias antes de guardar.
    for numero, fecha in enumerate(fechas, start=1):
        try:
            datos = validar_reservacion(
                conexion=conexion,
                carne=carne,
                codigo_sala=codigo_sala,
                fecha=fecha,
                hora_inicio=hora_inicio,
                duracion=duracion,
                cantidad_personas=cantidad_personas,
                ahora=ahora,
            )

            datos_validados.append(datos)

            ocurrencias.append({
                "numero": numero,
                "fecha": fecha.isoformat(),
                "hora_inicio": v.formatear_hora(datos["hora_inicio"]),
                "hora_fin": v.formatear_hora(
                    datos["hora_inicio"] + datos["duracion"]
                ),
                "estado": "disponible",
                "motivo": "",
            })

        except ValueError as error:
            conflictos.append(
                f"{fecha.isoformat()}: {error}"
            )

            ocurrencias.append({
                "numero": numero,
                "fecha": fecha.isoformat(),
                "hora_inicio": str(hora_inicio).strip(),
                "hora_fin": "",
                "estado": "conflicto",
                "motivo": str(error),
            })

    # RN-11:
    # También se deben contar las nuevas reservaciones de esta serie.
    #
    # Antes este control no funcionaba porque todas las ocurrencias
    # se validaban antes de insertar alguna, por lo que cada una veía
    # únicamente las reservaciones que ya existían en la BD.
    if not conflictos and datos_validados:

        referencia = (
            ahora
            if ahora is not None
            else datetime.now()
        )

        vigentes = contar_reservaciones_vigentes(
            conexion,
            datos_validados[0]["carne"],
            referencia,
        )

        total_resultante = (
            vigentes
            + len(datos_validados)
        )

        if (
            total_resultante
            > MAXIMO_RESERVACIONES_VIGENTES
        ):
            conflictos.append(
                "Límite de reservaciones: el estudiante ya tiene "
                f"{vigentes} reservaciones activas presentes o futuras "
                f"y la serie agregaría {len(datos_validados)}. "
                f"El máximo permitido es "
                f"{MAXIMO_RESERVACIONES_VIGENTES}."
            )

    return datos_validados, ocurrencias, conflictos


def _mensaje_conflictos(conflictos):
    """Texto único con el resumen de conflictos de una serie."""

    detalle = "\n- ".join(
        conflictos
    )

    return (
        "Se encontraron conflictos en la serie recurrente.\n- "
        + detalle
    )


def previsualizar_serie_recurrente(
    carne,
    codigo_sala,
    fecha_inicio,
    hora_inicio,
    duracion,
    cantidad_personas,
    cantidad_ocurrencias,
    ahora=None,
):
    """
    RF-14 / H-03: evalúa la serie completa sin guardar nada.

    Permite mostrar, antes de crear la serie, cada ocurrencia con su
    fecha, su horario y si está disponible o presenta conflicto, junto
    con el resumen de conflictos. No inicia transacciones de escritura,
    no inserta reservaciones y no registra auditoría.

    Returns:
        dict con las claves:
            ocurrencias: lista de ocurrencias (ver _evaluar_serie).
            total: cantidad de ocurrencias de la serie.
            validas: cantidad de ocurrencias sin conflicto.
            conflictos: lista de textos de conflicto (vacía si no hay).
            puede_confirmar: True solo si la serie completa es válida.
            resumen: texto breve para la persona usuaria.

    Raises:
        ValueError: si la cantidad de ocurrencias o la fecha inicial
                    no son válidas (no es posible armar la serie).
    """

    fechas = generar_fechas_semanales(
        fecha_inicio,
        cantidad_ocurrencias,
    )

    conexion = obtener_conexion()

    try:
        _, ocurrencias, conflictos = _evaluar_serie(
            conexion,
            carne,
            codigo_sala,
            fechas,
            hora_inicio,
            duracion,
            cantidad_personas,
            ahora,
        )

    finally:
        conexion.close()

    total = len(ocurrencias)

    validas = sum(
        1
        for ocurrencia in ocurrencias
        if ocurrencia["estado"] == "disponible"
    )

    puede_confirmar = not conflictos

    if puede_confirmar:
        resumen = (
            f"Las {total} ocurrencias están disponibles. "
            "Confirme para guardar la serie."
        )
    else:
        resumen = (
            "La serie no puede guardarse: "
            f"{len(conflictos)} conflicto(s) detectado(s). "
            "Corrija los datos y vuelva a intentarlo."
        )

    return {
        "ocurrencias": ocurrencias,
        "total": total,
        "validas": validas,
        "conflictos": conflictos,
        "puede_confirmar": puede_confirmar,
        "resumen": resumen,
    }


def crear_reservacion_recurrente(
    carne,
    codigo_sala,
    fecha_inicio,
    hora_inicio,
    duracion,
    cantidad_personas,
    cantidad_ocurrencias,
    ahora=None,
):
    """
    RF-14: crea una serie de reservaciones semanales.

    Todas las ocurrencias se validan antes de confirmar la transacción.
    Si una o más ocurrencias presentan conflictos, se informa un resumen
    completo y ninguna reservación de la serie queda almacenada.
    """

    fechas = generar_fechas_semanales(
        fecha_inicio,
        cantidad_ocurrencias,
    )

    conexion = obtener_conexion()

    try:
        conexion.execute("BEGIN IMMEDIATE")

        serie_id = str(uuid4())

        datos_validados, _, conflictos = _evaluar_serie(
            conexion,
            carne,
            codigo_sala,
            fechas,
            hora_inicio,
            duracion,
            cantidad_personas,
            ahora,
        )

        # Si existe cualquier conflicto, no se guarda nada.
        if conflictos:
            raise ValueError(
                _mensaje_conflictos(conflictos)
            )

        # Solo si toda la serie es válida se almacena.
        ids_reservaciones = []

        for datos in datos_validados:

            id_reservacion = insertar_reservacion(
                conexion,
                datos,
                serie_id=serie_id,
            )

            ids_reservaciones.append(
                id_reservacion
            )

        conexion.commit()

        return {
            "serie_id": serie_id,
            "ids": ids_reservaciones,
        }

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def obtener_serie_id(id_reservacion):
    """
    Obtiene el identificador de la serie recurrente
    a la que pertenece una reservación.
    """

    try:
        id_interno = normalizar_id_reservacion(
            id_reservacion
        )

    except ValueError:
        return None

    conexion = obtener_conexion()

    try:
        fila = conexion.execute(
            """
            SELECT serie_id
            FROM reservaciones
            WHERE id = ?
            """,
            (id_interno,),
        ).fetchone()

        if fila is None:
            return None

        return fila[0]

    finally:
        conexion.close()


def cancelar_ocurrencias_futuras(
    serie_id,
    fecha_desde=None,
):
    """
    RF-14.

    Cancela todas las ocurrencias activas de una serie recurrente
    cuya fecha sea igual o posterior a fecha_desde.

    Cada cancelación queda registrada en auditoría.

    Args:
        serie_id: identificador de la serie recurrente.
        fecha_desde: fecha a partir de la cual se cancelan
                     las ocurrencias. Si no se indica, se utiliza
                     la fecha actual.

    Returns:
        tuple:
            (True, mensaje, cantidad_cancelada)
            (False, mensaje, 0)
    """

    if not serie_id:
        return (
            False,
            "La reservación seleccionada no pertenece "
            "a una serie recurrente.",
            0,
        )

    if fecha_desde is None:
        fecha_desde = date.today().isoformat()

    try:
        fecha_desde = v.fecha_a_texto(
            v.validar_fecha(fecha_desde)
        )
    except ValueError:
        return (
            False,
            "La fecha indicada no es válida.",
            0,
        )

    conexion = None

    try:
        conexion = obtener_conexion()

        conexion.execute(
            "BEGIN IMMEDIATE"
        )

        ocurrencias = conexion.execute(
            """
            SELECT id
            FROM reservaciones
            WHERE serie_id = ?
              AND fecha >= ?
              AND estado = 'activa'
            ORDER BY fecha ASC, hora_inicio ASC, id ASC
            """,
            (
                serie_id,
                fecha_desde,
            ),
        ).fetchall()

        if not ocurrencias:
            conexion.rollback()

            return (
                False,
                "No existen ocurrencias futuras activas "
                "para cancelar en esta serie.",
                0,
            )

        ids = [
            fila[0]
            for fila in ocurrencias
        ]

        for id_reservacion in ids:

            conexion.execute(
                """
                UPDATE reservaciones
                SET estado = 'cancelada'
                WHERE id = ?
                """,
                (id_reservacion,),
            )

            registrar_auditoria(
                conexion,
                "cancelación",
                "reservación",
                id_reservacion,
            )

        conexion.commit()

        cantidad = len(ids)

        return (
            True,
            (
                f"Se cancelaron {cantidad} ocurrencias "
                "futuras de la serie."
            ),
            cantidad,
        )

    except Exception:
        if conexion is not None:
            conexion.rollback()

        return (
            False,
            "No fue posible cancelar las ocurrencias futuras.",
            0,
        )

    finally:
        if conexion is not None:
            conexion.close()

def obtener_ocurrencia(id_reservacion):
    """
    H-09: devuelve los datos de la ocurrencia seleccionada.

    Returns:
        dict con serie_id, fecha (AAAA-MM-DD), estado e id público
        (R0001), o None si el ID no es válido o no existe.
    """

    try:
        id_interno = normalizar_id_reservacion(
            id_reservacion
        )

    except ValueError:
        return None

    conexion = obtener_conexion()

    try:
        fila = conexion.execute(
            """
            SELECT id, serie_id, fecha, estado
            FROM reservaciones
            WHERE id = ?
            """,
            (id_interno,),
        ).fetchone()

    finally:
        conexion.close()

    if fila is None:
        return None

    return {
        "id": f"R{fila[0]:04d}",
        "serie_id": fila[1],
        "fecha": fila[2],
        "estado": fila[3],
    }


def _fecha_desde_cancelacion(fecha_ocurrencia, ahora=None):
    """
    Fecha a partir de la cual se cancela: la de la ocurrencia
    seleccionada, sin tocar nunca ocurrencias anteriores a hoy.
    """

    referencia = (
        ahora
        if ahora is not None
        else datetime.now()
    )

    return max(
        fecha_ocurrencia,
        referencia.date().isoformat(),
    )


def previsualizar_cancelacion_desde_ocurrencia(
    id_reservacion,
    ahora=None,
):
    """
    H-09: indica qué ocurrencias se cancelarían, sin modificar nada.

    Incluye la ocurrencia seleccionada y las posteriores activas de su
    serie. Las anteriores no se consideran.

    Returns:
        dict con serie_id, desde (fecha) y ocurrencias (lista de
        {"id", "fecha"}). Si la reservación no existe o no pertenece a
        una serie, devuelve None.
    """

    ocurrencia = obtener_ocurrencia(
        id_reservacion
    )

    if ocurrencia is None or not ocurrencia["serie_id"]:
        return None

    desde = _fecha_desde_cancelacion(
        ocurrencia["fecha"],
        ahora,
    )

    conexion = obtener_conexion()

    try:
        filas = conexion.execute(
            """
            SELECT id, fecha
            FROM reservaciones
            WHERE serie_id = ?
              AND fecha >= ?
              AND estado = 'activa'
            ORDER BY fecha ASC, hora_inicio ASC, id ASC
            """,
            (
                ocurrencia["serie_id"],
                desde,
            ),
        ).fetchall()

    finally:
        conexion.close()

    return {
        "serie_id": ocurrencia["serie_id"],
        "desde": desde,
        "ocurrencias": [
            {
                "id": f"R{fila[0]:04d}",
                "fecha": fila[1],
            }
            for fila in filas
        ],
    }


def cancelar_serie_desde_ocurrencia(
    id_reservacion,
    ahora=None,
):
    """
    RF-14 / H-09: cancela la ocurrencia seleccionada y todas las
    posteriores de su serie.

    Las ocurrencias anteriores a la seleccionada, las ya canceladas y
    las reservaciones de otras series no se modifican. Cada cancelación
    queda en auditoría y toda la operación es atómica.

    Returns:
        tuple: (exito, mensaje, cantidad_cancelada)
    """

    ocurrencia = obtener_ocurrencia(
        id_reservacion
    )

    if ocurrencia is None:
        return (
            False,
            "No existe la reservación seleccionada.",
            0,
        )

    if not ocurrencia["serie_id"]:
        return (
            False,
            "La reservación seleccionada no pertenece "
            "a una serie recurrente.",
            0,
        )

    desde = _fecha_desde_cancelacion(
        ocurrencia["fecha"],
        ahora,
    )

    exito, mensaje, cantidad = cancelar_ocurrencias_futuras(
        ocurrencia["serie_id"],
        desde,
    )

    if not exito:
        return exito, mensaje, cantidad

    if cantidad == 1:
        mensaje = (
            "Se canceló 1 ocurrencia de la serie "
            f"a partir del {desde}."
        )

    else:
        mensaje = (
            f"Se cancelaron {cantidad} ocurrencias de la serie "
            f"a partir del {desde}."
        )

    return True, mensaje, cantidad