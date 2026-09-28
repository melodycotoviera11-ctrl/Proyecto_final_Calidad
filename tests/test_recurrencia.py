import unittest
from datetime import date, timedelta

from reservaciones.gestion_recurrencia import (
    generar_fechas_semanales,
    validar_cantidad_ocurrencias,
)


class TestValidarCantidadOcurrencias(unittest.TestCase):

    def test_minimo_de_ocurrencias(self):
        self.assertEqual(
            validar_cantidad_ocurrencias(2),
            2
        )

    def test_maximo_de_ocurrencias(self):
        self.assertEqual(
            validar_cantidad_ocurrencias(8),
            8
        )

    def test_menos_de_dos_ocurrencias(self):
        with self.assertRaises(ValueError):
            validar_cantidad_ocurrencias(1)

    def test_mas_de_ocho_ocurrencias(self):
        with self.assertRaises(ValueError):
            validar_cantidad_ocurrencias(9)

    def test_cantidad_cero(self):
        with self.assertRaises(ValueError):
            validar_cantidad_ocurrencias(0)

    def test_cantidad_negativa(self):
        with self.assertRaises(ValueError):
            validar_cantidad_ocurrencias(-1)

    def test_cantidad_no_numerica(self):
        with self.assertRaises(ValueError):
            validar_cantidad_ocurrencias("abc")


class TestGenerarFechasSemanales(unittest.TestCase):

    def test_generar_dos_ocurrencias(self):
        fechas = generar_fechas_semanales(
            "2026-10-05",
            2
        )

        self.assertEqual(
            fechas,
            [
                date(2026, 10, 5),
                date(2026, 10, 12),
            ]
        )

    def test_generar_ocho_ocurrencias(self):
        fechas = generar_fechas_semanales(
            "2026-10-05",
            8
        )

        self.assertEqual(len(fechas), 8)

    def test_frecuencia_semanal(self):
        fechas = generar_fechas_semanales(
            "2026-10-05",
            8
        )

        for anterior, siguiente in zip(fechas, fechas[1:]):
            self.assertEqual(
                siguiente - anterior,
                timedelta(days=7)
            )

    def test_primera_fecha_corresponde_a_la_inicial(self):
        fechas = generar_fechas_semanales(
            "2026-10-05",
            4
        )

        self.assertEqual(
            fechas[0],
            date(2026, 10, 5)
        )

    def test_rechaza_una_ocurrencia(self):
        with self.assertRaises(ValueError):
            generar_fechas_semanales(
                "2026-10-05",
                1
            )

    def test_rechaza_nueve_ocurrencias(self):
        with self.assertRaises(ValueError):
            generar_fechas_semanales(
                "2026-10-05",
                9
            )


if __name__ == "__main__":
    unittest.main()