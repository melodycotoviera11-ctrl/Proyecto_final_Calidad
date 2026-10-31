"""
Pruebas de H-02 (Fase 3, Grupo 07): RF-17 en estudiantes y salas.

La auditoría solo registraba las operaciones de reservaciones. Se
comprueba que las altas y modificaciones de estudiantes y salas quedan
registradas con fecha y hora, acción, entidad e identificador, y que
una operación rechazada no deja ningún registro.
"""

import unittest
from datetime import datetime

from estudiantes.gestion_estudiantes import (
    modificar_estudiante,
    registrar_estudiante,
)
from reservaciones.gestion_reservaciones import consultar_auditoria
from salas.gestion_salas import modificar_sala, registrar_sala
from tests.utilidades import PruebaConBaseTemporal


class TestH02AuditoriaCatalogos(PruebaConBaseTemporal):

    def auditoria(self):
        return self.sql(
            "SELECT tipo_accion, entidad, identificador "
            "FROM auditoria ORDER BY id"
        )

    # --- Estudiantes ------------------------------------------------

    def test_h02_registrar_estudiante_audita_creacion(self):
        exito, mensaje = registrar_estudiante(
            "Z000000001", "Ana Prueba", "ana@u.ac.cr"
        )

        self.assertTrue(exito, mensaje)
        self.assertEqual(
            self.auditoria(),
            [("creación", "estudiante", "Z000000001")],
        )

    def test_h02_modificar_estudiante_audita_modificacion(self):
        registrar_estudiante("Z000000001", "Ana Prueba", "ana@u.ac.cr")

        exito, mensaje = modificar_estudiante(
            "Z000000001", "Ana P", "ana@u.ac.cr", "inactivo"
        )

        self.assertTrue(exito, mensaje)
        self.assertEqual(
            self.auditoria(),
            [
                ("creación", "estudiante", "Z000000001"),
                ("modificación", "estudiante", "Z000000001"),
            ],
        )

    def test_h02_estudiante_rechazado_no_audita(self):
        registrar_estudiante("Z000000001", "Ana Prueba", "ana@u.ac.cr")
        antes = self.auditoria()

        # Carné duplicado con otra capitalización, correo inválido y
        # estudiante inexistente.
        self.assertFalse(
            registrar_estudiante("z000000001", "Otra", "otra@u.ac.cr")[0]
        )
        self.assertFalse(
            modificar_estudiante("Z000000001", "Ana", "sin-arroba", "activo")[0]
        )
        self.assertFalse(
            modificar_estudiante("Y999999999", "Nadie", "n@u.ac.cr", "activo")[0]
        )

        self.assertEqual(self.auditoria(), antes)

    # --- Salas ------------------------------------------------------

    def test_h02_registrar_sala_audita_creacion(self):
        exito, mensaje = registrar_sala("S06", "Sala 6", 3)

        self.assertTrue(exito, mensaje)
        self.assertEqual(
            self.auditoria(),
            [("creación", "sala", "S06")],
        )

    def test_h02_modificar_sala_audita_modificacion(self):
        registrar_sala("S06", "Sala 6", 3)

        exito, mensaje = modificar_sala("S06", "Sala 6b", 5, "disponible")

        self.assertTrue(exito, mensaje)
        self.assertEqual(
            self.auditoria(),
            [
                ("creación", "sala", "S06"),
                ("modificación", "sala", "S06"),
            ],
        )

    def test_h02_sala_rechazada_no_audita(self):
        antes = self.auditoria()

        self.assertFalse(registrar_sala("S01", "Duplicada", 3)[0])
        self.assertFalse(registrar_sala("S07", "Sala 7", 0)[0])
        self.assertFalse(modificar_sala("S99", "No existe", 3, "disponible")[0])

        self.assertEqual(self.auditoria(), antes)

    # --- Escenario completo de la Fase 3 ----------------------------

    def test_h02_escenario_del_hallazgo_registra_cuatro_eventos(self):
        """Pasos 1 a 4 del hallazgo: deben quedar 4 registros completos."""
        registrar_estudiante("Z000000001", "Ana Prueba", "ana@u.ac.cr")
        modificar_estudiante("Z000000001", "Ana P", "ana@u.ac.cr", "inactivo")
        registrar_sala("S06", "Sala 6", 3)
        modificar_sala("S06", "Sala 6b", 5, "disponible")

        eventos = consultar_auditoria()

        self.assertEqual(len(eventos), 4)

        for _id, fecha_hora, accion, entidad, identificador in eventos:
            datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M:%S")
            self.assertIn(accion, ("creación", "modificación"))
            self.assertIn(entidad, ("estudiante", "sala"))
            self.assertIn(identificador, ("Z000000001", "S06"))


if __name__ == "__main__":
    unittest.main()
