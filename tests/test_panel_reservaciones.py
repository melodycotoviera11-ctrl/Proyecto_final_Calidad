import unittest
from unittest import mock

from interfaz.vistas_panel_reservaciones import PanelReservaciones


class TestPanelReservaciones(unittest.TestCase):

    def test_rf15_actualiza_consultas_despues_de_crear(self):
        panel = object.__new__(PanelReservaciones)

        panel.vista_consultar = mock.Mock()
        panel.vista_panel = mock.Mock()

        PanelReservaciones._actualizar_reservaciones(panel)

        panel.vista_consultar.refrescar.assert_called_once_with()
        panel.vista_panel.refrescar.assert_called_once_with()

    def test_rf15_callback_de_crear_apunta_a_actualizacion(self):
        panel = object.__new__(PanelReservaciones)

        panel.vista_consultar = mock.Mock()
        panel.vista_panel = mock.Mock()

        callback = panel._actualizar_reservaciones

        callback()

        panel.vista_consultar.refrescar.assert_called_once_with()
        panel.vista_panel.refrescar.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()