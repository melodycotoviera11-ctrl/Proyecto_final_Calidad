"""
Pruebas de calidad:

- RNF-03: portabilidad.
- RNF-07: mantenibilidad.
- RNF-09: rendimiento.
- RNF-10: testabilidad.
"""

import ctypes
import os
import platform
import random
import re
import sqlite3
import subprocess
import sys
import time
import unittest

from datetime import date, timedelta
from pathlib import Path

from reservaciones.disponibilidad import (
    consultar_disponibilidad,
)

from reservaciones.gestion_reservaciones import (
    buscar_por_estudiante,
    consultar_reservaciones,
)

from salas.gestion_salas import (
    consultar_salas,
)

from tests.utilidades import (
    AHORA,
    PruebaConBaseTemporal,
)


RAIZ = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Información del equipo para la evidencia de RNF-09.
# ---------------------------------------------------------------------------

def obtener_memoria_total_gb():
    """
    Obtiene la memoria RAM total del equipo utilizando únicamente
    herramientas de la biblioteca estándar de Python.
    """

    try:
        if sys.platform == "win32":

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            estado = MEMORYSTATUSEX()
            estado.dwLength = ctypes.sizeof(
                MEMORYSTATUSEX
            )

            resultado = (
                ctypes.windll.kernel32.GlobalMemoryStatusEx(
                    ctypes.byref(estado)
                )
            )

            if resultado:
                return estado.ullTotalPhys / (1024 ** 3)

        if hasattr(os, "sysconf"):

            paginas = os.sysconf(
                "SC_PHYS_PAGES"
            )

            tamano_pagina = os.sysconf(
                "SC_PAGE_SIZE"
            )

            return (
                paginas
                * tamano_pagina
                / (1024 ** 3)
            )

    except Exception:
        pass

    return None


# ===========================================================================
# RNF-03 / RNF-07 / RNF-10
# ===========================================================================

class TestArquitectura(unittest.TestCase):

    def test_logica_se_importa_sin_interfaz_grafica(self):
        codigo = (
            "import sys\n"
            "import reservaciones.validaciones, reservaciones.reglas\n"
            "import reservaciones.gestion_reservaciones, "
            "reservaciones.disponibilidad\n"
            "assert 'tkinter' not in sys.modules, "
            "'la lógica importa tkinter'\n"
        )

        resultado = subprocess.run(
            [
                sys.executable,
                "-c",
                codigo,
            ],
            cwd=RAIZ,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            resultado.returncode,
            0,
            resultado.stderr,
        )

    def test_interfaz_no_ejecuta_sql(self):

        patron = re.compile(
            r"sqlite3|obtener_conexion|"
            r"\.execute\(|\bSELECT\b|"
            r"\bINSERT\b|\bUPDATE\b|\bDELETE\b"
        )

        carpeta = RAIZ / "interfaz"

        for archivo in carpeta.glob("*.py"):

            with self.subTest(
                archivo=archivo.name
            ):

                contenido = archivo.read_text(
                    encoding="utf-8"
                )

                self.assertIsNone(
                    patron.search(
                        contenido
                    )
                )

    def test_sin_rutas_absolutas(self):

        patron = re.compile(
            r"[A-Za-z]:\\|/Users/|/home/"
        )

        for carpeta in (
            "reservaciones",
            "interfaz",
        ):

            for archivo in (
                RAIZ / carpeta
            ).glob("*.py"):

                with self.subTest(
                    archivo=archivo.name
                ):

                    contenido = archivo.read_text(
                        encoding="utf-8"
                    )

                    self.assertIsNone(
                        patron.search(
                            contenido
                        )
                    )


# ===========================================================================
# RNF-09. RENDIMIENTO
# ===========================================================================

