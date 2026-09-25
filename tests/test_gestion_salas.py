"""Pruebas de RF-12: gestionar salas."""

import unittest

from reservaciones.gestion_reservaciones import crear_reservacion
from salas.gestion_salas import registrar_sala, modificar_sala
from tests.utilidades import (
    ACTIVO,
    AHORA,
    MANANA,
    PruebaConBaseTemporal,
)


class TestGestionSalas(PruebaConBaseTemporal):

    def test_registrar_sala_valida(self):
        exito, mensaje = registrar_sala(
            "S06",
            "Sala de estudio nueva",
            5,
            "disponible",
        )

        self.assertTrue(exito)
        self.assertIn("registró correctamente", mensaje)

        sala = self.sql(
            """
            SELECT codigo, nombre, capacidad, estado
            FROM salas
            WHERE codigo = 'S06'
            """
        )

        self.assertEqual(
            sala,
            [
                (
                    "S06",
                    "Sala de estudio nueva",
                    5,
                    "disponible",
                )
            ],
        )

    def test_codigo_duplicado(self):
        exito, mensaje = registrar_sala(
            "s01",
            "Otra sala",
            5,
            "disponible",
        )

        self.assertFalse(exito)
        self.assertIn("ya se encuentra registrado", mensaje)

    def test_capacidad_invalida_no_registra(self):
        casos = (0, -1, "2.5", "abc", None, True)

        for capacidad in casos:
            with self.subTest(capacidad=capacidad):
                exito, _ = registrar_sala(
                    "S06",
                    "Sala inválida",
                    capacidad,
                    "disponible",
                )

                self.assertFalse(exito)

        resultado = self.sql(
            "SELECT codigo FROM salas WHERE codigo = 'S06'"
        )

        self.assertEqual(resultado, [])

    def test_modificar_nombre_capacidad_y_estado(self):
        exito, mensaje = modificar_sala(
            "S01",
            "Sala Biblioteca Renovada",
            7,
            "fuera de servicio",
            ahora=AHORA,
        )

        self.assertTrue(exito)
        self.assertIn("modificó correctamente", mensaje)

        sala = self.sql(
            """
            SELECT codigo, nombre, capacidad, estado
            FROM salas
            WHERE codigo = 'S01'
            """
        )

        self.assertEqual(
            sala,
            [
                (
                    "S01",
                    "Sala Biblioteca Renovada",
                    7,
                    "fuera_de_servicio",
                )
            ],
        )

    def test_codigo_permanece_sin_cambios(self):
        modificar_sala(
            "S01",
            "Sala Modificada",
            4,
            "disponible",
            ahora=AHORA,
        )

        resultado = self.sql(
            """
            SELECT codigo
            FROM salas
            WHERE nombre = 'Sala Modificada'
            """
        )

        self.assertEqual(resultado, [("S01",)])

    def test_sala_inexistente(self):
        exito, mensaje = modificar_sala(
            "S99",
            "Sala inexistente",
            4,
            "disponible",
            ahora=AHORA,
        )

        self.assertFalse(exito)
        self.assertIn("no se encuentra registrada", mensaje)

    def test_no_reducir_capacidad_bajo_reservacion_futura(self):
        self.insertar_directo(
            ACTIVO,
            "S02",
            MANANA,
            "10:00",
            1,
            6,
        )

        antes = self.sql(
            """
            SELECT nombre, capacidad, estado
            FROM salas
            WHERE codigo = 'S02'
            """
        )

        exito, mensaje = modificar_sala(
            "S02",
            "Sala Biblioteca 2 modificada",
            4,
            "disponible",
            ahora=AHORA,
        )

        self.assertFalse(exito)
        self.assertIn("capacidad", mensaje)

        despues = self.sql(
            """
            SELECT nombre, capacidad, estado
            FROM salas
            WHERE codigo = 'S02'
            """
        )

        self.assertEqual(despues, antes)

    def test_capacidad_exacta_de_reservacion_es_valida(self):
        self.insertar_directo(
            ACTIVO,
            "S02",
            MANANA,
            "10:00",
            1,
            6,
        )

        exito, _ = modificar_sala(
            "S02",
            "Sala Biblioteca 2",
            6,
            "disponible",
            ahora=AHORA,
        )

        self.assertTrue(exito)

    def test_fuera_de_servicio_conserva_reservaciones(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            1,
            2,
        )

        exito, _ = modificar_sala(
            "S01",
            "Sala Biblioteca 1",
            4,
            "fuera_de_servicio",
            ahora=AHORA,
        )

        self.assertTrue(exito)

        reservacion = self.sql(
            """
            SELECT id, codigo_sala
            FROM reservaciones
            WHERE id = ?
            """,
            (id_reservacion,),
        )

        self.assertEqual(
            reservacion,
            [(id_reservacion, "S01")],
        )

    def test_fuera_de_servicio_impide_nueva_reservacion(self):
        exito, _ = modificar_sala(
            "S01",
            "Sala Biblioteca 1",
            4,
            "fuera_de_servicio",
            ahora=AHORA,
        )

        self.assertTrue(exito)

        exito_reserva, mensaje, id_reservacion = crear_reservacion(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            1,
            1,
            ahora=AHORA,
        )

        self.assertFalse(exito_reserva)
        self.assertIsNone(id_reservacion)
        self.assertIn("fuera de servicio", mensaje)


if __name__ == "__main__":
    unittest.main()