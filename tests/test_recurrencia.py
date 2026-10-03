import unittest
from datetime import date, timedelta

from reservaciones.gestion_recurrencia import (
    crear_reservacion_recurrente,
    generar_fechas_semanales,
    validar_cantidad_ocurrencias,
)

from tests.utilidades import (
    ACTIVO,
    AHORA,
    PruebaConBaseTemporal,
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

        for anterior, siguiente in zip(
            fechas,
            fechas[1:]
        ):
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


class TestCrearReservacionRecurrente(
    PruebaConBaseTemporal
):

    def test_serie_respeta_maximo_tres_reservaciones_activas(
        self
    ):
        # El estudiante ya tiene dos reservaciones activas.
        self.insertar_directo(
            ACTIVO,
            "S01",
            "2026-10-06",
            "10:00",
        )

        self.insertar_directo(
            ACTIVO,
            "S02",
            "2026-10-07",
            "10:00",
        )

        antes = self.sql(
            """
            SELECT COUNT(*)
            FROM reservaciones
            WHERE carne = ?
            """,
            (ACTIVO,),
        )[0][0]

        # Una serie de dos provocaría un total de cuatro,
        # superando el máximo permitido de tres.
        with self.assertRaisesRegex(
            ValueError,
            "máximo permitido",
        ):
            crear_reservacion_recurrente(
                ACTIVO,
                "S03",
                "2026-10-12",
                "10:00",
                1,
                1,
                2,
                ahora=AHORA,
            )

        despues = self.sql(
            """
            SELECT COUNT(*)
            FROM reservaciones
            WHERE carne = ?
            """,
            (ACTIVO,),
        )[0][0]

        # Si la serie es rechazada, no debe guardarse
        # ninguna de sus ocurrencias.
        self.assertEqual(
            despues,
            antes,
        )

    def test_resume_todos_los_conflictos_de_horario(
        self
    ):
        # Se preparan conflictos para las dos semanas.
        self.insertar_directo(
            ACTIVO,
            "S01",
            "2026-10-12",
            "10:00",
        )

        self.insertar_directo(
            ACTIVO,
            "S01",
            "2026-10-19",
            "10:00",
        )

        antes = self.sql(
            """
            SELECT COUNT(*)
            FROM reservaciones
            """
        )[0][0]

        with self.assertRaises(
            ValueError
        ) as contexto:

            crear_reservacion_recurrente(
                ACTIVO,
                "S01",
                "2026-10-12",
                "10:00",
                1,
                1,
                2,
                ahora=AHORA,
            )

        mensaje = str(
            contexto.exception
        )

        # Debe indicar que existe más de un conflicto.
        self.assertIn(
            "Se encontraron conflictos",
            mensaje,
        )

        # Deben aparecer las dos fechas conflictivas.
        self.assertIn(
            "2026-10-12",
            mensaje,
        )

        self.assertIn(
            "2026-10-19",
            mensaje,
        )

        despues = self.sql(
            """
            SELECT COUNT(*)
            FROM reservaciones
            """
        )[0][0]

        # Si hay conflictos, la serie completa se rechaza.
        self.assertEqual(
            despues,
            antes,
        )


if __name__ == "__main__":
    unittest.main()