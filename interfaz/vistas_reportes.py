"""
Interfaz para generación de reportes.

RF-16:
- Solicita fecha inicial.
- Solicita fecha final.
- Permite seleccionar el destino del archivo.
- Genera el reporte en formato CSV.
- Informa si el reporte fue generado correctamente.
- Informa los errores de validación.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from reservaciones.reportes import generar_reporte_csv


class VistaReportes(ttk.Frame):
    """
    RF-16. Interfaz para generar reportes de reservaciones.
    """

    def __init__(self, padre):
        super().__init__(
            padre,
            padding=(20, 16),
        )

        self.var_fecha_inicial = tk.StringVar()
        self.var_fecha_final = tk.StringVar()
        self.var_mensaje = tk.StringVar()

        self._crear_interfaz()

    # ------------------------------------------------------------------
    # Construcción de interfaz
    # ------------------------------------------------------------------

    def _crear_interfaz(self):

        ttk.Label(
            self,
            text="Generar reporte",
            font=("TkDefaultFont", 16, "bold"),
        ).pack(
            anchor="w"
        )

        ttk.Label(
            self,
            text=(
                "Seleccione un rango de fechas para generar "
                "un reporte de reservaciones en formato CSV."
            ),
            foreground="#5c5f66",
        ).pack(
            anchor="w",
            pady=(2, 15),
        )

        # --------------------------------------------------------------
        # Rango de fechas
        # --------------------------------------------------------------

        marco_fechas = ttk.LabelFrame(
            self,
            text="Rango de fechas",
            padding=12,
        )

        marco_fechas.pack(
            fill="x",
            pady=(0, 12),
        )

        ttk.Label(
            marco_fechas,
            text="Fecha inicial (AAAA-MM-DD)",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=6,
        )

        ttk.Entry(
            marco_fechas,
            textvariable=self.var_fecha_inicial,
            width=18,
        ).grid(
            row=0,
            column=1,
            sticky="w",
            pady=6,
        )

        ttk.Label(
            marco_fechas,
            text="Fecha final (AAAA-MM-DD)",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=6,
        )

        ttk.Entry(
            marco_fechas,
            textvariable=self.var_fecha_final,
            width=18,
        ).grid(
            row=1,
            column=1,
            sticky="w",
            pady=6,
        )

        # --------------------------------------------------------------
        # Destino
        # --------------------------------------------------------------

        marco_destino = ttk.LabelFrame(
            self,
            text="Archivo de destino",
            padding=12,
        )

        marco_destino.pack(
            fill="x",
            pady=(0, 12),
        )

        self.var_destino = tk.StringVar()

        ttk.Entry(
            marco_destino,
            textvariable=self.var_destino,
            state="readonly",
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8),
        )

        ttk.Button(
            marco_destino,
            text="Seleccionar archivo",
            command=self.seleccionar_destino,
        ).pack(
            side="left",
        )

        # --------------------------------------------------------------
        # Botón generar
        # --------------------------------------------------------------

        ttk.Button(
            self,
            text="Generar reporte CSV",
            command=self.generar,
        ).pack(
            anchor="w",
            pady=(0, 10),
        )

        # --------------------------------------------------------------
        # Mensaje
        # --------------------------------------------------------------

        ttk.Label(
            self,
            textvariable=self.var_mensaje,
            foreground="#5c5f66",
        ).pack(
            anchor="w",
        )

    # ------------------------------------------------------------------
    # Seleccionar destino
    # ------------------------------------------------------------------

    def seleccionar_destino(self):

        ruta = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar reporte",
            defaultextension=".csv",
            filetypes=(
                ("Archivos CSV", "*.csv"),
                ("Todos los archivos", "*.*"),
            ),
        )

        if ruta:
            self.var_destino.set(ruta)

    # ------------------------------------------------------------------
    # Generar reporte
    # ------------------------------------------------------------------

    def generar(self):

        fecha_inicial = self.var_fecha_inicial.get().strip()
        fecha_final = self.var_fecha_final.get().strip()
        ruta_destino = self.var_destino.get().strip()

        exito, mensaje = generar_reporte_csv(
            fecha_inicial,
            fecha_final,
            ruta_destino,
        )

        if not exito:

            self.var_mensaje.set(mensaje)

            messagebox.showerror(
                "No se pudo generar el reporte",
                mensaje,
                parent=self,
            )

            return

        self.var_mensaje.set(mensaje)

        messagebox.showinfo(
            "Reporte generado",
            mensaje,
            parent=self,
        )

    # ------------------------------------------------------------------
    # Limpiar formulario
    # ------------------------------------------------------------------

    def limpiar(self):

        self.var_fecha_inicial.set("")
        self.var_fecha_final.set("")
        self.var_destino.set("")
        self.var_mensaje.set("")

    # ------------------------------------------------------------------
    # Refrescar
    # ------------------------------------------------------------------

    def refrescar(self):
        """
        RF-16. La vista no requiere recargar información
        al cambiar de pestaña.
        """
        return None