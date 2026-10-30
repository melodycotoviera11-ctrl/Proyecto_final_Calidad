"""
Pruebas de RF-10: salir.

Agregadas en la Fase 6:
- H-05: la salida no permitía descartar los datos y un formulario
  inválido impedía cerrar la aplicación.
- H-07: la suite no tenía pruebas de la salida.

La primera clase prueba la lógica sin Tkinter (RNF-10). Las demás usan
la ventana principal real sobre una base de datos temporal; los cuadros
de diálogo se reemplazan por respuestas fijas para no depender de clics.
"""

import unittest
from unittest import mock

from interfaz.logica_salida import (
    CANCELAR,
    GUARDAR_Y_SALIR,
    SALIR_SIN_GUARDAR,
    resolver_salida,
)
from tests.utilidades import ACTIVO, PruebaConBaseTemporal

try:
    import tkinter as tk
except ImportError:  # Python sin Tkinter
    tk = None


class VistaFalsa:
    """Vista mínima con la misma interfaz que usan las vistas editables."""

    def __init__(self, pendiente=False, guarda=True, mensaje=""):
        self.pendiente = pendiente
        self.guarda = guarda
        self.mensaje = mensaje
        self.guardada = False

    def hay_cambios_pendientes(self):
        return self.pendiente

    def guardar_pendientes(self):
        if not self.guarda:
            return False, self.mensaje

        self.guardada = True
        self.pendiente = False
        return True, ""


def nunca_llamar(*_args):
    raise AssertionError("No debía mostrarse este cuadro.")


class TestRF10LogicaSalida(unittest.TestCase):

    def test_rf10_sin_cambios_cierra_sin_preguntar(self):
        vistas = [VistaFalsa(), VistaFalsa()]

        self.assertTrue(resolver_salida(vistas, nunca_llamar, nunca_llamar))

    def test_rf10_cancelar_mantiene_abierta_y_no_guarda(self):
        vista = VistaFalsa(pendiente=True)

        cerrar = resolver_salida([vista], lambda: CANCELAR, nunca_llamar)

        self.assertFalse(cerrar)
        self.assertFalse(vista.guardada)
        self.assertTrue(vista.hay_cambios_pendientes())

    def test_rf10_salir_sin_guardar_cierra_y_no_guarda(self):
        vista = VistaFalsa(pendiente=True)

        cerrar = resolver_salida([vista], lambda: SALIR_SIN_GUARDAR, nunca_llamar)

        self.assertTrue(cerrar)
        self.assertFalse(vista.guardada)

    def test_rf10_guardar_y_salir_guarda_y_cierra(self):
        vista = VistaFalsa(pendiente=True)

        cerrar = resolver_salida([vista], lambda: GUARDAR_Y_SALIR, nunca_llamar)

        self.assertTrue(cerrar)
        self.assertTrue(vista.guardada)

    def test_rf10_solo_guarda_las_vistas_con_cambios(self):
        con_cambios = VistaFalsa(pendiente=True)
        sin_cambios = VistaFalsa(pendiente=False)

        resolver_salida(
            [sin_cambios, con_cambios],
            lambda: GUARDAR_Y_SALIR,
            nunca_llamar,
        )

        self.assertTrue(con_cambios.guardada)
        self.assertFalse(sin_cambios.guardada)

    def test_rf10_error_al_guardar_permite_salir_sin_guardar(self):
        vista = VistaFalsa(pendiente=True, guarda=False, mensaje="El campo sala es obligatorio.")
        mensajes = []

        def tras_error(mensaje):
            mensajes.append(mensaje)
            return SALIR_SIN_GUARDAR

        cerrar = resolver_salida([vista], lambda: GUARDAR_Y_SALIR, tras_error)

        self.assertTrue(cerrar)
        self.assertEqual(mensajes, ["El campo sala es obligatorio."])

    def test_rf10_error_al_guardar_y_cancelar_mantiene_abierta(self):
        vista = VistaFalsa(pendiente=True, guarda=False, mensaje="Dato inválido.")

        cerrar = resolver_salida([vista], lambda: GUARDAR_Y_SALIR, lambda _m: CANCELAR)

        self.assertFalse(cerrar)
        self.assertTrue(vista.hay_cambios_pendientes())

    def test_rf10_se_detiene_en_la_primera_vista_que_falla(self):
        falla = VistaFalsa(pendiente=True, guarda=False, mensaje="Falla 1")
        siguiente = VistaFalsa(pendiente=True)

        resolver_salida([falla, siguiente], lambda: GUARDAR_Y_SALIR, lambda _m: CANCELAR)

        self.assertFalse(siguiente.guardada)

    def test_rf10_respuesta_no_prevista_mantiene_abierta(self):
        for respuesta in (None, "", "otra"):
            with self.subTest(respuesta=respuesta):
                vista = VistaFalsa(pendiente=True)

                self.assertFalse(
                    resolver_salida([vista], lambda r=respuesta: r, nunca_llamar)
                )
                self.assertFalse(vista.guardada)


