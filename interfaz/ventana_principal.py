"""
Ventana principal del Sistema de Reservación de Salas.

Integra estudiantes, salas y reservaciones,
y controla RF-10: Salir.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from interfaz.vistas_estudiantes import VistaEstudiantes
from interfaz.vistas_panel_reservaciones import PanelReservaciones
from interfaz.vistas_reservaciones import configurar_estilos
from interfaz.vistas_salas import VistaSalas


class VentanaPrincipal:

    def __init__(self, raiz):
        self.raiz = raiz

        self.raiz.title("Sistema de Reservación de Salas")
        self.raiz.geometry("1000x760")
        self.raiz.minsize(850, 650)

        configurar_estilos(self.raiz)

        self._crear_menu()
        self._crear_contenido()

        # La X de Windows utiliza exactamente la misma lógica de RF-10.
        self.raiz.protocol(
            "WM_DELETE_WINDOW",
            self.salir,
        )

    def _crear_menu(self):
        barra_menu = tk.Menu(self.raiz)

        menu_sistema = tk.Menu(
            barra_menu,
            tearoff=False,
        )

        menu_sistema.add_command(
            label="Salir",
            command=self.salir,
        )

        barra_menu.add_cascade(
            label="Sistema",
            menu=menu_sistema,
        )

        self.raiz.config(
            menu=barra_menu
        )

    def _crear_contenido(self):
        self.pestanas = ttk.Notebook(
            self.raiz
        )

        self.pestanas.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8,
        )

        self.vista_estudiantes = VistaEstudiantes(
            self.pestanas
        )

        self.vista_salas = VistaSalas(
            self.pestanas
        )

        self.vista_reservaciones = PanelReservaciones(
            self.pestanas
        )

        self.pestanas.add(
            self.vista_estudiantes,
            text="Estudiantes",
        )

        self.pestanas.add(
            self.vista_salas,
            text="Salas",
        )

        self.pestanas.add(
            self.vista_reservaciones,
            text="Reservaciones",
        )

    def hay_cambios_pendientes(self):
        return (
            self.vista_estudiantes.hay_cambios_pendientes()
            or self.vista_salas.hay_cambios_pendientes()
            or self.vista_reservaciones.hay_cambios_pendientes()
        )

    def guardar_cambios_pendientes(self):
        vistas = (
            self.vista_estudiantes,
            self.vista_salas,
            self.vista_reservaciones,
        )

        for vista in vistas:
            exito, mensaje = vista.guardar_pendientes()

            if not exito:
                return False, mensaje

        return True, ""

    def salir(self):
        """
        RF-10.

        Si no existen cambios pendientes, cierra inmediatamente.

        Si existen cambios pendientes, solicita confirmación.
        Al confirmar, intenta guardarlos antes de cerrar.
        Al cancelar, mantiene abierta la aplicación.
        """

        if not self.hay_cambios_pendientes():
            self.raiz.destroy()
            return

        confirmar = messagebox.askyesno(
            "Cambios pendientes",
            (
                "Hay cambios pendientes de guardar.\n\n"
                "¿Desea guardarlos y salir?"
            ),
            parent=self.raiz,
        )

        if not confirmar:
            return

        exito, mensaje = self.guardar_cambios_pendientes()

        if not exito:
            messagebox.showerror(
                "No se puede cerrar",
                (
                    "No fue posible guardar todos los cambios pendientes.\n\n"
                    f"{mensaje}\n\n"
                    "La aplicación permanecerá abierta para que pueda "
                    "corregir la información."
                ),
                parent=self.raiz,
            )
            return

        self.raiz.destroy()


def iniciar_interfaz():
    raiz = tk.Tk()

    VentanaPrincipal(
        raiz
    )

    raiz.mainloop()