"""
Pruebas de RF-02: registrar estudiante.

Agregadas en la Fase 6 para atender el hallazgo H-07 (Grupo 07):
la suite no tenía pruebas de registrar_estudiante. Cubren la sección
14.1 del enunciado: carné duplicado con otra capitalización, campos
vacíos, espacios periféricos y tipos o formatos inválidos.
"""

import unittest

from estudiantes.gestion_estudiantes import registrar_estudiante
from tests.utilidades import ACTIVO, PruebaConBaseTemporal


class TestRF02RegistrarEstudiante(PruebaConBaseTemporal):

    def estudiante(self, carne):
        return self.sql(
            """
            SELECT carne, nombre_completo, correo, estado
            FROM estudiantes
            WHERE carne = ?
            """,
            (carne,),
        )

    def assert_rechazado_sin_cambios(self, datos, palabra_clave):
        """Comprueba que el registro falla, identifica el dato y no guarda nada."""

        antes = self.conteos()

        exito, mensaje = registrar_estudiante(*datos)

        self.assertFalse(exito, f"Se aceptó {datos!r}")
        self.assertIn(palabra_clave, mensaje.lower())
        self.assertEqual(antes, self.conteos())

    # ------------------------------------------------------------------
    # Flujo exitoso
    # ------------------------------------------------------------------

    def test_rf02_registro_valido_queda_activo(self):
        exito, mensaje = registrar_estudiante(
            "D001112223",
            "Ana Mora",
            "ana.mora@universidad.ac.cr",
        )

        self.assertTrue(exito)
        self.assertIn("registrado correctamente", mensaje)
        self.assertEqual(
            self.estudiante("D001112223"),
            [("D001112223", "Ana Mora", "ana.mora@universidad.ac.cr", "activo")],
        )

    def test_rf02_elimina_espacios_perifericos(self):
        exito, _ = registrar_estudiante(
            "  D001112223  ",
            "  Ana Mora  ",
            "  ana.mora@universidad.ac.cr  ",
        )

        self.assertTrue(exito)
        self.assertEqual(
            self.estudiante("D001112223"),
            [("D001112223", "Ana Mora", "ana.mora@universidad.ac.cr", "activo")],
        )

    def test_rf02_carne_se_guarda_en_mayusculas(self):
        exito, _ = registrar_estudiante(
            "d001112223",
            "Ana Mora",
            "ana@universidad.ac.cr",
        )

        self.assertTrue(exito)
        self.assertEqual(len(self.estudiante("D001112223")), 1)

    # ------------------------------------------------------------------
    # Carné duplicado
    # ------------------------------------------------------------------

    def test_rf02_rechaza_carne_duplicado(self):
        self.assert_rechazado_sin_cambios(
            (ACTIVO, "Otra Persona", "otra@universidad.ac.cr"),
            "carné",
        )

    def test_rf02_rechaza_carne_duplicado_con_otra_capitalizacion(self):
        self.assert_rechazado_sin_cambios(
            (ACTIVO.lower(), "Otra Persona", "otra@universidad.ac.cr"),
            "carné",
        )

    def test_rf02_rechaza_duplicado_con_espacios_perifericos(self):
        self.assert_rechazado_sin_cambios(
            (f"  {ACTIVO.lower()} ", "Otra Persona", "otra@universidad.ac.cr"),
            "carné",
        )

    # ------------------------------------------------------------------
    # Campos vacíos
    # ------------------------------------------------------------------

    def test_rf02_rechaza_campos_vacios_identificando_el_dato(self):
        casos = (
            (("", "Ana Mora", "ana@universidad.ac.cr"), "carné"),
            (("   ", "Ana Mora", "ana@universidad.ac.cr"), "carné"),
            (("D001112223", "", "ana@universidad.ac.cr"), "nombre"),
            (("D001112223", "   ", "ana@universidad.ac.cr"), "nombre"),
            (("D001112223", "Ana Mora", ""), "correo"),
            (("D001112223", "Ana Mora", "   "), "correo"),
        )

        for datos, palabra in casos:
            with self.subTest(datos=datos):
                self.assert_rechazado_sin_cambios(datos, palabra)

    # ------------------------------------------------------------------
    # Formatos inválidos
    # ------------------------------------------------------------------

    def test_rf02_carne_debe_tener_exactamente_10_caracteres(self):
        for carne in ("D00111222", "D0011122233"):
            with self.subTest(carne=carne):
                self.assert_rechazado_sin_cambios(
                    (carne, "Ana Mora", "ana@universidad.ac.cr"),
                    "carné",
                )

    def test_rf02_carne_sin_espacios_internos_ni_simbolos(self):
        for carne in ("D0011 2223", "D00111222-", "D00111222Ñ"):
            with self.subTest(carne=carne):
                self.assert_rechazado_sin_cambios(
                    (carne, "Ana Mora", "ana@universidad.ac.cr"),
                    "carné",
                )

    def test_rf02_nombre_minimo_tres_caracteres_distintos_de_espacio(self):
        self.assert_rechazado_sin_cambios(
            ("D001112223", "A l", "ana@universidad.ac.cr"),
            "nombre",
        )

        exito, _ = registrar_estudiante(
            "D001112223",
            "Ana",
            "ana@universidad.ac.cr",
        )
        self.assertTrue(exito)

    def test_rf02_correo_con_un_arroba_y_punto_en_el_dominio(self):
        for correo in (
            "ana.universidad.ac.cr",
            "ana@@universidad.ac.cr",
            "ana@uni@ac.cr",
            "ana@universidad",
            "@universidad.ac.cr",
        ):
            with self.subTest(correo=correo):
                self.assert_rechazado_sin_cambios(
                    ("D001112223", "Ana Mora", correo),
                    "correo",
                )

    def test_rf02_tipos_invalidos_no_lanzan_excepcion_ni_guardan(self):
        antes = self.conteos()

        for datos in (
            (None, "Ana Mora", "ana@universidad.ac.cr"),
            ("D001112223", 123, "ana@universidad.ac.cr"),
            ("D001112223", "Ana Mora", None),
        ):
            with self.subTest(datos=datos):
                exito, mensaje = registrar_estudiante(*datos)
                self.assertFalse(exito)
                self.assertTrue(mensaje)

        self.assertEqual(antes, self.conteos())


if __name__ == "__main__":
    unittest.main()