class BaseVentanaPrincipal(PruebaConBaseTemporal):
    """Abre la ventana principal real sin mostrarla."""

    def setUp(self):
        super().setUp()

        if tk is None:
            self.skipTest("Tkinter no está instalado.")

        try:
            self.raiz = tk.Tk()
        except tk.TclError:
            self.skipTest("No hay pantalla disponible para Tkinter.")

        self.raiz.withdraw()

        from interfaz.ventana_principal import VentanaPrincipal

        self.ventana = VentanaPrincipal(self.raiz)
        self.destruir = mock.patch.object(self.raiz, "destroy").start()

    def tearDown(self):
        mock.patch.stopall()

        raiz = getattr(self, "raiz", None)

        if raiz is not None:
            raiz.destroy()

        super().tearDown()

    def responder(self, opcion, tras_error=None):
        """Reemplaza los cuadros de diálogo por respuestas fijas."""

        self.pregunta = mock.patch.object(
            self.ventana,
            "_preguntar_opcion_salida",
            return_value=opcion,
        ).start()

        self.pregunta_error = mock.patch.object(
            self.ventana,
            "_preguntar_tras_error",
            return_value=tras_error,
        ).start()


class TestRF10VentanaPrincipal(BaseVentanaPrincipal):

    def test_rf10_x_de_la_ventana_usa_el_mismo_procedimiento(self):
        comando = self.raiz.protocol("WM_DELETE_WINDOW")

        self.assertTrue(comando.endswith("salir"), comando)

    def test_rf10_sin_cambios_cierra_sin_confirmacion(self):
        self.responder(CANCELAR)

        self.ventana.salir()

        self.pregunta.assert_not_called()
        self.destruir.assert_called_once_with()

    def test_rf10_h05_formulario_incompleto_puede_salir_sin_guardar(self):
        # Escenario de H-05: solo el carné escrito en "Crear reservación".
        self.ventana.vista_crear_reservacion.var_carne.set(ACTIVO)
        antes = self.conteos()

        self.responder(SALIR_SIN_GUARDAR)
        self.ventana.salir()

        self.destruir.assert_called_once_with()
        self.pregunta_error.assert_not_called()
        self.assertEqual(antes, self.conteos())

    def test_rf10_h05_guardar_falla_y_luego_salir_sin_guardar(self):
        self.ventana.vista_crear_reservacion.var_carne.set(ACTIVO)
        antes = self.conteos()

        self.responder(GUARDAR_Y_SALIR, tras_error=SALIR_SIN_GUARDAR)
        self.ventana.salir()

        self.pregunta_error.assert_called_once()
        mensaje = self.pregunta_error.call_args.args[0]
        self.assertIn("sala", mensaje.lower())
        self.destruir.assert_called_once_with()
        self.assertEqual(antes, self.conteos())

    def test_rf10_guardar_falla_y_cancelar_conserva_el_formulario(self):
        vista = self.ventana.vista_crear_reservacion
        vista.var_carne.set(ACTIVO)

        self.responder(GUARDAR_Y_SALIR, tras_error=CANCELAR)
        self.ventana.salir()

        self.destruir.assert_not_called()
        self.assertEqual(vista.var_carne.get(), ACTIVO)

    def test_rf10_cancelar_conserva_la_informacion_ingresada(self):
        vista = self.ventana.vista_estudiantes
        vista.var_carne_nuevo.set("D001112223")
        vista.var_nombre_nuevo.set("Ana Mora")

        self.responder(CANCELAR)
        self.ventana.salir()

        self.destruir.assert_not_called()
        self.assertEqual(vista.var_carne_nuevo.get(), "D001112223")
        self.assertEqual(vista.var_nombre_nuevo.get(), "Ana Mora")

    def test_rf10_guardar_y_salir_guarda_antes_de_cerrar(self):
        vista = self.ventana.vista_estudiantes
        vista.var_carne_nuevo.set("D001112223")
        vista.var_nombre_nuevo.set("Ana Mora")
        vista.var_correo_nuevo.set("ana@universidad.ac.cr")

        self.responder(GUARDAR_Y_SALIR)
        self.ventana.salir()

        self.destruir.assert_called_once_with()
        self.assertEqual(
            self.sql("SELECT carne, estado FROM estudiantes WHERE carne = ?", ("D001112223",)),
            [("D001112223", "activo")],
        )

    def test_rf10_salir_sin_guardar_no_guarda_el_estudiante(self):
        vista = self.ventana.vista_estudiantes
        vista.var_carne_nuevo.set("D001112223")
        vista.var_nombre_nuevo.set("Ana Mora")
        vista.var_correo_nuevo.set("ana@universidad.ac.cr")

        self.responder(SALIR_SIN_GUARDAR)
        self.ventana.salir()

        self.destruir.assert_called_once_with()
        self.assertEqual(
            self.sql("SELECT carne FROM estudiantes WHERE carne = ?", ("D001112223",)),
            [],
        )


