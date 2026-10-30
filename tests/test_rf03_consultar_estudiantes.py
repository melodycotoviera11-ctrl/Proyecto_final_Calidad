"""
Pruebas de RF-03: consultar estudiantes.

Agregadas en la Fase 6:
- H-07: la suite no tenía pruebas de consultar_estudiantes.
- H-08: la vista no mostraba un mensaje cuando no hay estudiantes.
"""

import unittest

from estudiantes.gestion_estudiantes import (
    consultar_estudiantes,
    registrar_estudiante,
)
from tests.utilidades import ACTIVO, ACTIVO_2, INACTIVO, PruebaConBaseTemporal

try:
    import tkinter as tk
except ImportError:  # Python sin Tkinter
    tk = None


class TestRF03ConsultarEstudiantes(PruebaConBaseTemporal):

    def test_rf03_muestra_carne_nombre_correo_y_estado(self):
        estudiantes = consultar_estudiantes()

        self.assertIn(
            (ACTIVO, "Andrea Solano", "andrea@universidad.ac.cr", "activo"),
            estudiantes,
        )

        for fila in estudiantes:
            self.assertEqual(len(fila), 4)

    def test_rf03_incluye_activos_e_inactivos(self):
        carnes = {fila[0]: fila[3] for fila in consultar_estudiantes()}

        self.assertEqual(carnes[ACTIVO], "activo")
        self.assertEqual(carnes[ACTIVO_2], "activo")
        self.assertEqual(carnes[INACTIVO], "inactivo")

    def test_rf03_ordena_alfabeticamente_por_nombre(self):
        registrar_estudiante("Z000000001", "Zulema Arias", "zulema@universidad.ac.cr")
        registrar_estudiante("E000000002", "bruno Díaz", "bruno@universidad.ac.cr")

        nombres = [fila[1] for fila in consultar_estudiantes()]

        self.assertEqual(
            nombres,
            [
                "Andrea Solano",
                "bruno Díaz",
                "Carlos Méndez",
                "Daniela Rojas",
                "Zulema Arias",
            ],
        )

    def test_rf03_sin_estudiantes_devuelve_lista_vacia(self):
        self.sql("DELETE FROM estudiantes")

        self.assertEqual(consultar_estudiantes(), [])

    def test_rf03_consultar_no_modifica_datos(self):
        antes = self.conteos()

        consultar_estudiantes()
        consultar_estudiantes()

        self.assertEqual(antes, self.conteos())


class TestRF03MensajeSinEstudiantes(unittest.TestCase):
    """H-08. Lógica del mensaje, sin abrir la interfaz."""

    def setUp(self):
        if tk is None:
            self.skipTest("Tkinter no está instalado.")

        from interfaz.vistas_estudiantes import (
            MENSAJE_SIN_ESTUDIANTES,
            mensaje_consulta_estudiantes,
        )

        self.mensaje_vacio = MENSAJE_SIN_ESTUDIANTES
        self.mensaje_consulta = mensaje_consulta_estudiantes

    def test_rf03_mensaje_cuando_no_hay_estudiantes(self):
        self.assertEqual(self.mensaje_consulta(0), "No hay estudiantes registrados.")
        self.assertEqual(self.mensaje_vacio, "No hay estudiantes registrados.")

    def test_rf03_sin_mensaje_cuando_hay_estudiantes(self):
        self.assertEqual(self.mensaje_consulta(1), "")
        self.assertEqual(self.mensaje_consulta(3), "")


class TestRF03VistaEstudiantes(PruebaConBaseTemporal):
    """H-08. La vista real muestra el mensaje con la tabla vacía."""

    def setUp(self):
        super().setUp()

        if tk is None:
            self.skipTest("Tkinter no está instalado.")

        try:
            self.raiz = tk.Tk()
        except tk.TclError:
            self.skipTest("No hay pantalla disponible para Tkinter.")

        self.raiz.withdraw()

        from interfaz.vistas_estudiantes import VistaEstudiantes

        self.VistaEstudiantes = VistaEstudiantes

    def tearDown(self):
        raiz = getattr(self, "raiz", None)

        if raiz is not None:
            raiz.destroy()

        super().tearDown()

    def test_rf03_vista_muestra_mensaje_con_tabla_vacia(self):
        self.sql("DELETE FROM estudiantes")

        vista = self.VistaEstudiantes(self.raiz)

        self.assertEqual(len(vista.tabla.get_children()), 0)
        self.assertEqual(
            vista.var_mensaje_consulta.get(),
            "No hay estudiantes registrados.",
        )

    def test_rf03_mensaje_desaparece_al_registrar_un_estudiante(self):
        self.sql("DELETE FROM estudiantes")

        vista = self.VistaEstudiantes(self.raiz)

        registrar_estudiante("D001112223", "Ana Mora", "ana@universidad.ac.cr")
        vista.refrescar()

        self.assertEqual(len(vista.tabla.get_children()), 1)
        self.assertEqual(vista.var_mensaje_consulta.get(), "")

    def test_rf03_vista_con_datos_iniciales_no_muestra_mensaje(self):
        vista = self.VistaEstudiantes(self.raiz)

        self.assertEqual(len(vista.tabla.get_children()), 3)
        self.assertEqual(vista.var_mensaje_consulta.get(), "")


if __name__ == "__main__":
    unittest.main()
