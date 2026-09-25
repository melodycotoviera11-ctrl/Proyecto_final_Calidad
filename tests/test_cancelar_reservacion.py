"""Pruebas de RF-09: cancelar reservación."""

import unittest

from reservaciones.disponibilidad import consultar_disponibilidad
from reservaciones.gestion_reservaciones import (
    cancelar_reservacion,
    consultar_reservaciones,
)
from tests.utilidades import (
    ACTIVO,
    AHORA,
    MANANA,
    PruebaConBaseTemporal,
)


class TestCancelarReservacion(PruebaConBaseTemporal):

    def test_cancelar_reservacion_activa(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            1,
            2,
        )

        exito, mensaje, id_cancelado = cancelar_reservacion(id_reservacion)

        self.assertTrue(exito)
        self.assertEqual(id_cancelado, id_reservacion)
        self.assertIn("canceló correctamente", mensaje)

        estado = self.sql(
            "SELECT estado FROM reservaciones WHERE id = ?",
            (id_reservacion,),
        )

        self.assertEqual(estado, [("cancelada",)])

    def test_cancelar_id_inexistente(self):
        exito, mensaje, id_cancelado = cancelar_reservacion(9999)

        self.assertFalse(exito)
        self.assertIsNone(id_cancelado)
        self.assertIn("No existe", mensaje)

    def test_cancelar_reservacion_ya_cancelada(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            estado="cancelada",
        )

        exito, mensaje, id_cancelado = cancelar_reservacion(id_reservacion)

        self.assertFalse(exito)
        self.assertIsNone(id_cancelado)
        self.assertIn("ya se encuentra cancelada", mensaje)

    def test_cancelada_permanece_en_historial(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
        )

        cancelar_reservacion(id_reservacion)

        reservaciones = consultar_reservaciones()

        fila = next(
            reservacion
            for reservacion in reservaciones
            if reservacion[0] == id_reservacion
        )

        self.assertEqual(fila[-1], "cancelada")

    def test_cancelacion_libera_horario(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            1,
        )

        cancelar_reservacion(id_reservacion)

        exito, _, disponible = consultar_disponibilidad(
            "S01",
            MANANA,
            "10:00",
            1,
            ahora=AHORA,
        )

        self.assertTrue(exito)
        self.assertTrue(disponible)

    def test_cancelacion_registra_auditoria(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
        )

        cancelar_reservacion(id_reservacion)

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
            [("cancelación", "reservación", str(id_reservacion))],
        )

    def test_id_invalido(self):
        for valor in ("", "abc", "-1", 0, None, True):
            with self.subTest(valor=valor):
                exito, mensaje, id_cancelado = cancelar_reservacion(valor)

                self.assertFalse(exito)
                self.assertIsNone(id_cancelado)
                self.assertIn("ID", mensaje)


if __name__ == "__main__":
    unittest.main()