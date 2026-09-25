"""Pruebas de RF-13: modificar reservación."""

import unittest

from reservaciones.gestion_reservaciones import modificar_reservacion
from tests.utilidades import (
    ACTIVO,
    ACTIVO_2,
    AHORA,
    MANANA,
    PASADO_MANANA,
    PruebaConBaseTemporal,
)


class TestModificarReservacion(PruebaConBaseTemporal):

    def test_modificar_reservacion_activa(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            1,
            2,
        )

        exito, mensaje, id_modificado = modificar_reservacion(
            id_reservacion,
            "S03",
            PASADO_MANANA,
            "14:00",
            2,
            4,
            ahora=AHORA,
        )

        self.assertTrue(exito)
        self.assertEqual(id_modificado, id_reservacion)
        self.assertIn("modificó correctamente", mensaje)

        reservacion = self.sql(
            """
            SELECT id, carne, codigo_sala, fecha, hora_inicio,
                   duracion, cantidad_personas, estado
            FROM reservaciones
            WHERE id = ?
            """,
            (id_reservacion,),
        )

        self.assertEqual(
            reservacion,
            [
                (
                    id_reservacion,
                    ACTIVO,
                    "S03",
                    PASADO_MANANA,
                    "14:00",
                    2,
                    4,
                    "activa",
                )
            ],
        )

    def test_reservacion_cancelada_no_se_modifica(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            estado="cancelada",
        )

        exito, mensaje, id_modificado = modificar_reservacion(
            id_reservacion,
            "S02",
            MANANA,
            "12:00",
            1,
            2,
            ahora=AHORA,
        )

        self.assertFalse(exito)
        self.assertIsNone(id_modificado)
        self.assertIn("cancelada", mensaje)

    def test_id_inexistente(self):
        exito, mensaje, id_modificado = modificar_reservacion(
            9999,
            "S01",
            MANANA,
            "10:00",
            1,
            1,
            ahora=AHORA,
        )

        self.assertFalse(exito)
        self.assertIsNone(id_modificado)
        self.assertIn("No existe", mensaje)

    def test_id_invalido(self):
        for valor in ("", "abc", "-1", 0, None, True):
            with self.subTest(valor=valor):
                exito, mensaje, id_modificado = modificar_reservacion(
                    valor,
                    "S01",
                    MANANA,
                    "10:00",
                    1,
                    1,
                    ahora=AHORA,
                )

                self.assertFalse(exito)
                self.assertIsNone(id_modificado)
                self.assertIn("ID", mensaje)

    def test_fecha_invalida_conserva_datos_originales(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            1,
            2,
        )

        antes = self.sql(
            "SELECT * FROM reservaciones WHERE id = ?",
            (id_reservacion,),
        )

        exito, mensaje, _ = modificar_reservacion(
            id_reservacion,
            "S02",
            "2026-10-04",
            "12:00",
            1,
            2,
            ahora=AHORA,
        )

        self.assertFalse(exito)
        self.assertIn("anterior", mensaje)

        despues = self.sql(
            "SELECT * FROM reservaciones WHERE id = ?",
            (id_reservacion,),
        )

        self.assertEqual(despues, antes)

    def test_superposicion_conserva_datos_originales(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "08:00",
            1,
            2,
        )

        self.insertar_directo(
            ACTIVO_2,
            "S02",
            MANANA,
            "10:00",
            2,
            2,
        )

        antes = self.sql(
            "SELECT * FROM reservaciones WHERE id = ?",
            (id_reservacion,),
        )

        exito, mensaje, _ = modificar_reservacion(
            id_reservacion,
            "S02",
            MANANA,
            "11:00",
            1,
            2,
            ahora=AHORA,
        )

        self.assertFalse(exito)
        self.assertIn("se superpone", mensaje)

        despues = self.sql(
            "SELECT * FROM reservaciones WHERE id = ?",
            (id_reservacion,),
        )

        self.assertEqual(despues, antes)

    def test_capacidad_invalida_conserva_datos_originales(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            1,
            2,
        )

        antes = self.sql(
            "SELECT * FROM reservaciones WHERE id = ?",
            (id_reservacion,),
        )

        exito, mensaje, _ = modificar_reservacion(
            id_reservacion,
            "S05",
            MANANA,
            "12:00",
            1,
            2,
            ahora=AHORA,
        )

        self.assertFalse(exito)
        self.assertIn("supera la capacidad", mensaje)

        despues = self.sql(
            "SELECT * FROM reservaciones WHERE id = ?",
            (id_reservacion,),
        )

        self.assertEqual(despues, antes)

    def test_estudiante_inactivo_no_puede_modificar(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            1,
            2,
        )

        self.sql(
            """
            UPDATE estudiantes
            SET estado = 'inactivo'
            WHERE carne = ?
            """,
            (ACTIVO,),
        )

        antes = self.sql(
            "SELECT * FROM reservaciones WHERE id = ?",
            (id_reservacion,),
        )

        exito, mensaje, _ = modificar_reservacion(
            id_reservacion,
            "S02",
            MANANA,
            "12:00",
            1,
            2,
            ahora=AHORA,
        )

        self.assertFalse(exito)
        self.assertIn("inactivo", mensaje)

        despues = self.sql(
            "SELECT * FROM reservaciones WHERE id = ?",
            (id_reservacion,),
        )

        self.assertEqual(despues, antes)

    def test_modificacion_registra_auditoria(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
        )

        modificar_reservacion(
            id_reservacion,
            "S02",
            MANANA,
            "12:00",
            1,
            2,
            ahora=AHORA,
        )

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
            [
                (
                    "modificación",
                    "reservación",
                    str(id_reservacion),
                )
            ],
        )

    def test_reservacion_no_choca_consigo_misma_ni_con_limite(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "08:00",
        )

        self.insertar_directo(
            ACTIVO,
            "S02",
            MANANA,
            "10:00",
        )

        self.insertar_directo(
            ACTIVO,
            "S03",
            MANANA,
            "12:00",
        )

        exito, mensaje, id_modificado = modificar_reservacion(
            id_reservacion,
            "S05",
            MANANA,
            "14:00",
            1,
            1,
            ahora=AHORA,
        )

        self.assertTrue(exito, mensaje)
        self.assertEqual(id_modificado, id_reservacion)


if __name__ == "__main__":
    unittest.main()