"""
Ventana principal del Sistema de Reservación de Salas.

Integra todas las vistas mediante un único menú lateral
y controla RF-10: Salir.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from interfaz.vistas_estudiantes import VistaEstudiantes
from interfaz.vistas_salas import VistaSalas

from interfaz.vistas_reservaciones import (
    VistaCrearReservacion,
    VistaConsultarReservaciones,
    VistaBuscarPorEstudiante,
    VistaDisponibilidad,
    configurar_estilos,
)

from interfaz.vistas_gestion_reservas import (
    VistaGestionReservaciones,
)

from interfaz.vistas_recurrencia import (
    VistaReservacionRecurrente,
)

from interfaz.vistas_reportes import (
    VistaReportes,
)

from interfaz.vistas_auditoria import (
    VistaAuditoria,
)

from interfaz.vistas_panel_reservaciones import (
    VistaPanelPrincipal,
)


class VentanaPrincipal:

    def __init__(self, raiz):
        self.raiz = raiz

        self.raiz.title(
            "Sistema de Reservación de Salas"
        )

        self.raiz.geometry(
            "1200x820"
        )

        self.raiz.minsize(
            1000,
            700,
        )

        configurar_estilos(
            self.raiz
        )

        self.vista_actual = None
        self.botones_menu = {}

        self._crear_estructura()
        self._crear_vistas()
        self._crear_menu_lateral()

        # RF-10:
        # La X utiliza la misma lógica que el botón Salir.
        self.raiz.protocol(
            "WM_DELETE_WINDOW",
            self.salir,
        )

        # La aplicación inicia en el panel principal.
        self.mostrar_vista(
            "panel"
        )

    # ------------------------------------------------------------------
    # Estructura general
    # ------------------------------------------------------------------

    def _crear_estructura(self):

        self.raiz.rowconfigure(
            0,
            weight=1,
        )

        self.raiz.columnconfigure(
            1,
            weight=1,
        )

        # --------------------------------------------------------------
        # Menú lateral
        # --------------------------------------------------------------

        self.menu_lateral = tk.Frame(
            self.raiz,
            bg="#f3f4f6",
            width=245,
        )

        self.menu_lateral.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.menu_lateral.grid_propagate(
            False
        )

        # --------------------------------------------------------------
        # Área donde se muestran las vistas
        # --------------------------------------------------------------

        self.contenido = ttk.Frame(
            self.raiz
        )

        self.contenido.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

    # ------------------------------------------------------------------
    # Vistas del sistema
    # ------------------------------------------------------------------

    def _crear_vistas(self):

        self.vista_panel = VistaPanelPrincipal(
            self.contenido
        )

        self.vista_estudiantes = VistaEstudiantes(
            self.contenido
        )

        self.vista_salas = VistaSalas(
            self.contenido
        )

        self.vista_crear_reservacion = VistaCrearReservacion(
            self.contenido,
            on_cambio=self._actualizar_datos,
        )

        self.vista_consultar_reservaciones = (
            VistaConsultarReservaciones(
                self.contenido
            )
        )

        self.vista_buscar_estudiante = (
            VistaBuscarPorEstudiante(
                self.contenido
            )
        )

        self.vista_disponibilidad = (
            VistaDisponibilidad(
                self.contenido
            )
        )

        self.vista_gestion_reservaciones = (
            VistaGestionReservaciones(
                self.contenido,
                on_cambio=self._actualizar_datos,
            )
        )

        self.vista_recurrencia = (
            VistaReservacionRecurrente(
                self.contenido,
                on_cambio=self._actualizar_datos,
            )
        )

        self.vista_reportes = VistaReportes(
            self.contenido
        )

        self.vista_auditoria = VistaAuditoria(
            self.contenido
        )

        self.vistas = {
            "panel": self.vista_panel,
            "estudiantes": self.vista_estudiantes,
            "salas": self.vista_salas,
            "crear": self.vista_crear_reservacion,
            "consultar": self.vista_consultar_reservaciones,
            "buscar": self.vista_buscar_estudiante,
            "disponibilidad": self.vista_disponibilidad,
            "gestionar": self.vista_gestion_reservaciones,
            "recurrencia": self.vista_recurrencia,
            "reportes": self.vista_reportes,
            "auditoria": self.vista_auditoria,
        }

    # ------------------------------------------------------------------
    # Menú lateral
    # ------------------------------------------------------------------

    def _crear_menu_lateral(self):

        encabezado = tk.Frame(
            self.menu_lateral,
            bg="#f3f4f6",
        )

        encabezado.pack(
            fill="x",
            padx=16,
            pady=(20, 16),
        )

        tk.Label(
            encabezado,
            text="Sistema de\nReservación de Salas",
            bg="#f3f4f6",
            fg="#111827",
            font=("TkDefaultFont", 14, "bold"),
            justify="left",
            anchor="w",
        ).pack(
            fill="x"
        )

        tk.Label(
            encabezado,
            text="Menú principal",
            bg="#f3f4f6",
            fg="#6b7280",
            anchor="w",
        ).pack(
            fill="x",
            pady=(4, 0),
        )

        self._crear_seccion_menu(
            "INICIO"
        )

        self._crear_boton_menu(
            "Panel principal",
            "panel",
        )

        self._crear_seccion_menu(
            "GESTIÓN"
        )

        self._crear_boton_menu(
            "Estudiantes",
            "estudiantes",
        )

        self._crear_boton_menu(
            "Salas",
            "salas",
        )

        self._crear_seccion_menu(
            "RESERVACIONES"
        )

        self._crear_boton_menu(
            "Crear reservación",
            "crear",
        )

        self._crear_boton_menu(
            "Consultar reservaciones",
            "consultar",
        )

        self._crear_boton_menu(
            "Buscar por estudiante",
            "buscar",
        )

        self._crear_boton_menu(
            "Consultar disponibilidad",
            "disponibilidad",
        )

        self._crear_boton_menu(
            "Modificar / cancelar",
            "gestionar",
        )

        self._crear_boton_menu(
            "Reservaciones recurrentes",
            "recurrencia",
        )

        self._crear_seccion_menu(
            "OTROS"
        )

        self._crear_boton_menu(
            "Reportes",
            "reportes",
        )

        self._crear_boton_menu(
            "Historial de auditoría",
            "auditoria",
        )

        # --------------------------------------------------------------
        # Salir siempre queda al fondo del menú lateral.
        # --------------------------------------------------------------

        boton_salir = tk.Button(
            self.menu_lateral,
            text="Salir",
            command=self.salir,
            anchor="w",
            relief="flat",
            borderwidth=0,
            padx=18,
            pady=10,
            bg="#f3f4f6",
            fg="#7f1d1d",
            activebackground="#fee2e2",
            activeforeground="#7f1d1d",
            cursor="hand2",
        )

        boton_salir.pack(
            side="bottom",
            fill="x",
            padx=8,
            pady=12,
        )

    def _crear_seccion_menu(self, texto):

        tk.Label(
            self.menu_lateral,
            text=texto,
            bg="#f3f4f6",
            fg="#6b7280",
            font=("TkDefaultFont", 8, "bold"),
            anchor="w",
        ).pack(
            fill="x",
            padx=18,
            pady=(10, 3),
        )

    def _crear_boton_menu(
        self,
        texto,
        clave,
    ):

        boton = tk.Button(
            self.menu_lateral,
            text=texto,
            command=lambda: self.mostrar_vista(
                clave
            ),
            anchor="w",
            relief="flat",
            borderwidth=0,
            padx=18,
            pady=7,
            bg="#f3f4f6",
            fg="#1f2937",
            activebackground="#e5e7eb",
            activeforeground="#111827",
            cursor="hand2",
        )

        boton.pack(
            fill="x",
            padx=8,
            pady=1,
        )

        self.botones_menu[clave] = boton

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

    def mostrar_vista(
        self,
        clave,
    ):

        nueva_vista = self.vistas[clave]

        if self.vista_actual is not None:
            self.vista_actual.pack_forget()

        nueva_vista.pack(
            fill="both",
            expand=True,
        )

        self.vista_actual = nueva_vista

        self._marcar_boton_activo(
            clave
        )

        refrescar = getattr(
            nueva_vista,
            "refrescar",
            None,
        )

        if callable(refrescar):
            refrescar()

    def _marcar_boton_activo(
        self,
        clave_activa,
    ):

        for clave, boton in self.botones_menu.items():

            if clave == clave_activa:

                boton.configure(
                    bg="#dbeafe",
                    fg="#1e3a8a",
                )

            else:

                boton.configure(
                    bg="#f3f4f6",
                    fg="#1f2937",
                )

    # ------------------------------------------------------------------
    # Actualización entre módulos
    # ------------------------------------------------------------------

    def _actualizar_datos(self):

        self.vista_consultar_reservaciones.refrescar()
        self.vista_panel.refrescar()
        self.vista_auditoria.refrescar()

    # ------------------------------------------------------------------
    # RF-10. Cambios pendientes
    # ------------------------------------------------------------------

    def hay_cambios_pendientes(self):

        vistas_editables = (
            self.vista_estudiantes,
            self.vista_salas,
            self.vista_crear_reservacion,
            self.vista_gestion_reservaciones,
        )

        for vista in vistas_editables:

            verificar = getattr(
                vista,
                "hay_cambios_pendientes",
                None,
            )

            if (
                callable(verificar)
                and verificar()
            ):
                return True

        return False

    def guardar_cambios_pendientes(self):

        vistas_editables = (
            self.vista_estudiantes,
            self.vista_salas,
            self.vista_crear_reservacion,
            self.vista_gestion_reservaciones,
        )

        for vista in vistas_editables:

            guardar = getattr(
                vista,
                "guardar_pendientes",
                None,
            )

            if not callable(guardar):
                continue

            exito, mensaje = guardar()

            if not exito:
                return False, mensaje

        return True, ""

    # ------------------------------------------------------------------
    # RF-10. Salir
    # ------------------------------------------------------------------

    def salir(self):
        """
        Si no existen cambios pendientes, cierra inmediatamente.

        Si existen cambios pendientes, solicita confirmación.

        El botón Salir del menú lateral y la X de Windows
        utilizan exactamente esta misma función.
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

        exito, mensaje = (
            self.guardar_cambios_pendientes()
        )

        if not exito:

            messagebox.showerror(
                "No se puede cerrar",
                (
                    "No fue posible guardar todos los "
                    "cambios pendientes.\n\n"
                    f"{mensaje}\n\n"
                    "La aplicación permanecerá abierta "
                    "para que pueda corregir la información."
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