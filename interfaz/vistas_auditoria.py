"""
Interfaz para RF-17: Historial de auditoría.

Permite consultar los registros de auditoría generados
por las acciones realizadas en el sistema.

La vista es de solo lectura.
"""

import tkinter as tk
from tkinter import ttk

from reservaciones.gestion_reservaciones import (
    consultar_auditoria,
)


class VistaAuditoria(ttk.Frame):
    """
    RF-17. Consulta del historial de auditoría.
    """

    def __init__(self, padre):
        super().__init__(
            padre,
            padding=(20, 16),
        )

        self.var_mensaje = tk.StringVar()

        self._crear_interfaz()
        self.refrescar()

    # ------------------------------------------------------------------
    # Construcción de interfaz
    # ------------------------------------------------------------------

    def _crear_interfaz(self):

        ttk.Label(
            self,
            text="Historial de auditoría",
            font=("TkDefaultFont", 16, "bold"),
        ).pack(
            anchor="w"
        )

        ttk.Label(
            self,
            text=(
                "Consulta las acciones de creación, modificación "
                "y cancelación realizadas en el sistema."
            ),
            foreground="#5c5f66",
        ).pack(
            anchor="w",
            pady=(2, 12),
        )

        marco_tabla = ttk.LabelFrame(
            self,
            text="Registros de auditoría",
            padding=8,
        )

        marco_tabla.pack(
            fill="both",
            expand=True,
            pady=(0, 10),
        )

        columnas = (
            "id",
            "fecha_hora",
            "tipo_accion",
            "entidad",
            "identificador",
        )

        self.tabla = ttk.Treeview(
            marco_tabla,
            columns=columnas,
            show="headings",
        )

        encabezados = {
            "id": "ID",
            "fecha_hora": "Fecha y hora",
            "tipo_accion": "Acción",
            "entidad": "Entidad",
            "identificador": "Identificador",
        }

        anchos = {
            "id": 60,
            "fecha_hora": 170,
            "tipo_accion": 130,
            "entidad": 130,
            "identificador": 120,
        }

        for columna in columnas:

            self.tabla.heading(
                columna,
                text=encabezados[columna],
            )

            self.tabla.column(
                columna,
                width=anchos[columna],
                anchor="center",
            )

        barra_vertical = ttk.Scrollbar(
            marco_tabla,
            orient="vertical",
            command=self.tabla.yview,
        )

        barra_horizontal = ttk.Scrollbar(
            marco_tabla,
            orient="horizontal",
            command=self.tabla.xview,
        )

        self.tabla.configure(
            yscrollcommand=barra_vertical.set,
            xscrollcommand=barra_horizontal.set,
        )

        self.tabla.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        barra_vertical.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        barra_horizontal.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        marco_tabla.rowconfigure(
            0,
            weight=1,
        )

        marco_tabla.columnconfigure(
            0,
            weight=1,
        )

        ttk.Button(
            self,
            text="Actualizar",
            command=self.refrescar,
        ).pack(
            anchor="w",
            pady=(0, 8),
        )

        ttk.Label(
            self,
            textvariable=self.var_mensaje,
            foreground="#5c5f66",
        ).pack(
            anchor="w",
        )

    # ------------------------------------------------------------------
    # Refrescar historial
    # ------------------------------------------------------------------

    def refrescar(self):

        self.tabla.delete(
            *self.tabla.get_children()
        )

        try:

            registros = consultar_auditoria()

            for registro in registros:

                self.tabla.insert(
                    "",
                    "end",
                    values=registro,
                )

            if registros:

                self.var_mensaje.set(
                    f"{len(registros)} registros de auditoría."
                )

            else:

                self.var_mensaje.set(
                    "No hay registros de auditoría."
                )

        except RuntimeError as error:

            self.var_mensaje.set(
                str(error)
            )