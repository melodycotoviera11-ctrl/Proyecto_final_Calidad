"""
Pruebas de H-03, H-09 y H-07 (Fase 3, Grupo 07) para RF-14.

H-03: antes de guardar una serie recurrente no se mostraba una
      previsualización ni se pedía confirmación; los conflictos solo
      aparecían como un error al intentar crearla.
H-09: "cancelar ocurrencias futuras" cancelaba desde la fecha actual y
      no desde la ocurrencia seleccionada por la persona usuaria.
H-07: la suite no cubría de forma suficiente la recurrencia (conflictos
      parciales, auditoría, cancelación de una ocurrencia y de la serie,
      ni la vista real).

Las primeras clases prueban la lógica sin Tkinter (RNF-10). Las últimas
usan las vistas reales sobre una base de datos temporal; los cuadros de
diálogo se reemplazan por respuestas fijas para no depender de clics.
"""

import unittest
from datetime import date, datetime, timedelta
from unittest import mock

from reservaciones.gestion_recurrencia import (
    cancelar_serie_desde_ocurrencia,
    crear_reservacion_recurrente,
    obtener_ocurrencia,
    obtener_serie_id,
    previsualizar_cancelacion_desde_ocurrencia,
    previsualizar_serie_recurrente,
)
from reservaciones.gestion_reservaciones import (
    cancelar_reservacion,
    crear_reservacion,
)
from tests.utilidades import (
    ACTIVO,
    ACTIVO_2,
    AHORA,
    INACTIVO,
    PruebaConBaseTemporal,
)

try:
    import tkinter as tk
except ImportError:  # pragma: no cover
    tk = None


# Fechas de la serie base (lunes), todas posteriores a AHORA.
F1 = "2026-10-12"
F2 = "2026-10-19"
F3 = "2026-10-26"


class BaseRecurrencia(PruebaConBaseTemporal):

    def serie(self, carne=ACTIVO, sala="S01", inicio=F1, hora="10:00",
              duracion=1, personas=1, ocurrencias=3):
        return crear_reservacion_recurrente(
            carne, sala, inicio, hora, duracion, personas, ocurrencias,
            ahora=AHORA,
        )

    def previsualizar(self, carne=ACTIVO, sala="S01", inicio=F1,
                      hora="10:00", duracion=1, personas=1, ocurrencias=3):
        return previsualizar_serie_recurrente(
            carne, sala, inicio, hora, duracion, personas, ocurrencias,
            ahora=AHORA,
        )

    def estados(self):
        return {
            fila[0]: fila[1]
            for fila in self.sql("SELECT id, estado FROM reservaciones")
        }

    def auditoria(self, tipo=None):
        if tipo is None:
            return self.sql("SELECT tipo_accion, entidad, identificador "
                            "FROM auditoria ORDER BY id")

        return self.sql(
            "SELECT tipo_accion, entidad, identificador FROM auditoria "
            "WHERE tipo_accion = ? ORDER BY id",
            (tipo,),
        )


# ---------------------------------------------------------------------
# H-03. Previsualización y confirmación de la serie
# ---------------------------------------------------------------------

