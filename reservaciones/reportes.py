"""
Lógica para generar reportes de reservaciones en formato CSV.

RF-16:
- Permite consultar reservaciones dentro de un rango de fechas.
- Genera un archivo CSV con encabezados identificables.
- Utiliza codificación UTF-8 para conservar tildes y ñ.
- No crea ningún archivo si el destino no fue seleccionado.
"""

import csv
from pathlib import Path

from reservaciones.gestion_reservaciones import (
    COLUMNAS_RESERVACION,
    consultar_reservaciones,
)
from reservaciones.validaciones import validar_fecha


ENCABEZADOS_REPORTE = (
    "ID",
    "Carné",
    "Estudiante",
    "Código de sala",
    "Sala",
    "Fecha",
    "Hora inicio",
    "Hora fin",
    "Cantidad de personas",
    "Estado",
)


def consultar_reservaciones_por_fecha(fecha_inicial, fecha_final):
    """
    RF-16. Consulta las reservaciones comprendidas en un rango de fechas.

    Las fechas son obligatorias, deben tener formato AAAA-MM-DD y
    la fecha final no puede ser anterior a la fecha inicial.

    Devuelve:
        (True, mensaje, filas) si el rango es válido.
        (False, mensaje, []) si existe algún error de validación.
    """
    try:
        fecha_inicio = validar_fecha(fecha_inicial)
        fecha_fin = validar_fecha(fecha_final)
    except ValueError as error:
        return False, str(error), []

    if fecha_fin < fecha_inicio:
        return (
            False,
            "La fecha final no puede ser anterior a la fecha inicial.",
            [],
        )

    try:
        filas = consultar_reservaciones()
    except RuntimeError as error:
        return False, str(error), []

    filas_rango = [
        fila
        for fila in filas
        if fecha_inicio <= validar_fecha(fila[5]) <= fecha_fin
    ]

    return True, f"Se encontraron {len(filas_rango)} reservaciones.", filas_rango


def generar_reporte_csv(fecha_inicial, fecha_final, ruta_destino):
    """
    RF-16. Genera el reporte de reservaciones en formato CSV.

    El archivo utiliza UTF-8 con BOM para facilitar su apertura en
    aplicaciones como Microsoft Excel y conservar correctamente
    caracteres como tildes y ñ.

    Si ruta_destino es None o está vacío, no se crea ningún archivo.

    Devuelve:
        (True, mensaje) si el reporte fue generado correctamente.
        (False, mensaje) si no pudo generarse.
    """
    if not ruta_destino:
        return False, "No se seleccionó un archivo de destino."

    exito, mensaje, filas = consultar_reservaciones_por_fecha(
        fecha_inicial,
        fecha_final,
    )

    if not exito:
        return False, mensaje

    ruta = Path(ruta_destino)

    try:
        with ruta.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as archivo:
            escritor = csv.writer(archivo)

            escritor.writerow(ENCABEZADOS_REPORTE)

            for fila in filas:
                escritor.writerow(fila)

    except OSError:
        return (
            False,
            "No fue posible generar el reporte en la ubicación seleccionada.",
        )

    return True, f"Reporte generado correctamente: {ruta}"