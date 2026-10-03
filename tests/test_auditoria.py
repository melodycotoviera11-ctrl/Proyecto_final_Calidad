"""Pruebas de RF-17: auditoría de operaciones sobre reservaciones."""

import unittest

from reservaciones.gestion_reservaciones import (
    cancelar_reservacion,
    crear_reservacion,
    modificar_reservacion,
)
from tests.utilidades import (
    ACTIVO,
    AHORA,
    MANANA,
    PruebaConBaseTemporal,
)


class TestAuditoria(PruebaConBaseTemporal):

    def crear_reservacion_prueba(self):
        """Crea una reservación válida y devuelve su ID."""
        exito, mensaje, id_reservacion = crear_reservacion(
            ACTIVO,
            "S02",
            MANANA,
            "10:00",
            1,
            2,
            ahora=AHORA,
        )

        self.assertTrue(exito, mensaje)
        self.assertIsInstance(
            id_reservacion,
            str,
        )

        self.assertRegex(
            id_reservacion,
            r"^R\d{4,}$",
        )
        return id_reservacion

    def test_auditoria_creacion(self):
        """RF-17: registra la creación de una reservación."""
        id_reservacion = self.crear_reservacion_prueba()

        auditoria = self.sql(
            """
            SELECT tipo_accion, entidad, identificador
            FROM auditoria
            WHERE identificador = ?
            """,
            (str(id_reservacion),),
        )

        self.assertEqual(
            auditoria,
            [("creación", "reservación", str(id_reservacion))],
        )

    def test_auditoria_cancelacion(self):
        """RF-17: registra la cancelación de una reservación."""
        id_reservacion = self.crear_reservacion_prueba()

        exito, mensaje, _ = cancelar_reservacion(id_reservacion)

        self.assertTrue(exito, mensaje)

        auditoria = self.sql(
            """
            SELECT tipo_accion, entidad, identificador
            FROM auditoria
            WHERE identificador = ?
            ORDER BY id
            """,
            (str(id_reservacion),),
        )

        self.assertEqual(
            auditoria,
            [
                ("creación", "reservación", str(id_reservacion)),
                ("cancelación", "reservación", str(id_reservacion)),
            ],
        )

    def test_auditoria_modificacion(self):
        """RF-17: registra la modificación de una reservación."""
        id_reservacion = self.crear_reservacion_prueba()

        exito, mensaje, _ = modificar_reservacion(
            id_reservacion,
            "S03",
            MANANA,
            "12:00",
            1,
            2,
            ahora=AHORA,
        )

        self.assertTrue(exito, mensaje)

        auditoria = self.sql(
            """
            SELECT tipo_accion, entidad, identificador
            FROM auditoria
            WHERE identificador = ?
            ORDER BY id
            """,
            (str(id_reservacion),),
        )

        self.assertEqual(
            auditoria,
            [
                ("creación", "reservación", str(id_reservacion)),
                ("modificación", "reservación", str(id_reservacion)),
            ],
        )

    def test_rechazo_no_registra_auditoria(self):
        """RF-17: una operación rechazada no genera auditoría."""
        cantidad_antes = self.sql(
            "SELECT COUNT(*) FROM auditoria"
        )[0][0]

        exito, _, id_reservacion = crear_reservacion(
            "Z999999999",
            "S02",
            MANANA,
            "10:00",
            1,
            2,
            ahora=AHORA,
        )

        self.assertFalse(exito)
        self.assertIsNone(id_reservacion)

        cantidad_despues = self.sql(
            "SELECT COUNT(*) FROM auditoria"
        )[0][0]

        self.assertEqual(cantidad_despues, cantidad_antes)

    def test_auditoria_contiene_fecha_hora(self):
        """RF-17: cada registro conserva fecha y hora."""
        id_reservacion = self.crear_reservacion_prueba()

        auditoria = self.sql(
            """
            SELECT fecha_hora
            FROM auditoria
            WHERE identificador = ?
            """,
            (str(id_reservacion),),
        )

        self.assertEqual(len(auditoria), 1)
        self.assertIsInstance(auditoria[0][0], str)
        self.assertNotEqual(auditoria[0][0].strip(), "")


if __name__ == "__main__":
    unittest.main()