class TestH03Previsualizacion(BaseRecurrencia):

    def test_h03_serie_valida_lista_todas_las_ocurrencias(self):
        vista = self.previsualizar(ocurrencias=3)

        self.assertEqual(vista["total"], 3)
        self.assertEqual(vista["validas"], 3)
        self.assertEqual(vista["conflictos"], [])
        self.assertTrue(vista["puede_confirmar"])
        self.assertEqual(
            [o["fecha"] for o in vista["ocurrencias"]],
            [F1, F2, F3],
        )
        self.assertEqual(
            [o["numero"] for o in vista["ocurrencias"]],
            [1, 2, 3],
        )
        self.assertTrue(
            all(o["estado"] == "disponible" for o in vista["ocurrencias"])
        )

    def test_h03_muestra_el_horario_de_cada_ocurrencia(self):
        vista = self.previsualizar(hora="09:00", duracion=2, ocurrencias=2)

        for ocurrencia in vista["ocurrencias"]:
            self.assertEqual(ocurrencia["hora_inicio"], "09:00")
            self.assertEqual(ocurrencia["hora_fin"], "11:00")

    def test_h03_previsualizar_no_guarda_nada(self):
        antes = self.conteos()

        self.previsualizar(ocurrencias=3)

        self.assertEqual(self.conteos(), antes)
        self.assertEqual(self.auditoria(), [])

    def test_h03_previsualizar_con_conflictos_tampoco_guarda(self):
        self.insertar_directo(ACTIVO_2, "S01", F2, "10:00")
        antes = self.conteos()

        self.previsualizar(ocurrencias=3)

        self.assertEqual(self.conteos(), antes)

    def test_h03_resume_conflicto_parcial_en_la_fecha_afectada(self):
        # Solo la segunda semana está ocupada.
        self.insertar_directo(ACTIVO_2, "S01", F2, "10:00")

        vista = self.previsualizar(ocurrencias=3)

        self.assertFalse(vista["puede_confirmar"])
        self.assertEqual(vista["validas"], 2)
        self.assertEqual(
            [o["estado"] for o in vista["ocurrencias"]],
            ["disponible", "conflicto", "disponible"],
        )
        self.assertEqual(len(vista["conflictos"]), 1)
        self.assertIn(F2, vista["conflictos"][0])
        self.assertIn("superpone", vista["ocurrencias"][1]["motivo"])

    def test_h03_resume_todos_los_conflictos_a_la_vez(self):
        self.insertar_directo(ACTIVO_2, "S01", F1, "10:00")
        self.insertar_directo(ACTIVO_2, "S01", F3, "10:00")

        vista = self.previsualizar(ocurrencias=3)

        self.assertFalse(vista["puede_confirmar"])
        self.assertEqual(len(vista["conflictos"]), 2)
        self.assertIn(F1, vista["conflictos"][0])
        self.assertIn(F3, vista["conflictos"][1])

    def test_h03_horario_consecutivo_no_es_conflicto(self):
        # RN-10: una reserva que termina a las 10:00 no choca con 10:00.
        self.insertar_directo(ACTIVO_2, "S01", F2, "09:00", duracion=1)

        vista = self.previsualizar(hora="10:00", ocurrencias=3)

        self.assertTrue(vista["puede_confirmar"])

    def test_h03_sala_fuera_de_servicio_bloquea_la_serie(self):
        vista = self.previsualizar(sala="S04", ocurrencias=2)

        self.assertFalse(vista["puede_confirmar"])
        self.assertEqual(vista["validas"], 0)
        self.assertIn("fuera de servicio", vista["conflictos"][0])

    def test_h03_estudiante_inactivo_bloquea_la_serie(self):
        vista = self.previsualizar(carne=INACTIVO, ocurrencias=2)

        self.assertFalse(vista["puede_confirmar"])
        self.assertIn("inactivo", vista["conflictos"][0])

    def test_h03_capacidad_excedida_bloquea_la_serie(self):
        # S01 admite 4 personas.
        vista = self.previsualizar(personas=5, ocurrencias=2)

        self.assertFalse(vista["puede_confirmar"])
        self.assertEqual(len(vista["conflictos"]), 2)

    def test_h03_hora_invalida_se_informa_por_ocurrencia(self):
        vista = self.previsualizar(hora="10:30", ocurrencias=2)

        self.assertFalse(vista["puede_confirmar"])
        self.assertEqual(
            [o["estado"] for o in vista["ocurrencias"]],
            ["conflicto", "conflicto"],
        )

    def test_h03_horario_que_termina_despues_de_las_20_es_conflicto(self):
        # RN-05: 19:00 con duración 2 terminaría a las 21:00.
        vista = self.previsualizar(hora="19:00", duracion=2, ocurrencias=2)

        self.assertFalse(vista["puede_confirmar"])

    def test_h03_limite_de_tres_reservaciones_se_informa_en_la_serie(self):
        vista = self.previsualizar(ocurrencias=4)

        self.assertFalse(vista["puede_confirmar"])
        self.assertEqual(vista["validas"], 4)
        self.assertEqual(len(vista["conflictos"]), 1)
        self.assertIn("máximo permitido", vista["conflictos"][0])

    def test_h03_serie_de_tres_con_una_previa_supera_el_limite(self):
        self.insertar_directo(ACTIVO, "S02", "2026-10-06", "10:00")

        vista = self.previsualizar(ocurrencias=3)

        self.assertFalse(vista["puede_confirmar"])
        self.assertIn("máximo permitido", vista["conflictos"][0])

    def test_h03_cantidad_de_ocurrencias_fuera_de_rango(self):
        for cantidad in (0, 1, 9, "abc"):
            with self.subTest(cantidad=cantidad):
                with self.assertRaises(ValueError):
                    self.previsualizar(ocurrencias=cantidad)

    def test_h03_fecha_inicial_invalida(self):
        for fecha in ("", "2026-13-01", "12/10/2026", "2026-02-30"):
            with self.subTest(fecha=fecha):
                with self.assertRaises(ValueError):
                    self.previsualizar(inicio=fecha)

    def test_h03_fecha_pasada_es_conflicto_en_la_primera_ocurrencia(self):
        vista = self.previsualizar(inicio="2026-10-01", ocurrencias=2)

        self.assertFalse(vista["puede_confirmar"])
        self.assertEqual(vista["ocurrencias"][0]["estado"], "conflicto")

    def test_h03_resumen_indica_cuando_se_puede_confirmar(self):
        valida = self.previsualizar(ocurrencias=2)
        self.assertIn("Confirme", valida["resumen"])

        self.insertar_directo(ACTIVO_2, "S01", F1, "10:00")
        invalida = self.previsualizar(ocurrencias=2)
        self.assertIn("no puede guardarse", invalida["resumen"])

    def test_h03_previsualizacion_coincide_con_la_creacion_valida(self):
        vista = self.previsualizar(ocurrencias=3)
        self.assertTrue(vista["puede_confirmar"])

        resultado = self.serie(ocurrencias=3)

        fechas = [
            fila[0]
            for fila in self.sql(
                "SELECT fecha FROM reservaciones ORDER BY fecha"
            )
        ]

        self.assertEqual(len(resultado["ids"]), vista["total"])
        self.assertEqual(
            fechas,
            [o["fecha"] for o in vista["ocurrencias"]],
        )

    def test_h03_previsualizacion_coincide_con_el_rechazo_real(self):
        self.insertar_directo(ACTIVO_2, "S01", F2, "10:00")

        vista = self.previsualizar(ocurrencias=3)
        self.assertFalse(vista["puede_confirmar"])

        antes = self.conteos()

        with self.assertRaises(ValueError) as contexto:
            self.serie(ocurrencias=3)

        # El mismo conflicto que anunció la previsualización.
        self.assertIn(F2, str(contexto.exception))
        self.assertEqual(self.conteos(), antes)

    def test_h03_previsualizacion_coincide_con_el_limite_real(self):
        vista = self.previsualizar(ocurrencias=4)
        self.assertFalse(vista["puede_confirmar"])

        with self.assertRaisesRegex(ValueError, "máximo permitido"):
            self.serie(ocurrencias=4)


