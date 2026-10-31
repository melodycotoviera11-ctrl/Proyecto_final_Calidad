"""
Pruebas de H-14 (Fase 3, Grupo 07): el reporte CSV no neutralizaba las
celdas que comienzan con símbolos de fórmula (=, +, -, @).

Se reproduce el escenario del hallazgo (estudiante con nombre "=1+1")
y se comprueba que el texto se exporta como texto, sin alterar los
demás datos, y que el archivo conserva UTF-8 con BOM.
"""

import csv
import tempfile
import unittest
from pathlib import Path

from estudiantes.gestion_estudiantes import registrar_estudiante
from reservaciones.reportes import generar_reporte_csv, neutralizar_celda
from tests.utilidades import ACTIVO, PruebaConBaseTemporal


class TestH14NeutralizarCelda(unittest.TestCase):

    def test_h14_textos_con_simbolo_de_formula(self):
        casos = {
            "=1+1": "'=1+1",
            "+50": "'+50",
            "-2+3": "'-2+3",
            "@SUMA(A1)": "'@SUMA(A1)",
            "\t=1+1": "'\t=1+1",
            "\r=1+1": "'\r=1+1",
        }

        for valor, esperado in casos.items():
            with self.subTest(valor=valor):
                self.assertEqual(neutralizar_celda(valor), esperado)

    def test_h14_datos_normales_no_cambian(self):
        for valor in ("R0001", "Andrea Solano", "S01", "2026-11-03",
                      "10:00", "activa", "Íñigo Muñoz", "", 3, 0):
            with self.subTest(valor=valor):
                self.assertEqual(neutralizar_celda(valor), valor)


class TestH14ReporteCSV(PruebaConBaseTemporal):

    def generar(self, inicio="2026-11-01", fin="2026-11-30"):
        carpeta = Path(tempfile.mkdtemp(dir=self.directorio))
        ruta = carpeta / "reporte.csv"

        exito, mensaje = generar_reporte_csv(inicio, fin, ruta)
        self.assertTrue(exito, mensaje)

        return ruta

    def test_h14_escenario_del_hallazgo(self):
        exito, mensaje = registrar_estudiante("Z000000009", "=1+1", "x@y.cr")
        self.assertTrue(exito, mensaje)
        self.insertar_directo("Z000000009", "S01", "2026-11-03", "10:00", 1, 2)

        ruta = self.generar()
        texto = ruta.read_text(encoding="utf-8-sig")

        self.assertNotIn(",=1+1,", texto)
        self.assertIn(",'=1+1,", texto)

        with ruta.open(encoding="utf-8-sig", newline="") as archivo:
            filas = list(csv.reader(archivo))

        self.assertEqual(
            filas[1],
            ["R0001", "Z000000009", "'=1+1", "S01", "Sala Biblioteca 1",
             "2026-11-03", "10:00", "11:00", "2", "activa"],
        )

    def test_h14_datos_sin_formula_se_exportan_igual(self):
        self.insertar_directo(ACTIVO, "S02", "2026-11-04", "14:00", 2, 3)

        with self.generar().open(encoding="utf-8-sig", newline="") as archivo:
            filas = list(csv.reader(archivo))

        self.assertEqual(
            filas[1],
            ["R0001", ACTIVO, "Andrea Solano", "S02", "Sala Biblioteca 2",
             "2026-11-04", "14:00", "16:00", "3", "activa"],
        )

    def test_h14_archivo_utf8_con_bom(self):
        """El README documenta el BOM; se verifica que efectivamente esté."""
        self.insertar_directo(ACTIVO, "S01", "2026-11-03", "10:00")

        contenido = self.generar().read_bytes()

        self.assertTrue(contenido.startswith(b"\xef\xbb\xbf"))
        contenido.decode("utf-8-sig")


if __name__ == "__main__":
    unittest.main()
