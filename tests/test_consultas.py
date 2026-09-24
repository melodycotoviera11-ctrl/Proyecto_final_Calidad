"""Pruebas de RF-06 (consultar reservaciones) y RF-07 (buscar por estudiante)."""

import unittest

from reservaciones.gestion_reservaciones import (
    COLUMNAS_RESERVACION, buscar_por_estudiante, consultar_reservaciones,
)
from tests.utilidades import ACTIVO, ACTIVO_2, INACTIVO, PruebaConBaseTemporal


class TestConsultarReservaciones(PruebaConBaseTemporal):

    def test_sin_registros_devuelve_lista_vacia(self):
        self.assertEqual(consultar_reservaciones(), [])

    def test_incluye_activas_y_canceladas_con_detalle(self):
        id_activa = self.insertar_directo(ACTIVO, "S01", "2026-10-06", "10:00", 2, 3)
        id_cancelada = self.insertar_directo(ACTIVO_2, "S02", "2026-10-06", "14:00",
                                             1, 1, "cancelada")
        filas = consultar_reservaciones()

        self.assertEqual(len(filas), 2)
        self.assertEqual(len(filas[0]), len(COLUMNAS_RESERVACION))
        self.assertEqual(
            filas[0],
            (id_activa, ACTIVO, "Andrea Solano", "S01", "Sala Biblioteca 1",
             "2026-10-06", "10:00", "12:00", 3, "activa"),
        )
        self.assertEqual(filas[1][0], id_cancelada)
        self.assertEqual(filas[1][-1], "cancelada")

    def test_orden_por_fecha_y_hora(self):
        self.insertar_directo(ACTIVO, "S01", "2026-10-08", "09:00")
        self.insertar_directo(ACTIVO, "S01", "2026-10-06", "15:00")
        self.insertar_directo(ACTIVO, "S02", "2026-10-06", "08:00")
        self.insertar_directo(ACTIVO, "S03", "2026-10-07", "12:00")

        orden = [(f[5], f[6]) for f in consultar_reservaciones()]
        self.assertEqual(orden, [
            ("2026-10-06", "08:00"), ("2026-10-06", "15:00"),
            ("2026-10-07", "12:00"), ("2026-10-08", "09:00"),
        ])

    def test_conserva_tildes_y_enie(self):
        # RNF-08: los nombres con tildes y ñ se recuperan sin alterarse.
        self.sql("INSERT INTO estudiantes VALUES ('N000000001', 'Íñigo Muñoz', "
                 "'inigo@universidad.ac.cr', 'activo')")
        self.insertar_directo("N000000001", "S05", "2026-10-06", "10:00")
        fila = consultar_reservaciones()[0]
        self.assertEqual(fila[2], "Íñigo Muñoz")
        self.assertEqual(fila[4], "Cubículo individual")


class TestBuscarPorEstudiante(PruebaConBaseTemporal):

    def test_carne_sin_distinguir_mayusculas(self):
        self.insertar_directo(ACTIVO, "S01", "2026-10-06", "10:00")
        for carne in (ACTIVO, ACTIVO.lower(), "  a001234567  "):
            with self.subTest(carne=carne):
                exito, _, filas = buscar_por_estudiante(carne)
                self.assertTrue(exito)
                self.assertEqual(len(filas), 1)

    def test_carne_no_registrado(self):
        exito, mensaje, filas = buscar_por_estudiante("Z999999999")
        self.assertFalse(exito)
        self.assertIn("no corresponde a ningún estudiante", mensaje)
        self.assertEqual(filas, [])

    def test_estudiante_sin_reservaciones(self):
        exito, mensaje, filas = buscar_por_estudiante(ACTIVO_2)
        self.assertTrue(exito)
        self.assertIn("no posee reservaciones", mensaje)
        self.assertEqual(filas, [])

    def test_estudiante_inactivo_tambien_se_consulta(self):
        self.insertar_directo(INACTIVO, "S01", "2026-09-01", "10:00")
        exito, _, filas = buscar_por_estudiante(INACTIVO)
        self.assertTrue(exito)
        self.assertEqual(len(filas), 1)

    def test_incluye_canceladas_y_solo_del_estudiante(self):
        self.insertar_directo(ACTIVO, "S01", "2026-10-06", "10:00")
        self.insertar_directo(ACTIVO, "S02", "2026-10-07", "10:00", estado="cancelada")
        self.insertar_directo(ACTIVO_2, "S03", "2026-10-06", "10:00")

        exito, mensaje, filas = buscar_por_estudiante(ACTIVO)
        self.assertTrue(exito)
        self.assertIn("2 reservaciones", mensaje)
        self.assertEqual({f[1] for f in filas}, {ACTIVO})
        self.assertEqual({f[-1] for f in filas}, {"activa", "cancelada"})

    def test_mismo_detalle_que_consulta_general(self):
        self.insertar_directo(ACTIVO, "S01", "2026-10-06", "10:00", 2, 3)
        _, _, filas = buscar_por_estudiante(ACTIVO)
        self.assertEqual(filas, consultar_reservaciones())

    def test_carne_vacio(self):
        for carne in ("", "   ", None):
            with self.subTest(carne=carne):
                exito, mensaje, filas = buscar_por_estudiante(carne)
                self.assertFalse(exito)
                self.assertIn("obligatorio", mensaje)
                self.assertEqual(filas, [])


if __name__ == "__main__":
    unittest.main()