# ---------------------------------------------------------------------
# H-09. Cancelación desde la ocurrencia seleccionada
# ---------------------------------------------------------------------

class TestH09CancelarDesdeOcurrencia(BaseRecurrencia):

    def preparar(self):
        resultado = self.serie(ocurrencias=3)
        self.serie_id = resultado["serie_id"]
        self.r1, self.r2, self.r3 = resultado["ids"]
        return resultado

    def test_h09_desde_la_segunda_cancela_la_segunda_y_las_posteriores(self):
        self.preparar()

        exito, mensaje, cantidad = cancelar_serie_desde_ocurrencia(
            self.r2, ahora=AHORA
        )

        self.assertTrue(exito, mensaje)
        self.assertEqual(cantidad, 2)
        self.assertEqual(
            self.sql(
                "SELECT fecha, estado FROM reservaciones ORDER BY fecha"
            ),
            [(F1, "activa"), (F2, "cancelada"), (F3, "cancelada")],
        )

    def test_h09_la_ocurrencia_anterior_futura_no_se_cancela(self):
        # Escenario del hallazgo: la primera ocurrencia sigue siendo
        # futura y antes se cancelaba junto con las demás.
        self.preparar()

        cancelar_serie_desde_ocurrencia(self.r3, ahora=AHORA)

        self.assertEqual(
            [fila[0] for fila in self.sql(
                "SELECT estado FROM reservaciones ORDER BY fecha"
            )],
            ["activa", "activa", "cancelada"],
        )

    def test_h09_desde_la_primera_cancela_toda_la_serie(self):
        self.preparar()

        exito, _, cantidad = cancelar_serie_desde_ocurrencia(
            self.r1, ahora=AHORA
        )

        self.assertTrue(exito)
        self.assertEqual(cantidad, 3)
        self.assertEqual(set(self.estados().values()), {"cancelada"})

    def test_h09_desde_la_ultima_cancela_solo_una(self):
        self.preparar()

        exito, mensaje, cantidad = cancelar_serie_desde_ocurrencia(
            self.r3, ahora=AHORA
        )

        self.assertTrue(exito)
        self.assertEqual(cantidad, 1)
        self.assertIn("1 ocurrencia", mensaje)
        self.assertNotIn("ocurrencias", mensaje)

    def test_h09_acepta_el_id_en_cualquier_formato(self):
        self.preparar()

        exito, _, cantidad = cancelar_serie_desde_ocurrencia(
            self.r3.lower(), ahora=AHORA
        )

        self.assertTrue(exito)
        self.assertEqual(cantidad, 1)

    def test_h09_no_toca_otras_series_ni_reservaciones_sueltas(self):
        self.preparar()

        otra = crear_reservacion_recurrente(
            ACTIVO_2, "S02", F2, "14:00", 1, 1, 2, ahora=AHORA
        )
        suelta = crear_reservacion(
            ACTIVO_2, "S03", F3, "08:00", 1, 1, ahora=AHORA
        )[2]

        cancelar_serie_desde_ocurrencia(self.r1, ahora=AHORA)

        estados = self.estados()

        for id_texto in otra["ids"] + [suelta]:
            self.assertEqual(estados[int(id_texto[1:])], "activa", id_texto)

    def test_h09_no_vuelve_a_cancelar_ni_audita_las_ya_canceladas(self):
        self.preparar()
        cancelar_reservacion(self.r3)

        exito, _, cantidad = cancelar_serie_desde_ocurrencia(
            self.r2, ahora=AHORA
        )

        self.assertTrue(exito)
        self.assertEqual(cantidad, 1)

        identificadores = [
            fila[2] for fila in self.auditoria("cancelación")
        ]

        # r3 se canceló manualmente una vez; r2 una vez; nunca repetidas.
        self.assertEqual(sorted(identificadores), sorted([self.r3, self.r2]))

    def test_h09_cada_cancelacion_queda_en_auditoria(self):
        self.preparar()

        cancelar_serie_desde_ocurrencia(self.r2, ahora=AHORA)

        registros = self.auditoria("cancelación")

        self.assertEqual(
            sorted(fila[2] for fila in registros),
            sorted([self.r2, self.r3]),
        )
        self.assertTrue(
            all(fila[1] == "reservación" for fila in registros)
        )

    def test_h09_las_ocurrencias_pasadas_no_se_modifican(self):
        self.preparar()

        # Con "hoy" = 20 de octubre, la primera y la segunda ya pasaron.
        ahora = datetime(2026, 10, 20, 9, 0)

        exito, _, cantidad = cancelar_serie_desde_ocurrencia(
            self.r1, ahora=ahora
        )

        self.assertTrue(exito)
        self.assertEqual(cantidad, 1)
        self.assertEqual(
            [fila[0] for fila in self.sql(
                "SELECT estado FROM reservaciones ORDER BY fecha"
            )],
            ["activa", "activa", "cancelada"],
        )

    def test_h09_sin_ocurrencias_futuras_no_cambia_nada(self):
        self.preparar()
        antes = self.conteos()

        exito, mensaje, cantidad = cancelar_serie_desde_ocurrencia(
            self.r1, ahora=datetime(2026, 12, 1, 9, 0)
        )

        self.assertFalse(exito)
        self.assertEqual(cantidad, 0)
        self.assertIn("No existen ocurrencias", mensaje)
        self.assertEqual(self.conteos(), antes)

    def test_h09_reservacion_no_recurrente_se_rechaza(self):
        id_suelta = crear_reservacion(
            ACTIVO, "S01", F1, "10:00", 1, 1, ahora=AHORA
        )[2]
        antes = self.conteos()

        exito, mensaje, cantidad = cancelar_serie_desde_ocurrencia(
            id_suelta, ahora=AHORA
        )

        self.assertFalse(exito)
        self.assertEqual(cantidad, 0)
        self.assertIn("no pertenece a una serie", mensaje)
        self.assertEqual(self.conteos(), antes)

    def test_h09_id_inexistente_o_invalido_se_rechaza(self):
        self.preparar()
        antes = self.conteos()

        for id_texto in ("R9999", "XYZ", "", None, "R0000"):
            with self.subTest(id=id_texto):
                exito, _, cantidad = cancelar_serie_desde_ocurrencia(
                    id_texto, ahora=AHORA
                )
                self.assertFalse(exito)
                self.assertEqual(cantidad, 0)

        self.assertEqual(self.conteos(), antes)

    def test_h09_previsualizacion_lista_lo_que_se_cancelaria(self):
        self.preparar()
        antes = self.conteos()

        vista = previsualizar_cancelacion_desde_ocurrencia(
            self.r2, ahora=AHORA
        )

        self.assertEqual(vista["serie_id"], self.serie_id)
        self.assertEqual(vista["desde"], F2)
        self.assertEqual(
            vista["ocurrencias"],
            [
                {"id": self.r2, "fecha": F2},
                {"id": self.r3, "fecha": F3},
            ],
        )
        # No modifica nada.
        self.assertEqual(self.conteos(), antes)

    def test_h09_previsualizacion_coincide_con_la_cancelacion(self):
        self.preparar()

        vista = previsualizar_cancelacion_desde_ocurrencia(
            self.r2, ahora=AHORA
        )
        _, _, cantidad = cancelar_serie_desde_ocurrencia(
            self.r2, ahora=AHORA
        )

        self.assertEqual(cantidad, len(vista["ocurrencias"]))

    def test_h09_previsualizacion_de_reservacion_no_recurrente(self):
        id_suelta = crear_reservacion(
            ACTIVO, "S01", F1, "10:00", 1, 1, ahora=AHORA
        )[2]

        self.assertIsNone(
            previsualizar_cancelacion_desde_ocurrencia(
                id_suelta, ahora=AHORA
            )
        )
        self.assertIsNone(
            previsualizar_cancelacion_desde_ocurrencia(
                "R9999", ahora=AHORA
            )
        )

    def test_h09_el_horario_cancelado_queda_disponible(self):
        # RF-09: el horario se libera después de la cancelación.
        self.preparar()

        cancelar_serie_desde_ocurrencia(self.r2, ahora=AHORA)

        exito, mensaje, _ = crear_reservacion(
            ACTIVO_2, "S01", F2, "10:00", 1, 1, ahora=AHORA
        )

        self.assertTrue(exito, mensaje)

    def test_h09_las_canceladas_permanecen_en_el_historial(self):
        self.preparar()

        cancelar_serie_desde_ocurrencia(self.r1, ahora=AHORA)

        total = self.sql("SELECT COUNT(*) FROM reservaciones")[0][0]

        self.assertEqual(total, 3)

    def test_h09_obtener_ocurrencia_devuelve_serie_fecha_y_estado(self):
        self.preparar()

        ocurrencia = obtener_ocurrencia(self.r2)

        self.assertEqual(ocurrencia["id"], self.r2)
        self.assertEqual(ocurrencia["serie_id"], self.serie_id)
        self.assertEqual(ocurrencia["fecha"], F2)
        self.assertEqual(ocurrencia["estado"], "activa")
        self.assertIsNone(obtener_ocurrencia("R9999"))
        self.assertIsNone(obtener_ocurrencia("abc"))


