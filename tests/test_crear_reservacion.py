"""Pruebas de RF-05 (crear reservación) y reglas RN-01 a RN-11 y RN-13."""

import unittest

from reservaciones.gestion_reservaciones import crear_reservacion
from tests.utilidades import (
    ACTIVO, ACTIVO_2, AHORA, HOY, INACTIVO, MANANA, PASADO_MANANA,
    PruebaConBaseTemporal,
)


class TestCrearReservacion(PruebaConBaseTemporal):

    def crear(self, carne=ACTIVO, sala="S02", fecha=MANANA, hora="10:00",
              duracion=1, cantidad=2):
        return crear_reservacion(carne, sala, fecha, hora, duracion, cantidad,
                                 ahora=AHORA)

    def assertRechazo(self, resultado, fragmento):
        """Rechazo con motivo claro y sin cambios en la base de datos."""
        exito, mensaje, id_reservacion = resultado
        self.assertFalse(exito)
        self.assertIsNone(id_reservacion)
        self.assertIn(fragmento, mensaje)
        self.assertNotIn("Traceback", mensaje)

    # --- Caso exitoso --------------------------------------------------

    def test_crea_reservacion_valida(self):
        exito, mensaje, id_reservacion = self.crear()

        self.assertTrue(exito)
        self.assertIsInstance(id_reservacion, int)
        self.assertIn(f"ID {id_reservacion}", mensaje)

        fila = self.sql(
            "SELECT carne, codigo_sala, fecha, hora_inicio, duracion, "
            "cantidad_personas, estado FROM reservaciones WHERE id = ?",
            (id_reservacion,),
        )
        self.assertEqual(
            fila, [(ACTIVO, "S02", MANANA, "10:00", 1, 2, "activa")]
        )

    def test_registra_auditoria_de_creacion(self):
        _, _, id_reservacion = self.crear()
        auditoria = self.sql("SELECT tipo_accion, entidad, identificador FROM auditoria")
        self.assertEqual(auditoria, [("creación", "reservación", str(id_reservacion))])

    def test_normaliza_carne_sala_y_hora(self):
        exito, _, id_reservacion = self.crear(carne="  a001234567 ", sala="s02",
                                              hora="9:00", duracion="2", cantidad="3")
        self.assertTrue(exito)
        fila = self.sql("SELECT carne, codigo_sala, hora_inicio, duracion, "
                        "cantidad_personas FROM reservaciones WHERE id = ?",
                        (id_reservacion,))
        self.assertEqual(fila, [(ACTIVO, "S02", "09:00", 2, 3)])

    def test_reservacion_hoy_hora_futura(self):
        exito, _, _ = self.crear(fecha=HOY, hora="10:00")
        self.assertTrue(exito)

    def test_ids_unicos_y_no_reutilizados(self):
        # RN-13: el ID de una cancelada nunca se reutiliza.
        _, _, primero = self.crear()
        self.sql("UPDATE reservaciones SET estado = 'cancelada' WHERE id = ?", (primero,))
        _, _, segundo = self.crear()
        self.assertGreater(segundo, primero)

        self.sql("DELETE FROM reservaciones WHERE id = ?", (segundo,))
        _, _, tercero = self.crear()
        self.assertGreater(tercero, segundo)

    # --- RN-01 / RN-08 ----------------------------------------------------

    def test_estudiante_inexistente(self):
        self.assertRechazo(self.crear(carne="Z999999999"), "no corresponde a ningún estudiante")

    def test_estudiante_inactivo(self):
        self.assertRechazo(self.crear(carne=INACTIVO), "inactivo")

    def test_sala_inexistente(self):
        self.assertRechazo(self.crear(sala="S99"), "La sala S99 no existe")

    def test_sala_fuera_de_servicio(self):
        self.assertRechazo(self.crear(sala="S04"), "fuera de servicio")

    # --- RN-02 a RN-07 ----------------------------------------------------

    def test_fecha_pasada(self):
        self.assertRechazo(self.crear(fecha="2026-10-04"), "anterior a la fecha actual")

    def test_hoy_hora_pasada(self):
        self.assertRechazo(self.crear(fecha=HOY, hora="09:00"), "posterior a la hora actual")

    def test_formato_fecha(self):
        self.assertRechazo(self.crear(fecha="06-10-2026"), "AAAA-MM-DD")

    def test_hora_no_completa(self):
        self.assertRechazo(self.crear(hora="10:30"), "hora completa")

    def test_fuera_de_horario(self):
        self.assertRechazo(self.crear(hora="19:00", duracion=2), "08:00 a 20:00")
        self.assertRechazo(self.crear(hora="07:00"), "08:00 a 20:00")

    def test_duracion_invalida(self):
        self.assertRechazo(self.crear(duracion=3), "1 o 2 horas")

    def test_capacidad_superada(self):
        self.assertRechazo(self.crear(sala="S05", cantidad=2), "supera la capacidad")

    def test_capacidad_exacta_permitida(self):
        exito, _, _ = self.crear(sala="S01", cantidad=4)
        self.assertTrue(exito)

    def test_cantidad_cero(self):
        self.assertRechazo(self.crear(cantidad=0), "mayor que cero")

    # --- RN-09 / RN-10 / RN-12 ----------------------------------------------

    def test_superposicion_rechazada(self):
        self.crear(hora="10:00", duracion=2)
        self.assertRechazo(self.crear(carne=ACTIVO_2, hora="11:00"), "se superpone")

    def test_superposicion_otra_sala_permitida(self):
        self.crear(hora="10:00", duracion=2)
        exito, _, _ = self.crear(carne=ACTIVO_2, sala="S03", hora="11:00")
        self.assertTrue(exito)

    def test_consecutivas_permitidas(self):
        self.crear(hora="10:00", duracion=2)
        exito, _, _ = self.crear(carne=ACTIVO_2, hora="12:00")
        self.assertTrue(exito)
        exito, _, _ = self.crear(carne=ACTIVO_2, hora="09:00")
        self.assertTrue(exito)

    def test_cancelada_no_bloquea_horario(self):
        self.insertar_directo(ACTIVO_2, "S02", MANANA, "10:00", 2, 1, "cancelada")
        exito, _, _ = self.crear(hora="10:00")
        self.assertTrue(exito)

    # --- RN-11 --------------------------------------------------------------

    def test_maximo_tres_vigentes(self):
        for hora in ("08:00", "10:00", "12:00"):
            exito, _, _ = self.crear(hora=hora)
            self.assertTrue(exito)

        self.assertRechazo(self.crear(fecha=PASADO_MANANA), "máximo permitido")

    def test_pasadas_y_canceladas_no_cuentan_para_el_limite(self):
        self.insertar_directo(ACTIVO, "S01", "2026-10-01", "10:00")          # pasada
        self.insertar_directo(ACTIVO, "S01", HOY, "08:00")                   # terminó 09:00
        self.insertar_directo(ACTIVO, "S01", MANANA, "15:00", estado="cancelada")
        for hora in ("08:00", "10:00", "12:00"):
            exito, mensaje, _ = self.crear(hora=hora)
            self.assertTrue(exito, mensaje)

    def test_reservacion_en_curso_cuenta_para_el_limite(self):
        # Hoy 09:00-11:00 sigue en curso a las 09:30: es "presente".
        self.insertar_directo(ACTIVO, "S01", HOY, "09:00", 2)
        self.crear(hora="08:00")
        self.crear(hora="10:00")
        self.assertRechazo(self.crear(hora="12:00"), "máximo permitido")

    # --- RNF-05 / RNF-06: entradas inválidas sin efectos -------------------

    def test_bateria_entradas_invalidas_no_modifica_bd(self):
        estado_inicial = self.conteos()
        casos = [
            dict(carne=None), dict(carne=""), dict(carne="   "),
            dict(sala=None), dict(sala=""),
            dict(fecha=None), dict(fecha=""), dict(fecha=20261006), dict(fecha=["x"]),
            dict(hora=None), dict(hora=""), dict(hora=10), dict(hora="10"),
            dict(duracion=None), dict(duracion=""), dict(duracion=1.5), dict(duracion=True),
            dict(cantidad=None), dict(cantidad=""), dict(cantidad=-1),
            dict(cantidad="dos"), dict(cantidad=2.0),
        ]
        for caso in casos:
            with self.subTest(**{k: repr(val) for k, val in caso.items()}):
                exito, mensaje, id_reservacion = self.crear(**caso)
                self.assertFalse(exito)
                self.assertIsNone(id_reservacion)
                self.assertTrue(mensaje)

        self.assertEqual(self.conteos(), estado_inicial)

    def test_rechazo_por_regla_no_deja_auditoria(self):
        self.crear(hora="10:00")
        estado = self.conteos()
        self.crear(carne=ACTIVO_2, hora="10:00")   # superposición
        self.assertEqual(self.conteos(), estado)


if __name__ == "__main__":
    unittest.main()
