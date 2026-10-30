import unittest
from datetime import datetime
from unittest.mock import patch

from reservaciones.disponibilidad import consultar_franjas_disponibilidad


class TestH11FranjasDisponibilidad(unittest.TestCase):

    @patch("reservaciones.disponibilidad.consultar_disponibilidad")
    def test_genera_doce_franjas_disponibles(self, consulta_simulada):
        consulta_simulada.return_value = (True, "Disponible", True)

        exito, mensaje, franjas = consultar_franjas_disponibilidad(
            "S01",
            "2026-11-05",
            ahora=datetime(2026, 10, 30, 8, 0),
        )

        self.assertTrue(exito)
        self.assertEqual(len(franjas), 12)
        self.assertEqual(franjas[0], ("08:00", "09:00", "Disponible"))
        self.assertEqual(franjas[-1], ("19:00", "20:00", "Disponible"))
        self.assertTrue(
            all(estado == "Disponible" for _, _, estado in franjas)
        )

    @patch("reservaciones.disponibilidad.consultar_disponibilidad")
    def test_identifica_franjas_ocupadas(self, consulta_simulada):

        def simular_consulta(codigo, fecha, hora, duracion, ahora=None):
            if hora in ("10:00", "11:00"):
                return True, "Existe una reservación activa.", False

            return True, "Disponible", True

        consulta_simulada.side_effect = simular_consulta

        exito, mensaje, franjas = consultar_franjas_disponibilidad(
            "S01",
            "2026-11-05",
            ahora=datetime(2026, 10, 30, 8, 0),
        )

        self.assertTrue(exito)
        self.assertEqual(len(franjas), 12)

        self.assertEqual(
            franjas[2],
            ("10:00", "11:00", "Ocupada"),
        )

        self.assertEqual(
            franjas[3],
            ("11:00", "12:00", "Ocupada"),
        )

        self.assertEqual(
            franjas[4],
            ("12:00", "13:00", "Disponible"),
        )

    @patch("reservaciones.disponibilidad.consultar_disponibilidad")
    def test_sala_fuera_de_servicio(self, consulta_simulada):
        consulta_simulada.return_value = (
            True,
            "La sala S01 no está disponible: se encuentra fuera de servicio.",
            False,
        )

        exito, mensaje, franjas = consultar_franjas_disponibilidad(
            "S01",
            "2026-11-05",
            ahora=datetime(2026, 10, 30, 8, 0),
        )

        self.assertTrue(exito)
        self.assertEqual(len(franjas), 12)

        self.assertTrue(
            all(
                estado == "Fuera de servicio"
                for _, _, estado in franjas
            )
        )

    @patch("reservaciones.disponibilidad.consultar_disponibilidad")
    def test_datos_invalidos(self, consulta_simulada):
        consulta_simulada.return_value = (
            False,
            "La fecha ingresada no es válida.",
            None,
        )

        exito, mensaje, franjas = consultar_franjas_disponibilidad(
            "S01",
            "fecha-invalida",
            ahora=datetime(2026, 10, 30, 8, 0),
        )

        self.assertFalse(exito)
        self.assertIn("fecha", mensaje.lower())
        self.assertEqual(franjas, [])
               
if __name__ == "__main__":
    unittest.main()