# ---------------------------------------------------------------------
# H-07. Pruebas de recurrencia (RF-14)
# ---------------------------------------------------------------------

class TestH07Recurrencia(BaseRecurrencia):

    def test_h07_la_serie_comparte_serie_id_y_es_semanal(self):
        resultado = self.serie(ocurrencias=3)

        filas = self.sql(
            "SELECT fecha, serie_id, estado FROM reservaciones "
            "ORDER BY fecha"
        )

        self.assertEqual(
            [fila[0] for fila in filas],
            [F1, F2, F3],
        )
        self.assertEqual(
            {fila[1] for fila in filas},
            {resultado["serie_id"]},
        )
        self.assertEqual({fila[2] for fila in filas}, {"activa"})

    def test_h07_los_ids_siguen_el_formato_y_no_se_repiten(self):
        resultado = self.serie(ocurrencias=3)

        self.assertEqual(resultado["ids"], ["R0001", "R0002", "R0003"])

    def test_h07_cada_ocurrencia_creada_queda_en_auditoria(self):
        resultado = self.serie(ocurrencias=3)

        registros = self.auditoria("creación")

        self.assertEqual(
            [fila[2] for fila in registros],
            resultado["ids"],
        )

    def test_h07_conflicto_parcial_no_guarda_ninguna_ocurrencia(self):
        self.insertar_directo(ACTIVO_2, "S01", F2, "10:00")
        antes = self.conteos()

        with self.assertRaisesRegex(ValueError, F2):
            self.serie(ocurrencias=3)

        self.assertEqual(self.conteos(), antes)
        self.assertEqual(self.auditoria(), [])

    def test_h07_estudiante_inactivo_no_crea_serie(self):
        antes = self.conteos()

        with self.assertRaisesRegex(ValueError, "inactivo"):
            self.serie(carne=INACTIVO, ocurrencias=2)

        self.assertEqual(self.conteos(), antes)

    def test_h07_estudiante_inexistente_no_crea_serie(self):
        antes = self.conteos()

        with self.assertRaisesRegex(ValueError, "registrado"):
            self.serie(carne="Z999999999", ocurrencias=2)

        self.assertEqual(self.conteos(), antes)

    def test_h07_sala_fuera_de_servicio_no_crea_serie(self):
        antes = self.conteos()

        with self.assertRaisesRegex(ValueError, "fuera de servicio"):
            self.serie(sala="S04", ocurrencias=2)

        self.assertEqual(self.conteos(), antes)

    def test_h07_capacidad_excedida_no_crea_serie(self):
        antes = self.conteos()

        with self.assertRaises(ValueError):
            self.serie(sala="S05", personas=2, ocurrencias=2)

        self.assertEqual(self.conteos(), antes)

    def test_h07_capacidad_exacta_se_acepta(self):
        resultado = self.serie(sala="S01", personas=4, ocurrencias=2)

        self.assertEqual(len(resultado["ids"]), 2)

    def test_h07_limites_de_horario(self):
        for hora, duracion, valido in (
            ("08:00", 1, True),
            ("19:00", 1, True),
            ("18:00", 2, True),
            ("19:00", 2, False),
            ("07:00", 1, False),
            ("20:00", 1, False),
        ):
            with self.subTest(hora=hora, duracion=duracion):
                vista = self.previsualizar(
                    hora=hora, duracion=duracion, ocurrencias=2
                )
                self.assertEqual(vista["puede_confirmar"], valido)

    def test_h07_duracion_invalida_no_crea_serie(self):
        antes = self.conteos()

        with self.assertRaises(ValueError):
            self.serie(duracion=3, ocurrencias=2)

        self.assertEqual(self.conteos(), antes)

    def test_h07_cantidad_de_personas_invalida_no_crea_serie(self):
        for personas in (0, -1, "1.5", "abc"):
            with self.subTest(personas=personas):
                with self.assertRaises(ValueError):
                    self.serie(personas=personas, ocurrencias=2)

        self.assertEqual(self.sql("SELECT COUNT(*) FROM reservaciones")[0][0], 0)

    def test_h07_fecha_inicial_pasada_no_crea_serie(self):
        with self.assertRaises(ValueError):
            self.serie(inicio="2026-10-01", ocurrencias=2)

    def test_h07_cancelar_una_sola_ocurrencia_conserva_las_demas(self):
        resultado = self.serie(ocurrencias=3)

        exito, mensaje, _ = cancelar_reservacion(resultado["ids"][1])

        self.assertTrue(exito, mensaje)
        self.assertEqual(
            [fila[0] for fila in self.sql(
                "SELECT estado FROM reservaciones ORDER BY fecha"
            )],
            ["activa", "cancelada", "activa"],
        )

    def test_h07_cancelar_ocurrencia_repetida_se_informa(self):
        resultado = self.serie(ocurrencias=2)
        cancelar_reservacion(resultado["ids"][0])

        exito, mensaje, _ = cancelar_reservacion(resultado["ids"][0])

        self.assertFalse(exito)
        self.assertIn("ya se encuentra cancelada", mensaje)

    def test_h07_cancelar_toda_la_serie_desde_la_primera(self):
        resultado = self.serie(ocurrencias=3)

        exito, _, cantidad = cancelar_serie_desde_ocurrencia(
            resultado["ids"][0], ahora=AHORA
        )

        self.assertTrue(exito)
        self.assertEqual(cantidad, 3)

    def test_h07_obtener_serie_id(self):
        resultado = self.serie(ocurrencias=2)
        suelta = crear_reservacion(
            ACTIVO_2, "S02", F1, "12:00", 1, 1, ahora=AHORA
        )[2]

        self.assertEqual(
            obtener_serie_id(resultado["ids"][0]),
            resultado["serie_id"],
        )
        self.assertIsNone(obtener_serie_id(suelta))
        self.assertIsNone(obtener_serie_id("R9999"))
        self.assertIsNone(obtener_serie_id("abc"))

    def test_h07_se_puede_reservar_de_nuevo_tras_cancelar_la_serie(self):
        resultado = self.serie(ocurrencias=3)
        cancelar_serie_desde_ocurrencia(resultado["ids"][0], ahora=AHORA)

        # Con la serie cancelada ya no cuenta para el máximo de tres.
        nueva = self.serie(sala="S02", ocurrencias=3)

        self.assertEqual(len(nueva["ids"]), 3)


