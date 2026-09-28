"""
Lógica para la gestión de reservaciones recurrentes (RF-14).
"""

from datetime import timedelta

from reservaciones import validaciones as v


MINIMO_OCURRENCIAS = 2
MAXIMO_OCURRENCIAS = 8


def validar_cantidad_ocurrencias(cantidad):
    """
    Valida que la cantidad de ocurrencias esté entre 2 y 8.

    Retorna la cantidad como entero si es válida.
    Lanza ValueError si no es válida.
    """
    if isinstance(cantidad, bool):
        raise ValueError(
            "La cantidad de ocurrencias debe ser un número entero entre 2 y 8."
        )

    try:
        cantidad = int(str(cantidad).strip())
    except (TypeError, ValueError) as error:
        raise ValueError(
            "La cantidad de ocurrencias debe ser un número entero entre 2 y 8."
        ) from error

    if not MINIMO_OCURRENCIAS <= cantidad <= MAXIMO_OCURRENCIAS:
        raise ValueError(
            "La cantidad de ocurrencias debe estar entre 2 y 8."
        )

    return cantidad


def generar_fechas_semanales(fecha_inicial, cantidad):
    """
    Genera las fechas de una serie semanal.

    La primera ocurrencia corresponde a fecha_inicial.
    Cada ocurrencia posterior se encuentra exactamente 7 días
    después de la anterior.
    """
    cantidad = validar_cantidad_ocurrencias(cantidad)

    fecha = v.validar_fecha(fecha_inicial)

    return [
        fecha + timedelta(weeks=i)
        for i in range(cantidad)
    ]