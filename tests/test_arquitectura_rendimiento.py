"""
Pruebas de calidad del módulo de reservaciones:
    - RNF-07 / RNF-10: la lógica se importa sin interfaz y la interfaz no usa SQL.
    - RNF-09: consultas de P2 en menos de 2 s con 1 000 estudiantes y 5 000 reservaciones.
"""

import random
import re
import sqlite3
import subprocess
import sys
import time
import unittest
from datetime import date, timedelta
from pathlib import Path

from reservaciones.disponibilidad import consultar_disponibilidad
from reservaciones.gestion_reservaciones import (
    buscar_por_estudiante, consultar_reservaciones,
)
from tests.utilidades import AHORA, PruebaConBaseTemporal

RAIZ = Path(__file__).resolve().parent.parent


class TestArquitectura(unittest.TestCase):

    def test_logica_se_importa_sin_interfaz_grafica(self):
        codigo = (
            "import sys\n"
            "import reservaciones.validaciones, reservaciones.reglas\n"
            "import reservaciones.gestion_reservaciones, reservaciones.disponibilidad\n"
            "assert 'tkinter' not in sys.modules, 'la lógica importa tkinter'\n"
        )
        resultado = subprocess.run(
            [sys.executable, "-c", codigo], cwd=RAIZ,
            capture_output=True, text=True,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)

    def test_interfaz_no_ejecuta_sql(self):
        patron = re.compile(
            r"sqlite3|obtener_conexion|\.execute\(|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b"
        )
        carpeta = RAIZ / "interfaz"
        for archivo in carpeta.glob("*.py"):
            with self.subTest(archivo=archivo.name):
                contenido = archivo.read_text(encoding="utf-8")
                self.assertIsNone(patron.search(contenido))

    def test_sin_rutas_absolutas(self):
        # RNF-03: ninguna ruta personal en el código de P2.
        patron = re.compile(r"[A-Za-z]:\\|/Users/|/home/")
        for carpeta in ("reservaciones", "interfaz"):
            for archivo in (RAIZ / carpeta).glob("*.py"):
                with self.subTest(archivo=archivo.name):
                    self.assertIsNone(patron.search(archivo.read_text(encoding="utf-8")))


class TestRendimiento(PruebaConBaseTemporal):

    LIMITE_SEGUNDOS = 2.0

    def setUp(self):
        super().setUp()
        aleatorio = random.Random(472)
        estudiantes = [
            (f"P{indice:09d}", f"Estudiante Núñez {indice}",
             f"e{indice}@universidad.ac.cr", "activo")
            for indice in range(1000)
        ]
        salas = ["S01", "S02", "S03", "S05"]
        inicio = date(2026, 10, 6)
        reservaciones = [
            (
                aleatorio.choice(estudiantes)[0],
                aleatorio.choice(salas),
                (inicio + timedelta(days=aleatorio.randrange(60))).isoformat(),
                f"{aleatorio.randrange(8, 19):02d}:00",
                1, 1,
                aleatorio.choice(["activa", "cancelada"]),
            )
            for _ in range(5000)
        ]
        conexion = sqlite3.connect(self.ruta_bd)
        with conexion:
            conexion.executemany("INSERT INTO estudiantes VALUES (?, ?, ?, ?)", estudiantes)
            conexion.executemany(
                "INSERT INTO reservaciones (carne, codigo_sala, fecha, hora_inicio, "
                "duracion, cantidad_personas, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
                reservaciones,
            )
        conexion.close()

    def medir(self, funcion):
        tiempos = []
        for _ in range(3):   # tres ejecuciones consecutivas
            inicio = time.perf_counter()
            funcion()
            tiempos.append(time.perf_counter() - inicio)
        return max(tiempos)

    def test_consultas_de_p2_bajo_dos_segundos(self):
        consultas = {
            "consultar_reservaciones": consultar_reservaciones,
            "buscar_por_estudiante": lambda: buscar_por_estudiante("p000000500"),
            "consultar_disponibilidad": lambda: consultar_disponibilidad(
                "S01", "2026-10-20", "10:00", 2, ahora=AHORA),
        }
        self.assertEqual(len(consultar_reservaciones()), 5000)

        for nombre, funcion in consultas.items():
            with self.subTest(consulta=nombre):
                self.assertLess(self.medir(funcion), self.LIMITE_SEGUNDOS)


if __name__ == "__main__":
    unittest.main()