# ---------------------------------------------------------------------
# Vistas reales (Tkinter)
# ---------------------------------------------------------------------

class BaseVista(PruebaConBaseTemporal):

    def setUp(self):
        super().setUp()

        if tk is None:
            self.skipTest("Tkinter no está instalado.")

        try:
            self.raiz = tk.Tk()
        except tk.TclError:
            self.skipTest("No hay pantalla disponible para Tkinter.")

        self.raiz.withdraw()

        from interfaz.vistas_reservaciones import configurar_estilos

        configurar_estilos(self.raiz)

    def tearDown(self):
        raiz = getattr(self, "raiz", None)

        if raiz is not None:
            raiz.destroy()

        super().tearDown()

    @staticmethod
    def dias(cantidad):
        return (date.today() + timedelta(days=cantidad)).isoformat()


class TestH03VistaRecurrencia(BaseVista):

    def setUp(self):
        super().setUp()

        # Si el flujo regresara a guardar sin confirmar, el cuadro de
        # mensaje real bloquearía la prueba en lugar de hacerla fallar.
        parche = mock.patch("interfaz.vistas_recurrencia.messagebox")
        self.caja = parche.start()
        self.addCleanup(parche.stop)

    def vista(self):
        from interfaz.vistas_recurrencia import VistaReservacionRecurrente

        vista = VistaReservacionRecurrente(self.raiz)
        vista.var_carne.set(ACTIVO)
        vista.var_sala.set("S01 - Sala Biblioteca 1")
        vista.var_fecha.set(self.dias(1))
        vista.var_hora.set("10:00")
        vista.var_duracion.set("1")
        vista.var_cantidad.set("1")
        vista.var_ocurrencias.set("3")
        return vista

    def total(self):
        return self.sql("SELECT COUNT(*) FROM reservaciones")[0][0]

    def test_h03_crear_muestra_la_previsualizacion_antes_de_guardar(self):
        vista = self.vista()
        vistas_previas = []

        def espiar(vista_previa, solo_consulta=False):
            # Al mostrarse el diálogo todavía no existe nada guardado.
            vistas_previas.append((vista_previa, self.total()))
            return False

        with mock.patch.object(vista, "_mostrar_dialogo", side_effect=espiar):
            vista.crear()

        self.assertEqual(len(vistas_previas), 1)
        vista_previa, guardadas = vistas_previas[0]
        self.assertEqual(guardadas, 0)
        self.assertEqual(vista_previa["total"], 3)
        self.assertTrue(vista_previa["puede_confirmar"])

    def test_h03_sin_confirmacion_no_se_guarda_la_serie(self):
        vista = self.vista()

        with mock.patch.object(vista, "_mostrar_dialogo", return_value=False):
            vista.crear()

        self.assertEqual(self.total(), 0)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM auditoria")[0][0], 0)
        # Los datos escritos se conservan para poder corregirlos.
        self.assertEqual(vista.var_carne.get(), ACTIVO)

    def test_h03_con_confirmacion_se_guarda_la_serie(self):
        vista = self.vista()
        cambios = []
        vista.on_cambio = lambda: cambios.append(True)

        with mock.patch.object(vista, "_mostrar_dialogo", return_value=True):
            vista.crear()

        self.assertEqual(self.total(), 3)
        self.caja.showinfo.assert_called_once()
        self.assertEqual(cambios, [True])
        # El formulario se limpia tras guardar.
        self.assertEqual(vista.var_carne.get(), "")

    def test_h03_serie_con_conflictos_se_muestra_sin_poder_confirmar(self):
        self.insertar_directo(ACTIVO_2, "S01", self.dias(8), "10:00")
        vista = self.vista()
        recibidas = []

        def espiar(vista_previa, solo_consulta=False):
            recibidas.append(vista_previa)
            return False

        with mock.patch.object(vista, "_mostrar_dialogo", side_effect=espiar):
            vista.crear()

        self.assertFalse(recibidas[0]["puede_confirmar"])
        self.assertEqual(len(recibidas[0]["conflictos"]), 1)
        self.assertEqual(self.total(), 1)

    def test_h03_datos_invalidos_muestran_error_y_no_abren_el_dialogo(self):
        vista = self.vista()
        vista.var_ocurrencias.set("9")

        with mock.patch.object(vista, "_mostrar_dialogo") as dialogo:
            vista.crear()

        dialogo.assert_not_called()
        self.caja.showerror.assert_called_once()
        self.assertEqual(self.total(), 0)

    def test_h03_previsualizar_no_guarda_y_solo_consulta(self):
        vista = self.vista()

        with mock.patch.object(
            vista, "_mostrar_dialogo", return_value=True
        ) as dialogo:
            vista.previsualizar()

        dialogo.assert_called_once()
        self.assertTrue(dialogo.call_args.kwargs["solo_consulta"])
        self.assertEqual(self.total(), 0)

    def test_h03_el_dialogo_real_lista_cada_ocurrencia(self):
        from interfaz.vistas_recurrencia import DialogoPrevisualizacionSerie

        vista_previa = previsualizar_serie_recurrente(
            ACTIVO, "S01", self.dias(1), "10:00", 1, 1, 3
        )
        dialogo = DialogoPrevisualizacionSerie(self.raiz, vista_previa)

        try:
            filas = [
                dialogo.tabla.item(item, "values")
                for item in dialogo.tabla.get_children()
            ]

            self.assertEqual(len(filas), 3)
            self.assertEqual(
                [fila[3] for fila in filas],
                ["Disponible"] * 3,
            )
            self.assertEqual(filas[0][2], "10:00 a 11:00")
        finally:
            dialogo.destroy()

    def test_h03_el_dialogo_confirma_solo_si_la_serie_es_valida(self):
        from interfaz.vistas_recurrencia import DialogoPrevisualizacionSerie

        valida = previsualizar_serie_recurrente(
            ACTIVO, "S01", self.dias(1), "10:00", 1, 1, 2
        )
        dialogo = DialogoPrevisualizacionSerie(self.raiz, valida)
        self.assertFalse(dialogo.confirmado)
        dialogo.confirmar()
        self.assertTrue(dialogo.confirmado)

        invalida = previsualizar_serie_recurrente(
            ACTIVO, "S04", self.dias(1), "10:00", 1, 1, 2
        )
        dialogo = DialogoPrevisualizacionSerie(self.raiz, invalida)

        try:
            self.assertIn(
                "disabled", dialogo.boton_confirmar.state()
            )
            dialogo.confirmar()
            self.assertFalse(dialogo.confirmado)
            self.assertEqual(
                [
                    dialogo.tabla.item(item, "values")[3]
                    for item in dialogo.tabla.get_children()
                ],
                ["Conflicto", "Conflicto"],
            )
        finally:
            dialogo.destroy()

    def test_h03_volver_y_corregir_no_confirma(self):
        from interfaz.vistas_recurrencia import DialogoPrevisualizacionSerie

        valida = previsualizar_serie_recurrente(
            ACTIVO, "S01", self.dias(1), "10:00", 1, 1, 2
        )
        dialogo = DialogoPrevisualizacionSerie(self.raiz, valida)
        dialogo.cancelar()

        self.assertFalse(dialogo.confirmado)


