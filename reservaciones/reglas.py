"""
Reglas de negocio de reservaciones que requieren consultar la base de datos.

Todas las funciones reciben una conexión abierta, de modo que la
validación y la escritura puedan ocurrir dentro de la misma transacción
(RNF-06). No abren ventanas ni muestran mensajes (RNF-07 / RNF-10).

Reglas cubiertas: RN-01, RN-07, RN-08, RN-09, RN-10 y RN-11.

Uso previsto por otros módulos:
    - RF-13 (modificar): validar_reservacion(..., excluir_id=id_original)
    - RF-14 (recurrencia): validar_reservacion(...) por cada ocurrencia
"""

from datetime import datetime

from reservaciones import validaciones as v

MAXIMO_RESERVACIONES_VIGENTES = 3


def obtener_estudiante_activo(conexion, carne):
    """RN-01: solamente un estudiante registrado y activo puede reservar."""
    fila = conexion.execute(
        """
        SELECT carne, nombre_completo, estado
        FROM estudiantes
        WHERE carne = ?
        """,
        (carne,),
    ).fetchone()

    if fila is None:
        raise ValueError(
            f"El carné {carne} no corresponde a ningún estudiante registrado."
        )

    if fila[2] != "activo":
        raise ValueError(
            f"El estudiante con carné {fila[0]} está inactivo y no puede "
            "crear reservaciones."
        )

    return {"carne": fila[0], "nombre": fila[1]}


def obtener_sala(conexion, codigo_sala):
    """Devuelve la sala (sin importar su estado) o lanza ValueError si no existe."""
    fila = conexion.execute(
        """
        SELECT codigo, nombre, capacidad, estado
        FROM salas
        WHERE codigo = ? COLLATE NOCASE
        """,
        (codigo_sala,),
    ).fetchone()

    if fila is None:
        raise ValueError(f"La sala {codigo_sala} no existe.")

    return {
        "codigo": fila[0],
        "nombre": fila[1],
        "capacidad": fila[2],
        "estado": fila[3],
    }


def obtener_sala_disponible(conexion, codigo_sala):
    """RN-08: una sala fuera de servicio no puede reservarse."""
    sala = obtener_sala(conexion, codigo_sala)

    if sala["estado"] != "disponible":
        raise ValueError(
            f"La sala {sala['codigo']} se encuentra fuera de servicio y no "
            "puede reservarse."
        )

    return sala


def buscar_conflictos(conexion, codigo_sala, fecha, hora_inicio, duracion,
                      excluir_id=None):
    """
    RN-09 / RN-10 / RN-12: devuelve las reservaciones ACTIVAS de la sala y
    fecha indicadas que se superponen con el intervalo solicitado.
    Las canceladas no bloquean horarios.
    """
    filas = conexion.execute(
        """
        SELECT id, hora_inicio, duracion
        FROM reservaciones
        WHERE codigo_sala = ? COLLATE NOCASE
          AND fecha = ?
          AND estado = 'activa'
          AND (? IS NULL OR id <> ?)
        ORDER BY hora_inicio
        """,
        (codigo_sala, v.fecha_a_texto(fecha), excluir_id, excluir_id),
    ).fetchall()

    conflictos = []

    for id_reservacion, hora_texto, duracion_existente in filas:
        inicio_existente = int(hora_texto[:2])

        if v.hay_superposicion(hora_inicio, duracion,
                               inicio_existente, duracion_existente):
            conflictos.append({
                "id": id_reservacion,
                "hora_inicio": v.formatear_hora(inicio_existente),
                "hora_fin": v.formatear_hora(inicio_existente + duracion_existente),
            })

    return conflictos


def contar_reservaciones_vigentes(conexion, carne, ahora, excluir_id=None):
    """
    RN-11: cuenta las reservaciones activas presentes o futuras del
    estudiante, es decir, aquellas que todavía no han finalizado.
    """
    hoy = ahora.date().isoformat()
    minutos_actuales = ahora.hour * 60 + ahora.minute

    fila = conexion.execute(
        """
        SELECT COUNT(*)
        FROM reservaciones
        WHERE carne = ? COLLATE NOCASE
          AND estado = 'activa'
          AND (? IS NULL OR id <> ?)
          AND (
                fecha > ?
                OR (fecha = ?
                    AND (CAST(substr(hora_inicio, 1, 2) AS INTEGER) + duracion) * 60 > ?)
              )
        """,
        (carne, excluir_id, excluir_id, hoy, hoy, minutos_actuales),
    ).fetchone()

    return fila[0]


def describir_conflictos(codigo_sala, fecha, conflictos):
    detalle = ", ".join(
        f"{c['hora_inicio']} a {c['hora_fin']} (ID {c['id']})" for c in conflictos
    )
    return (
        f"La sala {codigo_sala} ya tiene una reservación activa el "
        f"{v.fecha_a_texto(fecha)} que se superpone con el horario solicitado: "
        f"{detalle}."
    )


def validar_reservacion(conexion, carne, codigo_sala, fecha, hora_inicio,
                        duracion, cantidad_personas, ahora=None, excluir_id=None):
    """
    Aplica TODAS las reglas de negocio de una reservación (RN-01 a RN-11).

    Devuelve un diccionario con los datos normalizados listos para
    almacenarse o lanza ValueError con el motivo del rechazo.

    `ahora` permite fijar la fecha y hora del sistema en las pruebas.
    `excluir_id` permite reutilizar la validación al modificar una
    reservación existente (RF-13) sin que choque consigo misma.
    """
    if ahora is None:
        ahora = datetime.now()

    datos = v.validar_datos_basicos(
        carne, codigo_sala, fecha, hora_inicio, duracion,
        cantidad_personas, ahora,
    )

    estudiante = obtener_estudiante_activo(conexion, datos["carne"])
    sala = obtener_sala_disponible(conexion, datos["codigo_sala"])

    # Se usan los valores tal como están registrados en la base de datos.
    datos["carne"] = estudiante["carne"]
    datos["codigo_sala"] = sala["codigo"]

    v.validar_capacidad(datos["cantidad_personas"], sala["capacidad"], sala["codigo"])

    conflictos = buscar_conflictos(
        conexion, sala["codigo"], datos["fecha"], datos["hora_inicio"],
        datos["duracion"], excluir_id,
    )

    if conflictos:
        raise ValueError(describir_conflictos(sala["codigo"], datos["fecha"], conflictos))

    vigentes = contar_reservaciones_vigentes(
        conexion, estudiante["carne"], ahora, excluir_id,
    )

    if vigentes >= MAXIMO_RESERVACIONES_VIGENTES:
        raise ValueError(
            f"El estudiante con carné {estudiante['carne']} ya tiene "
            f"{MAXIMO_RESERVACIONES_VIGENTES} reservaciones activas presentes o "
            "futuras, que es el máximo permitido."
        )

    return datos
