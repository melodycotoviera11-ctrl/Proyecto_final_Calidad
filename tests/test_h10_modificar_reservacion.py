
"""Pruebas H-10: modificación de reservaciones."""

import unittest
from datetime import datetime, timedelta

from estudiantes.gestion_estudiantes import modificar_estudiante
from reservaciones.gestion_reservaciones import modificar_reservacion
from tests.utilidades import ACTIVO, PruebaConBaseTemporal


class TestH10ModificarReservacion(PruebaConBaseTemporal):

    def test_estudiante_inactivo_no_puede_modificar_reservacion(self):
        """Rechaza la modificación y conserva los datos originales."""

        fecha_futura = (
            datetime.now() + timedelta(days=2)
        ).date().isoformat()

        id_reservacion = self.insertar_directo(
            ACTIVO, "S01", fecha_futura, "10:00"
        )

        modificar_estudiante(
            ACTIVO,
            "Andrea Solano",
            "andrea@universidad.ac.cr",
            "inactivo",
        )

        antes = self.sql(
            """
            SELECT codigo_sala, fecha, hora_inicio,
                   duracion, cantidad_personas, estado
            FROM reservaciones
            WHERE id = ?
            """,
            (id_reservacion,),
        )

        exito, mensaje, nuevo_id = modificar_reservacion(
            f"R{id_reservacion:04d}",
            "S02",
            fecha_futura,
            "12:00",
            1,
            1,
        )

        self.assertFalse(exito)
        self.assertIsNone(nuevo_id)
        self.assertIn("no puede modificar reservaciones", mensaje)
        self.assertNotIn("no puede crear reservaciones", mensaje)

        despues = self.sql(
            """
            SELECT codigo_sala, fecha, hora_inicio,
                   duracion, cantidad_personas, estado
            FROM reservaciones
            WHERE id = ?
            """,
            (id_reservacion,),
        )

        self.assertEqual(antes, despues)


if __name__ == "__main__":
    unittest.main()