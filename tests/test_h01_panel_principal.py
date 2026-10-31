"""
Pruebas de H-01 y H-07 (Fase 3, Grupo 07) para RF-15.

H-01: con el filtro de fecha por defecto (hoy), la tabla "Próximas
reservaciones" quedaba vacía aunque hubiera reservaciones activas en
los días siguientes.

H-07: las pruebas anteriores del panel usaban simulaciones sobre
PanelReservaciones (que la ventana principal no usa) y no ejercían los
filtros. Estas pruebas ejercen la lógica real (reservaciones/panel.py)
y la vista real VistaPanelPrincipal sobre una base temporal.
"""

import unittest
from datetime import datetime

from reservaciones.gestion_reservaciones import (
    cancelar_reservacion,
    consultar_reservaciones,
    crear_reservacion,
    modificar_reservacion,
)
from reservaciones.panel import (
    MENSAJE_SIN_RESULTADOS,
    calcular_ocupacion,
    datos_panel,
    filtrar_reservaciones,
    interpretar_filtros,
    obtener_proximas,
)
from salas.gestion_salas import consultar_salas
from tests.utilidades import (
    ACTIVO,
    ACTIVO_2,
    AHORA,
    HOY,
    MANANA,
    PASADO_MANANA,
    PruebaConBaseTemporal,
)

try:
    import tkinter as tk
except ImportError:  # pragma: no cover
    tk = None


def ids(filas):
    return [fila[0] for fila in filas]


class EscenarioPanel(PruebaConBaseTemporal):
    """Datos del hallazgo H-01 más casos de hoy, cancelados y pasados."""

    def preparar_escenario(self):
        # Escenario exacto de la Fase 3: dos reservaciones para mañana.
        self.r_manana_1 = self.crear(ACTIVO, "S01", MANANA, "10:00", 2, 3)
        self.r_manana_2 = self.crear(ACTIVO_2, "S02", MANANA, "14:00", 1, 5)

        # Casos adicionales para los filtros.
        self.r_hoy_pasada = self.formato(
            self.insertar_directo(ACTIVO, "S03", HOY, "08:00", 1, 2)
        )
        self.r_hoy_futura = self.crear(ACTIVO_2, "S03", HOY, "15:00", 1, 4)
        self.r_hoy_cancelada = self.formato(
            self.insertar_directo(ACTIVO, "S01", HOY, "11:00", 1, 1, "cancelada")
        )
        self.r_pasado_manana = self.crear(ACTIVO, "S02", PASADO_MANANA, "09:00", 1, 2)

    def crear(self, carne, sala, fecha, hora, duracion, personas):
        exito, mensaje, id_reservacion = crear_reservacion(
            carne, sala, fecha, hora, duracion, personas, ahora=AHORA
        )
        self.assertTrue(exito, mensaje)
        return id_reservacion

    @staticmethod
    def formato(id_interno):
        return f"R{id_interno:04d}"


class TestH01LogicaPanel(EscenarioPanel):

    def test_h01_proximas_con_fecha_por_defecto(self):
        """Escenario del hallazgo: fecha de hoy y las dos reservas de mañana."""
        self.crear(ACTIVO, "S01", MANANA, "10:00", 2, 3)
        self.crear(ACTIVO_2, "S02", MANANA, "14:00", 1, 5)

        datos = datos_panel(
            consultar_reservaciones(), consultar_salas(),
            fecha=HOY, sala="Todas", estado="Todos", ahora=AHORA,
        )

        self.assertEqual(datos["dia"], [])
        self.assertEqual(ids(datos["proximas"]), ["R0001", "R0002"])
        self.assertIn("2 próximas reservaciones", datos["mensaje"])

    def test_h01_proximas_ordenadas_solo_activas_desde_ahora(self):
        self.preparar_escenario()

        proximas = obtener_proximas(consultar_reservaciones(), AHORA)

        self.assertEqual(
            ids(proximas),
            [self.r_hoy_futura, self.r_manana_1, self.r_manana_2, self.r_pasado_manana],
        )
        self.assertNotIn(self.r_hoy_pasada, ids(proximas))
        self.assertNotIn(self.r_hoy_cancelada, ids(proximas))

    def test_h01_proximas_respetan_sala_y_estado(self):
        self.preparar_escenario()
        filas = consultar_reservaciones()

        self.assertEqual(
            ids(obtener_proximas(filas, AHORA, codigo_sala="S02")),
            [self.r_manana_2, self.r_pasado_manana],
        )
        self.assertEqual(
            obtener_proximas(filas, AHORA, estado="cancelada"),
            [],
        )

    def test_h01_proximas_limitadas_a_ocho(self):
        for dia in range(6, 16):
            self.insertar_directo(ACTIVO, "S03", f"2026-10-{dia:02d}", "10:00")

        self.assertEqual(len(obtener_proximas(consultar_reservaciones(), AHORA)), 8)

    def test_h07_filtros_combinados(self):
        self.preparar_escenario()
        filas = consultar_reservaciones()

        casos = [
            ((HOY, "", "todos"),
             {self.r_hoy_pasada, self.r_hoy_futura, self.r_hoy_cancelada}),
            ((HOY, "S03", "todos"), {self.r_hoy_pasada, self.r_hoy_futura}),
            ((HOY, "S01", "cancelada"), {self.r_hoy_cancelada}),
            (("", "S02", "activa"), {self.r_manana_2, self.r_pasado_manana}),
            ((MANANA, "S05", "todos"), set()),
        ]

        for filtros, esperado in casos:
            with self.subTest(filtros=filtros):
                self.assertEqual(set(ids(filtrar_reservaciones(filas, *filtros))), esperado)

    def test_h07_interpretar_filtros_de_la_interfaz(self):
        self.assertEqual(
            interpretar_filtros(" 2026-10-05 ", "S01 - Sala Biblioteca 1", "Activa"),
            ("2026-10-05", "S01", "activa"),
        )
        self.assertEqual(interpretar_filtros("", "Todas", "Todos"), ("", "", "todos"))

        for fecha, estado in (("05/10/2026", "Todos"), ("2026-02-30", "Todos"),
                              ("", "pendiente")):
            with self.subTest(fecha=fecha, estado=estado):
                with self.assertRaises(ValueError):
                    interpretar_filtros(fecha, "Todas", estado)

    def test_h07_ocupacion_del_dia_cuenta_activas(self):
        self.preparar_escenario()
        filas = filtrar_reservaciones(consultar_reservaciones(), HOY)

        ocupacion = {fila[0]: fila for fila in calcular_ocupacion(filas, consultar_salas())}

        self.assertEqual(sorted(ocupacion), ["S01", "S02", "S03", "S04", "S05"])
        self.assertEqual(ocupacion["S03"][2:5], (2, 6, "60%"))
        self.assertEqual(ocupacion["S01"][2:4], (0, 0))  # la cancelada no cuenta
        self.assertEqual(ocupacion["S04"][5], "Fuera de servicio")

    def test_h07_estado_vacio_comprensible(self):
        datos = datos_panel([], consultar_salas(), fecha=HOY, ahora=AHORA)

        self.assertEqual(datos["dia"], [])
        self.assertEqual(datos["proximas"], [])
        self.assertEqual(datos["mensaje"], MENSAJE_SIN_RESULTADOS)


