"""
Pruebas de H-13 (Fase 3, Grupo 07): ejecutar la suite sobrescribía la
evidencia de rendimiento entregada (evidencias/rendimiento_rnf09.txt).

Se comprueba que la evidencia entregada no cambia, que cada corrida
genera su propio archivo en evidencias/ejecuciones/ y que esa carpeta
está excluida del control de versiones.
"""

import hashlib
import unittest
from datetime import datetime

# Se importa el módulo (no la clase) para que unittest no vuelva a
# descubrir y ejecutar aquí la prueba de rendimiento completa.
from tests import test_arquitectura_rendimiento as rendimiento
from tests.test_arquitectura_rendimiento import (
    CARPETA_EJECUCIONES,
    EVIDENCIA_ENTREGADA,
    RAIZ,
    nombre_evidencia_ejecucion,
)


def huella(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


class TestH13ConservarEvidencia(unittest.TestCase):

    def test_h13_evidencia_entregada_existe(self):
        self.assertTrue(EVIDENCIA_ENTREGADA.is_file())

    def test_h13_guardar_evidencia_no_modifica_la_entregada(self):
        antes = huella(EVIDENCIA_ENTREGADA)

        prueba = rendimiento.TestRendimiento("test_consultas_bajo_dos_segundos")
        ruta = prueba.guardar_evidencia({"Consulta de prueba H-13": [0.001, 0.002]})

        try:
            self.assertEqual(huella(EVIDENCIA_ENTREGADA), antes)
            self.assertEqual(ruta.parent.resolve(), CARPETA_EJECUCIONES.resolve())
            self.assertNotEqual(ruta.resolve(), EVIDENCIA_ENTREGADA.resolve())

            contenido = ruta.read_text(encoding="utf-8")
            self.assertIn("RNF-09 - Evidencia de rendimiento", contenido)
            self.assertIn("Consulta de prueba H-13:", contenido)
        finally:
            ruta.unlink(missing_ok=True)

    def test_h13_nombre_por_entorno_y_fecha(self):
        nombre = nombre_evidencia_ejecucion(datetime(2026, 10, 31, 10, 30, 0, 5))

        self.assertRegex(
            nombre,
            r"^rendimiento_rnf09_[A-Za-z0-9]+_20261031-103000_000005\.txt$",
        )

    def test_h13_ejecuciones_excluidas_de_git(self):
        gitignore = (RAIZ / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("evidencias/ejecuciones/", gitignore.splitlines())


if __name__ == "__main__":
    unittest.main()
