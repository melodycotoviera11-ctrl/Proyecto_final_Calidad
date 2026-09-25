"""Pruebas de RF-11: modificar estudiante."""

import unittest

from estudiantes.gestion_estudiantes import modificar_estudiante
from reservaciones.gestion_reservaciones import crear_reservacion
from tests.utilidades import (
    ACTIVO,
    AHORA,
    MANANA,
    PruebaConBaseTemporal,
)


class TestModificarEstudiante(PruebaConBaseTemporal):

    def test_modificar_nombre_y_correo(self):
        exito, mensaje = modificar_estudiante(
            ACTIVO,
            "Andrea Solano Vargas",
            "andrea.solano@universidad.ac.cr",
            "activo",
        )

        self.assertTrue(exito)
        self.assertIn("modificó correctamente", mensaje)

        estudiante = self.sql(
            """
            SELECT carne, nombre_completo, correo, estado
            FROM estudiantes
            WHERE carne = ?
            """,
            (ACTIVO,),
        )

        self.assertEqual(
            estudiante,
            [
                (
                    ACTIVO,
                    "Andrea Solano Vargas",
                    "andrea.solano@universidad.ac.cr",
                    "activo",
                )
            ],
        )

    def test_cambiar_estado_a_inactivo(self):
        exito, _ = modificar_estudiante(
            ACTIVO,
            "Andrea Solano",
            "andrea@universidad.ac.cr",
            "inactivo",
        )

        self.assertTrue(exito)

        estado = self.sql(
            "SELECT estado FROM estudiantes WHERE carne = ?",
            (ACTIVO,),
        )

        self.assertEqual(estado, [("inactivo",)])

    def test_carne_permanece_sin_cambios(self):
        modificar_estudiante(
            ACTIVO,
            "Andrea Modificada",
            "andrea.nueva@universidad.ac.cr",
            "activo",
        )

        estudiantes = self.sql(
            """
            SELECT carne
            FROM estudiantes
            WHERE nombre_completo = ?
            """,
            ("Andrea Modificada",),
        )

        self.assertEqual(estudiantes, [(ACTIVO,)])

    def test_estudiante_inexistente(self):
        exito, mensaje = modificar_estudiante(
            "Z999999999",
            "Persona Inexistente",
            "persona@universidad.ac.cr",
            "activo",
        )

        self.assertFalse(exito)
        self.assertIn("no corresponde a ningún estudiante", mensaje)

    def test_datos_invalidos_no_modifican_estudiante(self):
        antes = self.sql(
            """
            SELECT carne, nombre_completo, correo, estado
            FROM estudiantes
            WHERE carne = ?
            """,
            (ACTIVO,),
        )

        casos = [
            ("", "andrea@universidad.ac.cr", "activo"),
            ("Andrea Solano", "correo-invalido", "activo"),
            ("Andrea Solano", "andrea@universidad.ac.cr", "bloqueado"),
        ]

        for nombre, correo, estado in casos:
            with self.subTest(
                nombre=nombre,
                correo=correo,
                estado=estado,
            ):
                exito, _ = modificar_estudiante(
                    ACTIVO,
                    nombre,
                    correo,
                    estado,
                )

                self.assertFalse(exito)

                despues = self.sql(
                    """
                    SELECT carne, nombre_completo, correo, estado
                    FROM estudiantes
                    WHERE carne = ?
                    """,
                    (ACTIVO,),
                )

                self.assertEqual(despues, antes)

    def test_inactivar_conserva_reservaciones(self):
        id_reservacion = self.insertar_directo(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
        )

        modificar_estudiante(
            ACTIVO,
            "Andrea Solano",
            "andrea@universidad.ac.cr",
            "inactivo",
        )

        reservacion = self.sql(
            """
            SELECT id, carne, estado
            FROM reservaciones
            WHERE id = ?
            """,
            (id_reservacion,),
        )

        self.assertEqual(
            reservacion,
            [(id_reservacion, ACTIVO, "activa")],
        )

    def test_estudiante_inactivo_no_puede_crear_reservacion(self):
        modificar_estudiante(
            ACTIVO,
            "Andrea Solano",
            "andrea@universidad.ac.cr",
            "inactivo",
        )

        exito, mensaje, id_reservacion = crear_reservacion(
            ACTIVO,
            "S01",
            MANANA,
            "10:00",
            1,
            1,
            ahora=AHORA,
        )

        self.assertFalse(exito)
        self.assertIsNone(id_reservacion)
        self.assertIn("inactivo", mensaje)


if __name__ == "__main__":
    unittest.main()