class TestH07VistaPanelPrincipal(EscenarioPanel):
    """La vista que usa la ventana principal, con Tkinter real."""

    def setUp(self):
        super().setUp()

        if tk is None:
            self.skipTest("Tkinter no está instalado.")

        try:
            self.raiz = tk.Tk()
        except tk.TclError:
            self.skipTest("No hay pantalla disponible para Tkinter.")

        self.raiz.withdraw()

        from interfaz.vistas_panel_reservaciones import VistaPanelPrincipal

        self.VistaPanelPrincipal = VistaPanelPrincipal

    def tearDown(self):
        raiz = getattr(self, "raiz", None)

        if raiz is not None:
            raiz.destroy()

        super().tearDown()

    def vista(self):
        vista = self.VistaPanelPrincipal(self.raiz, reloj=lambda: AHORA)
        vista.var_fecha.set(HOY)
        vista.refrescar()
        return vista

    @staticmethod
    def ids_tabla(tabla):
        return [tabla.item(item, "values")[0] for item in tabla.get_children()]

    def test_h01_vista_muestra_proximas_con_fecha_de_hoy(self):
        self.crear(ACTIVO, "S01", MANANA, "10:00", 2, 3)
        self.crear(ACTIVO_2, "S02", MANANA, "14:00", 1, 5)

        vista = self.vista()

        self.assertEqual(self.ids_tabla(vista.tabla_dia), [])
        self.assertEqual(self.ids_tabla(vista.tabla_proximas), ["R0001", "R0002"])

    def test_h07_vista_aplica_filtros_combinados(self):
        self.preparar_escenario()
        vista = self.vista()

        vista.var_sala.set("S03 - Laboratorio de estudio")
        vista.var_estado.set("activa")
        vista.refrescar()

        self.assertEqual(
            self.ids_tabla(vista.tabla_dia),
            [self.r_hoy_pasada, self.r_hoy_futura],
        )
        self.assertEqual(self.ids_tabla(vista.tabla_proximas), [self.r_hoy_futura])

    def test_h07_vista_fecha_invalida_muestra_mensaje(self):
        self.preparar_escenario()
        vista = self.vista()

        vista.var_fecha.set("31/10/2026")
        vista.refrescar()

        self.assertEqual(vista.var_mensaje.get(), "La fecha debe tener formato AAAA-MM-DD.")
        self.assertEqual(self.ids_tabla(vista.tabla_proximas), [])

    def test_h07_vista_se_actualiza_tras_crear_modificar_cancelar(self):
        vista = self.vista()
        self.assertEqual(self.ids_tabla(vista.tabla_proximas), [])

        id_reservacion = self.crear(ACTIVO, "S01", MANANA, "10:00", 1, 2)
        vista.refrescar()
        self.assertEqual(self.ids_tabla(vista.tabla_proximas), [id_reservacion])

        exito, mensaje = modificar_reservacion(
            id_reservacion, "S02", MANANA, "10:00", 1, 2, ahora=AHORA
        )[:2]
        self.assertTrue(exito, mensaje)
        vista.refrescar()
        fila = vista.tabla_proximas.item(vista.tabla_proximas.get_children()[0], "values")
        self.assertEqual(fila[1], "S02")

        exito, mensaje = cancelar_reservacion(id_reservacion)[:2]
        self.assertTrue(exito, mensaje)
        vista.refrescar()
        self.assertEqual(self.ids_tabla(vista.tabla_proximas), [])


if __name__ == "__main__":
    unittest.main()
