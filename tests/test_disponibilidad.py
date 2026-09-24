"""Pruebas de RF-08 (consultar disponibilidad)."""

import unittest

from reservaciones.disponibilidad import consultar_disponibilidad
from tests.utilidades import (
    ACTIVO, AHORA, HOY, MANANA, PruebaConBaseTemporal,
)


class TestDisponibilidad(PruebaConBaseTemporal):

    def consultar(self, sala="S01", fecha=MANANA, hora="10:00", duracion=1):
        return consultar_disponibilidad(sala, fecha, hora, duracion, ahora=AHORA)

    def test_sala_libre_disponible(self):
        exito, mensaje, disponible = self.consultar()
        self.assertTrue(exito)
        self.assertTrue(disponible)
        self.assertIn("está disponible", mensaje)

    def test_conflicto_no_disponible(self):
        id_existente = self.insertar_directo(ACTIVO, "S01", MANANA, "10:00", 2)
        exito, mensaje, disponible = self.consultar(hora="11:00")
        self.assertTrue(exito)
        self.assertFalse(disponible)
        self.assertIn(f"ID {id_existente}", mensaje)

    def test_consecutiva_disponible(self):
        self.insertar_directo(ACTIVO, "S01", MANANA, "10:00", 2)
        _, _, disponible = self.consultar(hora="12:00")
        self.assertTrue(disponible)

    def test_cancelada_no_bloquea(self):
        self.insertar_directo(ACTIVO, "S01", MANANA, "10:00", 2, estado="cancelada")
        _, _, disponible = self.consultar(hora="10:00")
        self.assertTrue(disponible)

    def test_sala_fuera_de_servicio(self):
        exito, mensaje, disponible = self.consultar(sala="S04")
        self.assertTrue(exito)
        self.assertFalse(disponible)
        self.assertIn("fuera de servicio", mensaje)

    def test_sala_inexistente(self):
        exito, mensaje, disponible = self.consultar(sala="S99")
        self.assertFalse(exito)
        self.assertIsNone(disponible)
        self.assertIn("no existe", mensaje)

    def test_validaciones_de_formato_y_horario(self):
        casos = {
            "AAAA-MM-DD": dict(fecha="06/10/2026"),
            "hora completa": dict(hora="10:15"),
            "08:00 a 20:00": dict(hora="19:00", duracion=2),
            "1 o 2 horas": dict(duracion=4),
            "anterior a la fecha actual": dict(fecha="2026-10-01"),
            "posterior a la hora actual": dict(fecha=HOY, hora="09:00"),
            "sala es obligatorio": dict(sala=""),
        }
        for fragmento, caso in casos.items():
            with self.subTest(fragmento=fragmento):
                exito, mensaje, disponible = self.consultar(**caso)
                self.assertFalse(exito)
                self.assertIsNone(disponible)
                self.assertIn(fragmento, mensaje)

    def test_consulta_no_modifica_la_base_de_datos(self):
        self.insertar_directo(ACTIVO, "S01", MANANA, "10:00", 2)
        antes = self.conteos()
        secuencia_antes = self.sql("SELECT * FROM sqlite_sequence ORDER BY name")

        self.consultar(hora="10:00")
        self.consultar(hora="14:00")
        self.consultar(sala="S04")
        self.consultar(fecha="basura")

        self.assertEqual(self.conteos(), antes)
        self.assertEqual(self.sql("SELECT * FROM sqlite_sequence ORDER BY name"),
                         secuencia_antes)


if __name__ == "__main__":
    unittest.main()