class TestRendimiento(
    PruebaConBaseTemporal
):

    LIMITE_SEGUNDOS = 2.0

    def setUp(self):

        super().setUp()

        aleatorio = random.Random(
            472
        )

        # La BD temporal ya contiene los 3 estudiantes iniciales.
        # Se agregan 997 para alcanzar exactamente 1 000.
        estudiantes = [
            (
                f"P{indice:09d}",
                f"Estudiante Núñez {indice}",
                f"e{indice}@universidad.ac.cr",
                "activo",
            )
            for indice in range(997)
        ]

        salas = [
            "S01",
            "S02",
            "S03",
            "S05",
        ]

        inicio = date(
            2026,
            10,
            6,
        )

        reservaciones = [
            (
                aleatorio.choice(
                    estudiantes
                )[0],
                aleatorio.choice(
                    salas
                ),
                (
                    inicio
                    + timedelta(
                        days=aleatorio.randrange(
                            60
                        )
                    )
                ).isoformat(),
                (
                    f"{aleatorio.randrange(8, 19):02d}:00"
                ),
                1,
                1,
                aleatorio.choice(
                    [
                        "activa",
                        "cancelada",
                    ]
                ),
            )
            for _ in range(5000)
        ]

        conexion = sqlite3.connect(
            self.ruta_bd
        )

        try:
            with conexion:

                conexion.executemany(
                    """
                    INSERT INTO estudiantes
                        (
                            carne,
                            nombre_completo,
                            correo,
                            estado
                        )
                    VALUES (?, ?, ?, ?)
                    """,
                    estudiantes,
                )

                conexion.executemany(
                    """
                    INSERT INTO reservaciones
                        (
                            carne,
                            codigo_sala,
                            fecha,
                            hora_inicio,
                            duracion,
                            cantidad_personas,
                            estado
                        )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    reservaciones,
                )

        finally:
            conexion.close()

    # ------------------------------------------------------------------
    # Medición
    # ------------------------------------------------------------------

    def medir(
        self,
        funcion,
    ):
        """
        Ejecuta una consulta tres veces consecutivas
        y devuelve los tres tiempos obtenidos.
        """

        tiempos = []

        for _ in range(3):

            inicio = time.perf_counter()

            funcion()

            fin = time.perf_counter()

            tiempos.append(
                fin - inicio
            )

        return tiempos

    # ------------------------------------------------------------------
    # Carga utilizada por el panel principal
    # ------------------------------------------------------------------

    def cargar_panel_principal(self):
        """
        Mide la carga de información utilizada por RF-15.

        El panel principal obtiene las reservaciones
        y las salas antes de aplicar sus filtros y
        mostrar la información.
        """

        reservaciones = (
            consultar_reservaciones()
        )

        salas = consultar_salas()

        return (
            reservaciones,
            salas,
        )

    # ------------------------------------------------------------------
    # Evidencia
    # ------------------------------------------------------------------

    def guardar_evidencia(
        self,
        resultados,
    ):

        carpeta = (
            RAIZ / "evidencias"
        )

        carpeta.mkdir(
            exist_ok=True
        )

        ruta = (
            carpeta
            / "rendimiento_rnf09.txt"
        )

        memoria = (
            obtener_memoria_total_gb()
        )

        procesador = (
            platform.processor()
            or platform.machine()
            or "No disponible"
        )

        lineas = [
            "RNF-09 - Evidencia de rendimiento",
            "",
            "Ambiente de prueba",
            f"Sistema operativo: {platform.platform()}",
            f"Procesador: {procesador}",
            (
                f"Memoria RAM: {memoria:.2f} GB"
                if memoria is not None
                else "Memoria RAM: No disponible"
            ),
            f"Python: {platform.python_version()}",
            "",
            "Volumen de datos",
            "Estudiantes: 1000",
            "Reservaciones: 5000",
            "",
            "Resultados",
        ]

        for nombre, tiempos in resultados.items():

            lineas.append(
                f"{nombre}:"
            )

            for numero, tiempo_obtenido in enumerate(
                tiempos,
                start=1,
            ):

                lineas.append(
                    (
                        f"  Ejecución {numero}: "
                        f"{tiempo_obtenido:.6f} segundos"
                    )
                )

            lineas.append(
                (
                    "  Tiempo máximo: "
                    f"{max(tiempos):.6f} segundos"
                )
            )

            lineas.append("")

        lineas.append(
            (
                "Criterio: cada ejecución debe "
                "responder en menos de 2 segundos."
            )
        )

        ruta.write_text(
            "\n".join(lineas),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # RNF-09
    # ------------------------------------------------------------------

    def test_consultas_bajo_dos_segundos(self):

        # Comprobar primero que el volumen sea
        # exactamente el definido en RNF-09.

        cantidad_estudiantes = self.sql(
            """
            SELECT COUNT(*)
            FROM estudiantes
            """
        )[0][0]

        cantidad_reservaciones = self.sql(
            """
            SELECT COUNT(*)
            FROM reservaciones
            """
        )[0][0]

        self.assertEqual(
            cantidad_estudiantes,
            1000,
        )

        self.assertEqual(
            cantidad_reservaciones,
            5000,
        )

        consultas = {
            "Consulta general de reservaciones":
                consultar_reservaciones,

            "Búsqueda por carné":
                lambda: buscar_por_estudiante(
                    "P000000500"
                ),

            "Consulta de disponibilidad":
                lambda: consultar_disponibilidad(
                    "S01",
                    "2026-10-20",
                    "10:00",
                    2,
                    ahora=AHORA,
                ),

            "Carga del panel principal":
                self.cargar_panel_principal,
        }

        resultados = {}

        for nombre, funcion in consultas.items():

            resultados[nombre] = (
                self.medir(
                    funcion
                )
            )

        # Guardar la evidencia antes de evaluar
        # los tiempos para que quede registro.
        self.guardar_evidencia(
            resultados
        )

        for nombre, tiempos in resultados.items():

            for numero, tiempo_obtenido in enumerate(
                tiempos,
                start=1,
            ):

                with self.subTest(
                    consulta=nombre,
                    ejecucion=numero,
                ):

                    self.assertLess(
                        tiempo_obtenido,
                        self.LIMITE_SEGUNDOS,
                        (
                            f"{nombre}, ejecución {numero}: "
                            f"{tiempo_obtenido:.6f} segundos"
                        ),
                    )


if __name__ == "__main__":
    unittest.main()