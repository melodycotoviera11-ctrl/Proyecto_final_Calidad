"""
Vista gráfica para la gestión de estudiantes.

Permite:
- RF-02 Registrar estudiante.
- RF-03 Consultar estudiantes.
- RF-11 Modificar nombre, correo y estado del estudiante.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from estudiantes.gestion_estudiantes import (
    consultar_estudiantes,
    modificar_estudiante,
    registrar_estudiante,
)


class VistaEstudiantes(ttk.Frame):

    def __init__(self, padre, on_volver=None):
        super().__init__(padre, padding=(20, 16))

        self.on_volver = on_volver
        self._datos_originales = None

        ttk.Label(
            self,
            text="Gestión de estudiantes",
            font=("TkDefaultFont", 14, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            self,
            text="Registre estudiantes y consulte o modifique la información existente.",
        ).pack(anchor="w", pady=(2, 15))

        self._crear_registro()
        self._crear_consulta()
        self._crear_modificacion()
        self._crear_botones()

        self.refrescar()

    # ------------------------------------------------------------------
    # Registro de estudiantes
    # ------------------------------------------------------------------

    def _crear_registro(self):
        marco = ttk.LabelFrame(
            self,
            text="Registrar estudiante",
            padding=12,
        )
        marco.pack(fill="x", pady=(0, 12))

        self.var_carne_nuevo = tk.StringVar()
        self.var_nombre_nuevo = tk.StringVar()
        self.var_correo_nuevo = tk.StringVar()

        ttk.Label(marco, text="Carné").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Entry(
            marco,
            textvariable=self.var_carne_nuevo,
            width=18,
        ).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(marco, text="Nombre completo").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Entry(
            marco,
            textvariable=self.var_nombre_nuevo,
            width=40,
        ).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(marco, text="Correo electrónico").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Entry(
            marco,
            textvariable=self.var_correo_nuevo,
            width=40,
        ).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Button(
            marco,
            text="Registrar estudiante",
            command=self.registrar,
        ).grid(row=3, column=1, sticky="w", pady=(8, 0))

    # ------------------------------------------------------------------
    # Consulta de estudiantes
    # ------------------------------------------------------------------

    def _crear_consulta(self):
        marco = ttk.LabelFrame(
            self,
            text="Estudiantes registrados",
            padding=12,
        )
        marco.pack(fill="both", expand=True, pady=(0, 12))

        columnas = ("carne", "nombre", "correo", "estado")

        self.tabla = ttk.Treeview(
            marco,
            columns=columnas,
            show="headings",
            height=8,
            selectmode="browse",
        )

        self.tabla.heading("carne", text="Carné")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("correo", text="Correo")
        self.tabla.heading("estado", text="Estado")

        self.tabla.column("carne", width=120, anchor="center")
        self.tabla.column("nombre", width=220)
        self.tabla.column("correo", width=240)
        self.tabla.column("estado", width=100, anchor="center")

        barra = ttk.Scrollbar(
            marco,
            orient="vertical",
            command=self.tabla.yview,
        )

        self.tabla.configure(yscrollcommand=barra.set)

        self.tabla.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")

        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)

        self.tabla.bind(
            "<<TreeviewSelect>>",
            self._seleccionar_estudiante,
        )

    # ------------------------------------------------------------------
    # Modificación
    # ------------------------------------------------------------------

    def _crear_modificacion(self):
        marco = ttk.LabelFrame(
            self,
            text="Modificar estudiante seleccionado",
            padding=12,
        )
        marco.pack(fill="x")

        self.var_carne = tk.StringVar()
        self.var_nombre = tk.StringVar()
        self.var_correo = tk.StringVar()
        self.var_estado = tk.StringVar()

        ttk.Label(marco, text="Carné").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4
        )

        ttk.Entry(
            marco,
            textvariable=self.var_carne,
            width=18,
            state="readonly",
        ).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(marco, text="Nombre completo").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4
        )

        ttk.Entry(
            marco,
            textvariable=self.var_nombre,
            width=40,
        ).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(marco, text="Correo electrónico").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=4
        )

        ttk.Entry(
            marco,
            textvariable=self.var_correo,
            width=40,
        ).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(marco, text="Estado").grid(
            row=3, column=0, sticky="w", padx=(0, 8), pady=4
        )

        ttk.Combobox(
            marco,
            textvariable=self.var_estado,
            values=("activo", "inactivo"),
            state="readonly",
            width=16,
        ).grid(row=3, column=1, sticky="w", pady=4)

        ttk.Button(
            marco,
            text="Guardar cambios",
            command=self.modificar,
        ).grid(row=4, column=1, sticky="w", pady=(8, 0))

    # ------------------------------------------------------------------
    # Botones generales
    # ------------------------------------------------------------------

    def _crear_botones(self):
        botones = ttk.Frame(self)
        botones.pack(fill="x", pady=(12, 0))

        ttk.Button(
            botones,
            text="Actualizar",
            command=self.refrescar,
        ).pack(side="left")

        if self.on_volver is not None:
            ttk.Button(
                botones,
                text="Volver al panel",
                command=self.on_volver,
            ).pack(side="right")

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def registrar(self):
        try:
            exito, mensaje = registrar_estudiante(
                self.var_carne_nuevo.get(),
                self.var_nombre_nuevo.get(),
                self.var_correo_nuevo.get(),
            )

            if not exito:
                messagebox.showerror(
                    "No se registró el estudiante",
                    mensaje,
                    parent=self,
                )
                return

            messagebox.showinfo(
                "Estudiante registrado",
                mensaje,
                parent=self,
            )

            self.var_carne_nuevo.set("")
            self.var_nombre_nuevo.set("")
            self.var_correo_nuevo.set("")

            self.refrescar()

        except Exception:
            messagebox.showerror(
                "Error",
                "Ocurrió un error inesperado. La operación no se completó.",
                parent=self,
            )

    def refrescar(self):
        try:
            estudiantes = consultar_estudiantes()

            self.tabla.delete(*self.tabla.get_children())

            for carne, nombre, correo, estado in estudiantes:
                self.tabla.insert(
                    "",
                    "end",
                    values=(
                        carne,
                        nombre,
                        correo,
                        estado.capitalize(),
                    ),
                )

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error),
                parent=self,
            )

    def _seleccionar_estudiante(self, _evento=None):
        seleccion = self.tabla.selection()

        if not seleccion:
            return

        valores = self.tabla.item(
            seleccion[0],
            "values",
        )

        self.var_carne.set(valores[0])
        self.var_nombre.set(valores[1])
        self.var_correo.set(valores[2])
        self.var_estado.set(valores[3].lower())
        self._datos_originales = (
            self.var_carne.get(),
            self.var_nombre.get(),
            self.var_correo.get(),
            self.var_estado.get(),
        )

    def modificar(self):
        carne = self.var_carne.get()

        if not carne:
            messagebox.showerror(
                "Seleccione un estudiante",
                "Debe seleccionar un estudiante de la lista antes de modificarlo.",
                parent=self,
            )
            return

        # RF-11: confirmación visual antes de aplicar la modificación.
        confirmar = messagebox.askyesno(
            "Confirmar modificación",
            (
                f"¿Desea guardar los cambios del estudiante "
                f"{carne}?"
            ),
            parent=self,
        )

        if not confirmar:
            return

        try:
            exito, mensaje = modificar_estudiante(
                carne,
                self.var_nombre.get(),
                self.var_correo.get(),
                self.var_estado.get(),
            )

            if not exito:
                messagebox.showerror(
                    "No se modificó el estudiante",
                    mensaje,
                    parent=self,
                )
                return

            messagebox.showinfo(
                "Estudiante modificado",
                mensaje,
                parent=self,
            )

            self.refrescar()
            self._datos_originales = None

        except Exception:
            messagebox.showerror(
                "Error",
                "Ocurrió un error inesperado. La operación no se completó.",
                parent=self,
            )

    def hay_cambios_pendientes(self):
        registro_pendiente = any([
            self.var_carne_nuevo.get().strip(),
            self.var_nombre_nuevo.get().strip(),
            self.var_correo_nuevo.get().strip(),
        ])

        modificacion_pendiente = False

        if self._datos_originales is not None:
            datos_actuales = (
                self.var_carne.get(),
                self.var_nombre.get(),
                self.var_correo.get(),
                self.var_estado.get(),
            )

            modificacion_pendiente = datos_actuales != self._datos_originales

        return registro_pendiente or modificacion_pendiente


    def guardar_pendientes(self):
        if any([
            self.var_carne_nuevo.get().strip(),
            self.var_nombre_nuevo.get().strip(),
            self.var_correo_nuevo.get().strip(),
        ]):
            exito, mensaje = registrar_estudiante(
                self.var_carne_nuevo.get(),
                self.var_nombre_nuevo.get(),
                self.var_correo_nuevo.get(),
            )

            if not exito:
                return False, mensaje

            self.var_carne_nuevo.set("")
            self.var_nombre_nuevo.set("")
            self.var_correo_nuevo.set("")

        if self._datos_originales is not None:
            datos_actuales = (
                self.var_carne.get(),
                self.var_nombre.get(),
                self.var_correo.get(),
                self.var_estado.get(),
            )

            if datos_actuales != self._datos_originales:
                exito, mensaje = modificar_estudiante(
                    self.var_carne.get(),
                    self.var_nombre.get(),
                    self.var_correo.get(),
                    self.var_estado.get(),
                )

                if not exito:
                    return False, mensaje

                self._datos_originales = datos_actuales

        return True, ""

def abrir_ventana_de_prueba():
    """Permite probar esta vista antes de integrarla a la ventana principal."""

    from database.inicializacion import inicializar_base_datos

    if not inicializar_base_datos():
        return

    raiz = tk.Tk()
    raiz.title("Gestión de estudiantes")
    raiz.geometry("850x700")
    raiz.minsize(750, 600)

    vista = VistaEstudiantes(raiz)
    vista.pack(
        fill="both",
        expand=True,
    )

    raiz.mainloop()


if __name__ == "__main__":
    abrir_ventana_de_prueba()