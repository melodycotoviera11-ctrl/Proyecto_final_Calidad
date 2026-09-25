"""
Panel unificado para la gestión de reservaciones.

Integra:
- RF-05 Crear reservación.
- RF-06 Consultar reservaciones.
- RF-07 Buscar por estudiante.
- RF-08 Consultar disponibilidad.
- RF-09 Cancelar reservación.
- RF-13 Modificar reservación.
"""

import tkinter as tk
from tkinter import ttk

from interfaz.vistas_reservaciones import (
    VistaCrearReservacion,
    VistaConsultarReservaciones,
    VistaBuscarPorEstudiante,
    VistaDisponibilidad,
    configurar_estilos,
)

from interfaz.vistas_gestion_reservas import VistaGestionReservaciones


class PanelReservaciones(ttk.Frame):

    def __init__(self, padre):
        super().__init__(padre)

        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(
            fill="both",
            expand=True,
        )

        # Consulta general. Otras vistas pueden solicitar que se actualice
        # después de crear, modificar o cancelar una reservación.
        self.vista_consultar = VistaConsultarReservaciones(
            self.pestanas
        )

        self.vista_crear = VistaCrearReservacion(
            self.pestanas,
            on_cambio=self._actualizar_reservaciones,
        )

        self.vista_buscar = VistaBuscarPorEstudiante(
            self.pestanas
        )

        self.vista_disponibilidad = VistaDisponibilidad(
            self.pestanas
        )

        self.vista_gestionar = VistaGestionReservaciones(
            self.pestanas,
            on_cambio=self._actualizar_reservaciones,
        )

        self.vistas = [
            self.vista_crear,
            self.vista_consultar,
            self.vista_buscar,
            self.vista_disponibilidad,
            self.vista_gestionar,
        ]

        nombres = [
            "Crear",
            "Reservaciones",
            "Buscar por estudiante",
            "Disponibilidad",
            "Gestionar reservaciones",
        ]

        for vista, nombre in zip(self.vistas, nombres):
            self.pestanas.add(
                vista,
                text=nombre,
            )

        self.pestanas.bind(
            "<<NotebookTabChanged>>",
            self._cambiar_pestana,
        )

    def _actualizar_reservaciones(self):
        """
        Actualiza las vistas que dependen del estado de las reservaciones
        después de crear, modificar o cancelar.
        """
        self.vista_consultar.refrescar()

    def _cambiar_pestana(self, _evento=None):
        indice = self.pestanas.index("current")
        vista = self.vistas[indice]

        refrescar = getattr(
            vista,
            "refrescar",
            None,
        )

        if callable(refrescar):
            refrescar()

    def hay_cambios_pendientes(self):
        return (
            self.vista_crear.hay_cambios_pendientes()
            or self.vista_gestionar.hay_cambios_pendientes()
        )


    def guardar_pendientes(self):
        for vista in (
            self.vista_crear,
            self.vista_gestionar,
        ):
            exito, mensaje = vista.guardar_pendientes()

            if not exito:
                return False, mensaje

        return True, ""


def abrir_ventana_de_prueba():
    """
    Abre el panel completo de reservaciones
    antes de integrarlo con la ventana principal.
    """

    from database.inicializacion import inicializar_base_datos

    if not inicializar_base_datos():
        return

    raiz = tk.Tk()

    raiz.title(
        "Sistema de Reservación de Salas"
    )

    raiz.geometry("950x750")
    raiz.minsize(850, 650)

    configurar_estilos(raiz)

    panel = PanelReservaciones(raiz)
    panel.pack(
        fill="both",
        expand=True,
    )

    raiz.mainloop()


if __name__ == "__main__":
    abrir_ventana_de_prueba()