class TestRF10DialogoSalida(BaseVentanaPrincipal):
    """El cuadro real devuelve la opción del botón presionado."""

    def presionar_despues(self, texto):
        def presionar():
            for ventana in self.raiz.winfo_children():
                if not isinstance(ventana, tk.Toplevel):
                    continue
                for boton in self._botones(ventana):
                    if boton.cget("text") == texto:
                        boton.invoke()
                        return

        self.raiz.after(150, presionar)

    def _botones(self, widget):
        for hijo in widget.winfo_children():
            if hijo.winfo_class() == "TButton":
                yield hijo
            yield from self._botones(hijo)

    def test_rf10_dialogo_ofrece_las_tres_opciones(self):
        self.raiz.deiconify()

        for texto, esperado in (
            ("Guardar y salir", GUARDAR_Y_SALIR),
            ("Salir sin guardar", SALIR_SIN_GUARDAR),
            ("Cancelar", CANCELAR),
        ):
            with self.subTest(boton=texto):
                self.presionar_despues(texto)
                self.assertEqual(self.ventana._preguntar_opcion_salida(), esperado)

    def test_rf10_dialogo_tras_error_ofrece_salir_o_cancelar(self):
        self.raiz.deiconify()

        for texto, esperado in (
            ("Salir sin guardar", SALIR_SIN_GUARDAR),
            ("Cancelar", CANCELAR),
        ):
            with self.subTest(boton=texto):
                self.presionar_despues(texto)
                self.assertEqual(
                    self.ventana._preguntar_tras_error("El campo sala es obligatorio."),
                    esperado,
                )

    def test_rf10_cerrar_el_dialogo_equivale_a_cancelar(self):
        self.raiz.deiconify()

        def cerrar():
            for ventana in self.raiz.winfo_children():
                if isinstance(ventana, tk.Toplevel):
                    ventana.destroy()

        self.raiz.after(150, cerrar)

        self.assertEqual(self.ventana._preguntar_opcion_salida(), CANCELAR)


if __name__ == "__main__":
    unittest.main()