class TestH09VistaGestion(BaseVista):

    def setUp(self):
        super().setUp()

        parche = mock.patch("interfaz.vistas_gestion_reservas.messagebox")
        self.caja = parche.start()
        self.addCleanup(parche.stop)

        # Por defecto la persona no confirma; cada prueba lo indica.
        self.caja.askyesno.return_value = False

    def preparar(self):
        resultado = crear_reservacion_recurrente(
            ACTIVO, "S01", self.dias(1), "10:00", 1, 1, 3
        )
        self.r1, self.r2, self.r3 = resultado["ids"]

        from interfaz.vistas_gestion_reservas import (
            VistaGestionReservaciones,
        )

        self.vista = VistaGestionReservaciones(self.raiz)

    def seleccionar(self, id_reservacion):
        arbol = self.vista.tabla.arbol

        for item in arbol.get_children():
            if arbol.item(item, "values")[0] == id_reservacion:
                arbol.selection_set(item)
                self.vista._seleccionar_reservacion()
                return

        self.fail(f"No aparece {id_reservacion} en la tabla.")

    def estados(self):
        return [
            fila[0]
            for fila in self.sql(
                "SELECT estado FROM reservaciones ORDER BY fecha"
            )
        ]

    def test_h09_cancela_desde_la_ocurrencia_seleccionada(self):
        self.preparar()
        self.seleccionar(self.r2)
        cambios = []
        self.vista.on_cambio = lambda: cambios.append(True)

        self.caja.askyesno.return_value = True
        self.vista.cancelar_ocurrencias_futuras()

        self.assertEqual(self.estados(), ["activa", "cancelada", "cancelada"])
        self.caja.showinfo.assert_called_once()
        self.assertEqual(cambios, [True])

    def test_h09_la_confirmacion_indica_lo_que_se_cancelara(self):
        self.preparar()
        self.seleccionar(self.r2)

        self.caja.askyesno.return_value = False
        self.vista.cancelar_ocurrencias_futuras()

        texto = self.caja.askyesno.call_args.args[1]

        self.assertIn("2 ocurrencia", texto)
        self.assertIn(self.r2, texto)
        self.assertIn(self.r3, texto)
        self.assertNotIn(self.r1, texto)
        self.assertIn("anteriores no serán modificadas", texto)

    def test_h09_si_la_persona_no_confirma_no_se_cancela_nada(self):
        self.preparar()
        self.seleccionar(self.r1)

        self.caja.askyesno.return_value = False
        self.vista.cancelar_ocurrencias_futuras()

        self.assertEqual(self.estados(), ["activa"] * 3)
        self.caja.showinfo.assert_not_called()

    def test_h09_sin_seleccion_pide_seleccionar(self):
        self.preparar()

        self.vista.cancelar_ocurrencias_futuras()

        self.caja.showerror.assert_called_once()
        self.caja.askyesno.assert_not_called()
        self.assertEqual(self.estados(), ["activa"] * 3)

    def test_h09_reservacion_no_recurrente_muestra_advertencia(self):
        self.preparar()
        id_suelta = crear_reservacion(
            ACTIVO_2, "S02", self.dias(2), "10:00", 1, 1
        )[2]
        self.vista.refrescar()
        self.seleccionar(id_suelta)

        self.vista.cancelar_ocurrencias_futuras()

        self.caja.showwarning.assert_called_once()
        self.caja.askyesno.assert_not_called()
        self.assertEqual(self.estados().count("cancelada"), 0)

    def test_h09_cancelar_una_sola_ocurrencia_no_afecta_a_las_demas(self):
        self.preparar()
        self.seleccionar(self.r2)

        self.caja.askyesno.return_value = True
        self.vista.cancelar()

        self.assertEqual(self.estados(), ["activa", "cancelada", "activa"])


if __name__ == "__main__":
    unittest.main()