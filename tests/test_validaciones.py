"""Pruebas de las validaciones puras (sin base de datos)."""

import unittest
from datetime import date, datetime

from reservaciones import validaciones as v

AHORA = datetime(2026, 10, 5, 9, 30)


class TestFecha(unittest.TestCase):

    def test_fecha_valida(self):
        self.assertEqual(v.validar_fecha("2026-10-06"), date(2026, 10, 6))
        self.assertEqual(v.validar_fecha("  2026-10-06  "), date(2026, 10, 6))

    def test_formatos_invalidos(self):
        for fecha in ("06/10/2026", "2026/10/06", "2026-1-6", "26-10-06",
                      "hoy", "2026-10-06 10:00"):
            with self.subTest(fecha=fecha):
                with self.assertRaisesRegex(ValueError, "AAAA-MM-DD"):
                    v.validar_fecha(fecha)

    def test_fechas_inexistentes(self):
        for fecha in ("2026-13-01", "2026-02-30", "2026-00-10"):
            with self.subTest(fecha=fecha):
                with self.assertRaisesRegex(ValueError, "no existe"):
                    v.validar_fecha(fecha)

    def test_fecha_vacia(self):
        for fecha in (None, "", "   "):
            with self.subTest(fecha=fecha):
                with self.assertRaisesRegex(ValueError, "fecha es obligatorio"):
                    v.validar_fecha(fecha)


class TestHora(unittest.TestCase):

    def test_horas_validas(self):
        self.assertEqual(v.validar_hora_inicio("08:00"), 8)
        self.assertEqual(v.validar_hora_inicio("8:00"), 8)
        self.assertEqual(v.validar_hora_inicio("19:00"), 19)

    def test_hora_no_completa(self):
        for hora in ("14:30", "09:01"):
            with self.subTest(hora=hora):
                with self.assertRaisesRegex(ValueError, "hora completa"):
                    v.validar_hora_inicio(hora)

    def test_formato_invalido(self):
        for hora in ("2pm", "14", "14h00", "14:0", "catorce"):
            with self.subTest(hora=hora):
                with self.assertRaisesRegex(ValueError, "24 horas"):
                    v.validar_hora_inicio(hora)

    def test_hora_fuera_de_rango(self):
        for hora in ("24:00", "25:00", "10:60"):
            with self.subTest(hora=hora):
                with self.assertRaises(ValueError):
                    v.validar_hora_inicio(hora)


class TestDuracionYCantidad(unittest.TestCase):

    def test_duracion_valida(self):
        for valor, esperado in ((1, 1), (2, 2), ("2", 2), (" 1 ", 1)):
            with self.subTest(valor=valor):
                self.assertEqual(v.validar_duracion(valor), esperado)

    def test_duracion_invalida(self):
        for valor in (0, 3, -1, "1.5", 1.5, "uno", True, ""):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    v.validar_duracion(valor)

    def test_cantidad_valida(self):
        self.assertEqual(v.validar_cantidad_personas(1), 1)
        self.assertEqual(v.validar_cantidad_personas("4"), 4)

    def test_cantidad_invalida(self):
        for valor in (0, -3, "0", "2.5", 2.5, "abc", True, None, "   "):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    v.validar_cantidad_personas(valor)

    def test_capacidad(self):
        v.validar_capacidad(4, 4, "S01")          # límite exacto permitido
        with self.assertRaisesRegex(ValueError, "supera la capacidad"):
            v.validar_capacidad(5, 4, "S01")


class TestHorarioPermitido(unittest.TestCase):

    def test_limites_validos(self):
        v.validar_horario_permitido(8, 1)
        v.validar_horario_permitido(18, 2)       # termina a las 20:00
        v.validar_horario_permitido(19, 1)       # termina a las 20:00

    def test_fuera_de_horario(self):
        for inicio, duracion in ((7, 1), (19, 2), (20, 1), (0, 1)):
            with self.subTest(inicio=inicio, duracion=duracion):
                with self.assertRaisesRegex(ValueError, "08:00 a 20:00"):
                    v.validar_horario_permitido(inicio, duracion)


class TestMomentoFuturo(unittest.TestCase):

    def test_fecha_pasada(self):
        with self.assertRaisesRegex(ValueError, "anterior a la fecha actual"):
            v.validar_momento_futuro(date(2026, 10, 4), 10, AHORA)

    def test_hoy_hora_ya_pasada_o_en_curso(self):
        for hora in (8, 9):   # 09:00 ya empezó cuando son las 09:30
            with self.subTest(hora=hora):
                with self.assertRaisesRegex(ValueError, "posterior a la hora actual"):
                    v.validar_momento_futuro(date(2026, 10, 5), hora, AHORA)

    def test_hoy_hora_futura(self):
        v.validar_momento_futuro(date(2026, 10, 5), 10, AHORA)

    def test_hora_exacta_no_es_posterior(self):
        ahora = datetime(2026, 10, 5, 10, 0)
        with self.assertRaises(ValueError):
            v.validar_momento_futuro(date(2026, 10, 5), 10, ahora)

    def test_fecha_futura_cualquier_hora(self):
        v.validar_momento_futuro(date(2026, 10, 6), 8, AHORA)


class TestSuperposicion(unittest.TestCase):

    def test_superpuestas(self):
        self.assertTrue(v.hay_superposicion(10, 2, 11, 1))
        self.assertTrue(v.hay_superposicion(10, 1, 10, 1))
        self.assertTrue(v.hay_superposicion(11, 1, 10, 2))
        self.assertTrue(v.hay_superposicion(9, 2, 10, 2))

    def test_consecutivas_no_se_superponen(self):
        # RN-10: una inicia exactamente al finalizar la otra.
        self.assertFalse(v.hay_superposicion(10, 1, 11, 1))
        self.assertFalse(v.hay_superposicion(11, 1, 10, 1))
        self.assertFalse(v.hay_superposicion(8, 2, 10, 2))

    def test_separadas(self):
        self.assertFalse(v.hay_superposicion(8, 1, 15, 2))


if __name__ == "__main__":
    unittest.main()
