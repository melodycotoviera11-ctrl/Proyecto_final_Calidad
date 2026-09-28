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
"""

from datetime import timedelta
from uuid import uuid4

from database.conexion import obtener_conexion
from reservaciones import validaciones as v
from reservaciones.gestion_reservaciones import insertar_reservacion
from reservaciones.reglas import validar_reservacion


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
    Si una sola ocurrencia es inválida o presenta un conflicto,
    ninguna reservación de la serie queda almacenada.

    Args:
        carne: carné del estudiante.
        codigo_sala: código de la sala.
        fecha_inicio: fecha de inicio de la serie.
        hora_inicio: hora inicial.
        duracion: duración de cada reservación.
        cantidad_personas: cantidad de personas.
        cantidad_ocurrencias: cantidad de reservaciones de la serie.
        ahora: fecha/hora de referencia opcional para las pruebas.

    Returns:
        dict: identificador de la serie y los IDs de las reservaciones creadas.

    Raises:
        ValueError: si alguna ocurrencia incumple una regla de negocio.
        Exception: si ocurre un error durante la transacción.
    """
    fechas = generar_fechas_semanales(
        fecha_inicio,
        cantidad_ocurrencias,
    )

    conexion = obtener_conexion()

    try:
        conexion.execute("BEGIN IMMEDIATE")

        serie_id = str(uuid4())

        datos_validados = []

        # Primero se validan TODAS las ocurrencias.
        for fecha in fechas:
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

        # Solo si todas las ocurrencias son válidas se insertan.
        ids_reservaciones = []

        for datos in datos_validados:
            id_reservacion = insertar_reservacion(
                conexion,
                datos,
                serie_id=serie_id,
            )

            ids_reservaciones.append(id_reservacion)

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