import csv
import tempfile
import unittest
from pathlib import Path

from reservaciones.reportes import (
    consultar_reservaciones_por_fecha,
    generar_reporte_csv,
)


class TestConsultarReservacionesPorFecha(unittest.TestCase):

    def test_fecha_inicial_invalida(self):
        exito, mensaje, filas = consultar_reservaciones_por_fecha(
            "2026-99-99",
            "2026-10-20",
        )

        self.assertFalse(exito)
        self.assertIn("no existe", mensaje.lower())
        self.assertEqual(filas, [])

    def test_fecha_final_invalida(self):
        exito, mensaje, filas = consultar_reservaciones_por_fecha(
            "2026-10-01",
            "fecha-invalida",
        )

        self.assertFalse(exito)
        self.assertEqual(filas, [])

    def test_fecha_final_anterior(self):
        exito, mensaje, filas = consultar_reservaciones_por_fecha(
            "2026-10-20",
            "2026-10-01",
        )

        self.assertFalse(exito)
        self.assertIn(
            "fecha final no puede ser anterior",
            mensaje.lower(),
        )
        self.assertEqual(filas, [])

    def test_rango_valido(self):
        exito, mensaje, filas = consultar_reservaciones_por_fecha(
            "2026-10-01",
            "2026-10-31",
        )

        self.assertTrue(exito)
        self.assertIsInstance(filas, list)


class TestGenerarReporteCSV(unittest.TestCase):

    def test_no_genera_si_no_hay_ruta(self):
        exito, mensaje = generar_reporte_csv(
            "2026-10-01",
            "2026-10-31",
            None,
        )

        self.assertFalse(exito)
        self.assertIn("destino", mensaje.lower())

    def test_no_genera_si_rango_invalido(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "reporte.csv"

            exito, mensaje = generar_reporte_csv(
                "2026-10-31",
                "2026-10-01",
                ruta,
            )

            self.assertFalse(exito)
            self.assertFalse(ruta.exists())

    def test_genera_csv_con_encabezados(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "reporte.csv"

            exito, mensaje = generar_reporte_csv(
                "2026-10-01",
                "2026-10-31",
                ruta,
            )

            self.assertTrue(exito)
            self.assertTrue(ruta.exists())

            with ruta.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as archivo:
                lector = csv.reader(archivo)
                encabezados = next(lector)

            self.assertEqual(
                encabezados,
                [
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
                ],
            )


if __name__ == "__main__":
    unittest.main()