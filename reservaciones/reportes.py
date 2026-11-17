"""
Lógica para generar reportes de reservaciones en formato CSV.

RF-16:
- Permite consultar reservaciones dentro de un rango de fechas.
- Genera un archivo CSV con encabezados identificables.
- Utiliza codificación UTF-8 con BOM para conservar tildes y ñ y
  facilitar su apertura en Microsoft Excel.
- No crea ningún archivo si el destino no fue seleccionado.
- Neutraliza los textos que una hoja de cálculo podría interpretar
  como fórmula (corrección del hallazgo H-14, Fase 3, Grupo 07).
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

# H-14: caracteres con los que una hoja de cálculo inicia una fórmula.
# Se incluyen el tabulador y el retorno de carro, que algunas
# aplicaciones descartan antes de evaluar la celda.
PREFIJOS_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def neutralizar_celda(valor):
    """
    H-14. Antepone un apóstrofo a los textos que comienzan con un
    símbolo de fórmula, para que la hoja de cálculo los muestre como
    texto y no los evalúe. Los números y los demás textos no cambian.
    """
    if isinstance(valor, str) and valor.startswith(PREFIJOS_FORMULA):
        return "'" + valor

    return valor


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
                escritor.writerow(
                    [neutralizar_celda(valor) for valor in fila]
                )

    except OSError:
        return (
            False,
            "No fue posible generar el reporte en la ubicación seleccionada.",
        )

    return True, f"Reporte generado correctamente: {ruta}"