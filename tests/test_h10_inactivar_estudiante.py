
"""Pruebas de H-10: inactivación con reservaciones futuras."""

import unittest
from datetime import datetime, timedelta

from estudiantes.gestion_estudiantes import modificar_estudiante
from tests.utilidades import ACTIVO, PruebaConBaseTemporal

class TestH10InactivarEstudiante(PruebaConBaseTemporal):

    
    def test_h10_inactivar_con_dos_reservaciones_futuras(self):
        """Informa las reservas futuras sin cancelarlas."""

        fecha_futura = (
            datetime.now() + timedelta(days=2)
        ).date().isoformat()

        primera = self.insertar_directo(
            ACTIVO, "S01", fecha_futura, "10:00"
        )

        segunda = self.insertar_directo(
            ACTIVO, "S02", fecha_futura, "12:00"
        )

        exito, mensaje = modificar_estudiante(
            ACTIVO,
            "Andrea Solano",
            "andrea@universidad.ac.cr",
            "inactivo",
        )

        self.assertTrue(exito)
        self.assertIn("2 reservación(es)", mensaje)
        self.assertIn("permanecerán registradas", mensaje)

        estudiante = self.sql(
            "SELECT estado FROM estudiantes WHERE carne = ?",
            (ACTIVO,),
        )
        self.assertEqual(estudiante, [("inactivo",)])

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

    def test_h10_inactivar_sin_reservaciones_futuras(self):
        """No muestra advertencia cuando no hay reservas futuras."""

        exito, mensaje = modificar_estudiante(
            ACTIVO,
            "Andrea Solano",
            "andrea@universidad.ac.cr",
            "inactivo",
        )

        self.assertTrue(exito)
        self.assertIn("modificó correctamente", mensaje)
        self.assertNotIn("Advertencia", mensaje)

    
    def test_h10_modificar_estudiante_activo_sin_advertencia(self):
        """Una edición normal no produce advertencias."""

        fecha_futura = (
            datetime.now() + timedelta(days=2)
        ).date().isoformat()

        self.insertar_directo(
            ACTIVO, "S01", fecha_futura, "10:00"
        )

        exito, mensaje = modificar_estudiante(
            ACTIVO,
            "Andrea Solano Vargas",
            "andrea@universidad.ac.cr",
            "activo",
        )

        self.assertTrue(exito)
        self.assertNotIn("Advertencia", mensaje)

if __name__ == "__main__":
    unittest.main()