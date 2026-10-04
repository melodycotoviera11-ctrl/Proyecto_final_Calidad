import csv
import tempfile
import unittest
from pathlib import Path

from reservaciones.reportes import (
    consultar_reservaciones_por_fecha,
    generar_reporte_csv,
)

from tests.utilidades import (
    PruebaConBaseTemporal,
)


class TestConsultarReservacionesPorFecha(
    PruebaConBaseTemporal
):

    def test_fecha_inicial_invalida(self):
        exito, mensaje, filas = consultar_reservaciones_por_fecha(
            "2026-99-99",
            "2026-10-20",
        )

        self.assertFalse(exito)
        self.assertIn(
            "no existe",
            mensaje.lower(),
        )
        self.assertEqual(
            filas,
            [],
        )

    def test_fecha_final_invalida(self):
        exito, mensaje, filas = consultar_reservaciones_por_fecha(
            "2026-10-01",
            "fecha-invalida",
        )

        self.assertFalse(exito)
        self.assertEqual(
            filas,
            [],
        )

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

        self.assertEqual(
            filas,
            [],
        )

    def test_rango_valido(self):
        exito, mensaje, filas = consultar_reservaciones_por_fecha(
            "2026-10-01",
            "2026-10-31",
        )

        self.assertTrue(exito)

        self.assertIsInstance(
            filas,
            list,
        )


class TestGenerarReporteCSV(
    PruebaConBaseTemporal
):

    def test_no_genera_si_no_hay_ruta(self):
        exito, mensaje = generar_reporte_csv(
            "2026-10-01",
            "2026-10-31",
            None,
        )

        self.assertFalse(exito)

        self.assertIn(
            "destino",
            mensaje.lower(),
        )

    def test_no_genera_si_rango_invalido(self):
        with tempfile.TemporaryDirectory() as carpeta:

            ruta = (
                Path(carpeta)
                / "reporte.csv"
            )

            exito, mensaje = generar_reporte_csv(
                "2026-10-31",
                "2026-10-01",
                ruta,
            )

            self.assertFalse(exito)

            self.assertFalse(
                ruta.exists()
            )

    def test_genera_csv_con_encabezados(self):
        with tempfile.TemporaryDirectory() as carpeta:

            ruta = (
                Path(carpeta)
                / "reporte.csv"
            )

            exito, mensaje = generar_reporte_csv(
                "2026-10-01",
                "2026-10-31",
                ruta,
            )

            self.assertTrue(
                exito,
                mensaje,
            )

            self.assertTrue(
                ruta.exists()
            )

            with ruta.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as archivo:

                lector = csv.reader(
                    archivo
                )

                encabezados = next(
                    lector
                )

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

    def test_csv_conserva_tildes_y_enie(self):
        """
        RNF-08:
        verifica que los datos exportados con tildes
        y la letra ñ se conserven correctamente.
        """

        self.sql(
            """
            INSERT INTO estudiantes
                (
                    carne,
                    nombre_completo,
                    correo,
                    estado
                )
            VALUES (?, ?, ?, ?)
            """,
            (
                "N000000001",
                "Íñigo Muñoz",
                "inigo@universidad.ac.cr",
                "activo",
            ),
        )

        self.sql(
            """
            INSERT INTO salas
                (
                    codigo,
                    nombre,
                    capacidad,
                    estado
                )
            VALUES (?, ?, ?, ?)
            """,
            (
                "S06",
                "Sala Pequeña Ñandú",
                6,
                "disponible",
            ),
        )

        self.insertar_directo(
            "N000000001",
            "S06",
            "2026-10-10",
            "10:00",
            1,
            2,
        )

        with tempfile.TemporaryDirectory() as carpeta:

            ruta = (
                Path(carpeta)
                / "reporte_codificacion.csv"
            )

            exito, mensaje = generar_reporte_csv(
                "2026-10-10",
                "2026-10-10",
                ruta,
            )

            self.assertTrue(
                exito,
                mensaje,
            )

            self.assertTrue(
                ruta.exists()
            )

            with ruta.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as archivo:

                lector = list(
                    csv.reader(
                        archivo
                    )
                )

            self.assertEqual(
                lector[0][1],
                "Carné",
            )

            self.assertEqual(
                lector[0][3],
                "Código de sala",
            )

            self.assertEqual(
                len(lector),
                2,
            )

            fila = lector[1]

            self.assertEqual(
                fila[2],
                "Íñigo Muñoz",
            )

            self.assertEqual(
                fila[4],
                "Sala Pequeña Ñandú",
            )

            contenido = ruta.read_text(
                encoding="utf-8-sig"
            )

            self.assertIn(
                "Íñigo Muñoz",
                contenido,
            )

            self.assertIn(
                "Sala Pequeña Ñandú",
                contenido,
            )

            self.assertIn(
                "Carné",
                contenido,
            )

            self.assertIn(
                "Código de sala",
                contenido,
            )


if __name__ == "__main__":
    unittest.main()