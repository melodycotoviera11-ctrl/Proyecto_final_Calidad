"""
Pruebas de BUG-F7-05 (Fase 7, Grupo 8) para RF-15 y RN-02.

El filtro de fecha del panel principal aceptaba formatos que
date.fromisoformat() admite desde Python 3.11, como 20261110 o
2030-W01-1, y mostraba "No hay reservaciones para los filtros
seleccionados." en lugar de informar el formato esperado. Ahora el
filtro exige exactamente AAAA-MM-DD.
"""

import unittest

from reservaciones.panel import interpretar_filtros


class TestBugF705FiltroFechaPanel(unittest.TestCase):

    def test_bug_f7_05_rechaza_formatos_no_canonicos(self):
        for fecha in ("20261110", "2030-W01-1", "2026-314", "2026-1-5",
                      "2026/11/10", "10-11-2026"):
            with self.subTest(fecha=fecha):
                with self.assertRaisesRegex(ValueError, "AAAA-MM-DD"):
                    interpretar_filtros(fecha, "Todas", "Todos")

    def test_bug_f7_05_rechaza_fecha_inexistente(self):
        with self.assertRaisesRegex(ValueError, "AAAA-MM-DD"):
            interpretar_filtros("2026-02-30", "Todas", "Todos")

    def test_bug_f7_05_acepta_formato_canonico_y_vacio(self):
        self.assertEqual(
            interpretar_filtros(" 2026-11-10 ", "Todas", "Todos"),
            ("2026-11-10", "", "todos"),
        )
        self.assertEqual(interpretar_filtros("", "Todas", "Todos"), ("", "", "todos"))


if __name__ == "__main__":
    unittest.main()
