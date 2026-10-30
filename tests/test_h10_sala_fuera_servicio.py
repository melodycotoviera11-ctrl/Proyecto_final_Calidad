
"""Pruebas H-10: salas fuera de servicio con reservas futuras."""

import unittest
from datetime import datetime, timedelta

from salas.gestion_salas import modificar_sala
from tests.utilidades import ACTIVO, PruebaConBaseTemporal


class TestH10SalaFueraServicio(PruebaConBaseTemporal):

    def test_sala_con_dos_reservaciones_futuras(self):
        """Advierte sobre reservas futuras y las conserva."""

        fecha_futura = (
            datetime.now() + timedelta(days=2)
        ).date().isoformat()

        primera = self.insertar_directo(
            ACTIVO, "S01", fecha_futura, "10:00"
        )
        segunda = self.insertar_directo(
            ACTIVO, "S01", fecha_futura, "12:00"
        )

        exito, mensaje = modificar_sala(
            "S01",
            "Sala Biblioteca 1",
            4,
            "fuera_de_servicio",
        )

        self.assertTrue(exito)
        self.assertIn("2 reservación(es)", mensaje)
        self.assertIn("permanecerán registradas", mensaje)

        estado_sala = self.sql(
            "SELECT estado FROM salas WHERE codigo = ?",
            ("S01",),
        )
        self.assertEqual(
            estado_sala, [("fuera_de_servicio",)]
        )

        reservaciones = self.sql(
            """
            SELECT id, estado
            FROM reservaciones
            WHERE id IN (?, ?)
            ORDER BY id
            """,
            (primera, segunda),
        )

        self.assertEqual(
            reservaciones,
            [(primera, "activa"), (segunda, "activa")],
        )

    def test_sala_sin_reservaciones_futuras(self):
        """No advierte cuando no existen reservas futuras."""

        exito, mensaje = modificar_sala(
            "S01",
            "Sala Biblioteca 1",
            4,
            "fuera_de_servicio",
        )

        self.assertTrue(exito)
        self.assertNotIn("Advertencia", mensaje)

    def test_sala_disponible_no_muestra_advertencia(self):
        """Una modificación normal no genera advertencias."""

        fecha_futura = (
            datetime.now() + timedelta(days=2)
        ).date().isoformat()

        self.insertar_directo(
            ACTIVO, "S01", fecha_futura, "10:00"
        )

        exito, mensaje = modificar_sala(
            "S01",
            "Sala Biblioteca Renovada",
            4,
            "disponible",
        )

        self.assertTrue(exito)
        self.assertNotIn("Advertencia", mensaje)


if __name__ == "__main__":
    unittest.main()