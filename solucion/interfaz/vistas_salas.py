"""
Vista gráfica para la gestión de salas.

Permite:
- RF-04 Consultar salas.
- RF-12 Registrar y modificar salas.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from salas.gestion_salas import (
    consultar_salas,
    modificar_sala,
    registrar_sala,
)


def texto_estado(estado):
    if estado == "fuera_de_servicio":
        return "Fuera de servicio"

    return "Disponible"


class VistaSalas(ttk.Frame):

    def __init__(self, padre, on_volver=None, on_cambio=None):
        super().__init__(padre, padding=(20, 16))

        self.on_volver = on_volver
        self.on_cambio = on_cambio
        self._datos_originales = None

        ttk.Label(
            self,
            text="Gestión de salas",
            font=("TkDefaultFont", 14, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            self,
            text="Registre nuevas salas y consulte o modifique las existentes.",
        ).pack(anchor="w", pady=(2, 15))

        self._crear_registro()
        self._crear_consulta()
        self._crear_modificacion()
        self._crear_botones()

        self.refrescar()

    def _crear_registro(self):
        marco = ttk.LabelFrame(
            self,
            text="Registrar sala",
            padding=12,
        )
        marco.pack(fill="x", pady=(0, 12))

        self.var_codigo_nuevo = tk.StringVar()
        self.var_nombre_nuevo = tk.StringVar()
        self.var_capacidad_nueva = tk.StringVar()
        self.var_estado_nuevo = tk.StringVar(value="disponible")

        campos = (
            ("Código", self.var_codigo_nuevo),
            ("Nombre", self.var_nombre_nuevo),
            ("Capacidad", self.var_capacidad_nueva),
        )

        for fila, (etiqueta, variable) in enumerate(campos):
            ttk.Label(
                marco,
                text=etiqueta,
            ).grid(
                row=fila,
                column=0,
                sticky="w",
                padx=(0, 8),
                pady=4,
            )

            ttk.Entry(
                marco,
                textvariable=variable,
                width=35,
            ).grid(
                row=fila,
                column=1,
                sticky="w",
                pady=4,
            )

        ttk.Label(
            marco,
            text="Estado",
        ).grid(
            row=3,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=4,
        )

        ttk.Combobox(
            marco,
            textvariable=self.var_estado_nuevo,
            values=("disponible", "fuera_de_servicio"),
            state="readonly",
            width=32,
        ).grid(
            row=3,
            column=1,
            sticky="w",
            pady=4,
        )

        ttk.Button(
            marco,
            text="Registrar sala",
            command=self.registrar,
        ).grid(
            row=4,
            column=1,
            sticky="w",
            pady=(8, 0),
        )

    def _crear_consulta(self):
        marco = ttk.LabelFrame(
            self,
            text="Salas registradas",
            padding=12,
        )
        marco.pack(fill="both", expand=True, pady=(0, 12))

        columnas = (
            "codigo",
            "nombre",
            "capacidad",
            "estado",
        )

        self.tabla = ttk.Treeview(
            marco,
            columns=columnas,
            show="headings",
            height=8,
            selectmode="browse",
        )

        self.tabla.heading("codigo", text="Código")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("capacidad", text="Capacidad")
        self.tabla.heading("estado", text="Estado")

        self.tabla.column("codigo", width=100, anchor="center")
        self.tabla.column("nombre", width=280)
        self.tabla.column("capacidad", width=100, anchor="center")
        self.tabla.column("estado", width=140, anchor="center")

        barra = ttk.Scrollbar(
            marco,
            orient="vertical",
            command=self.tabla.yview,
        )

        self.tabla.configure(
            yscrollcommand=barra.set
        )

        self.tabla.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        barra.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)

        self.tabla.bind(
            "<<TreeviewSelect>>",
            self._seleccionar_sala,
        )

    def _crear_modificacion(self):
        marco = ttk.LabelFrame(
            self,
            text="Modificar sala seleccionada",
            padding=12,
        )
        marco.pack(fill="x")

        self.var_codigo = tk.StringVar()
        self.var_nombre = tk.StringVar()
        self.var_capacidad = tk.StringVar()
        self.var_estado = tk.StringVar()

        ttk.Label(
            marco,
            text="Código",
        ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)

        ttk.Entry(
            marco,
            textvariable=self.var_codigo,
            state="readonly",
            width=18,
        ).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(
            marco,
            text="Nombre",
        ).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)

        ttk.Entry(
            marco,
            textvariable=self.var_nombre,
            width=35,
        ).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(
            marco,
            text="Capacidad",
        ).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)

        ttk.Entry(
            marco,
            textvariable=self.var_capacidad,
            width=18,
        ).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(
            marco,
            text="Estado",
        ).grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)

        ttk.Combobox(
            marco,
            textvariable=self.var_estado,
            values=("disponible", "fuera_de_servicio"),
            state="readonly",
            width=32,
        ).grid(row=3, column=1, sticky="w", pady=4)

        ttk.Button(
            marco,
            text="Guardar cambios",
            command=self.modificar,
        ).grid(row=4, column=1, sticky="w", pady=(8, 0))

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

    def registrar(self):
        try:
            exito, mensaje = registrar_sala(
                self.var_codigo_nuevo.get(),
                self.var_nombre_nuevo.get(),
                self.var_capacidad_nueva.get(),
                self.var_estado_nuevo.get(),
            )

            if not exito:
                messagebox.showerror(
                    "No se registró la sala",
                    mensaje,
                    parent=self,
                )
                return

            messagebox.showinfo(
                "Sala registrada",
                mensaje,
                parent=self,
            )

            self.var_codigo_nuevo.set("")
            self.var_nombre_nuevo.set("")
            self.var_capacidad_nueva.set("")
            self.var_estado_nuevo.set("disponible")

            self.refrescar()

            if self.on_cambio is not None:
                self.on_cambio()

        except Exception:
            messagebox.showerror(
                "Error",
                "Ocurrió un error inesperado. La operación no se completó.",
                parent=self,
            )

    def refrescar(self):
        try:
            salas = consultar_salas()

            self.tabla.delete(
                *self.tabla.get_children()
            )

            for codigo, nombre, capacidad, estado in salas:
                self.tabla.insert(
                    "",
                    "end",
                    values=(
                        codigo,
                        nombre,
                        capacidad,
                        texto_estado(estado),
                    ),
                )

        except RuntimeError as error:
            messagebox.showerror(
                "Error",
                str(error),
                parent=self,
            )

    def _seleccionar_sala(self, _evento=None):
        seleccion = self.tabla.selection()

        if not seleccion:
            return

        valores = self.tabla.item(
            seleccion[0],
            "values",
        )

        self.var_codigo.set(valores[0])
        self.var_nombre.set(valores[1])
        self.var_capacidad.set(valores[2])

        if valores[3] == "Fuera de servicio":
            self.var_estado.set("fuera_de_servicio")
        else:
            self.var_estado.set("disponible")

        self._datos_originales = (
            self.var_codigo.get(),
            self.var_nombre.get(),
            self.var_capacidad.get(),
            self.var_estado.get(),
        )

    def modificar(self):
        codigo = self.var_codigo.get()

        if not codigo:
            messagebox.showerror(
                "Seleccione una sala",
                "Debe seleccionar una sala de la lista antes de modificarla.",
                parent=self,
            )
            return

        try:
            exito, mensaje = modificar_sala(
                codigo,
                self.var_nombre.get(),
                self.var_capacidad.get(),
                self.var_estado.get(),
            )

            if not exito:
                messagebox.showerror(
                    "No se modificó la sala",
                    mensaje,
                    parent=self,
                )
                return

            messagebox.showinfo(
                "Sala modificada",
                mensaje,
                parent=self,
            )

            self.refrescar()
            self._datos_originales = None

            if self.on_cambio is not None:
                self.on_cambio()

        except Exception:
            messagebox.showerror(
                "Error",
                "Ocurrió un error inesperado. La operación no se completó.",
                parent=self,
            )

    def hay_cambios_pendientes(self):
        registro_pendiente = any([
            self.var_codigo_nuevo.get().strip(),
            self.var_nombre_nuevo.get().strip(),
            self.var_capacidad_nueva.get().strip(),
        ])

        modificacion_pendiente = False

        if self._datos_originales is not None:
            datos_actuales = (
                self.var_codigo.get(),
                self.var_nombre.get(),
                self.var_capacidad.get(),
                self.var_estado.get(),
            )

            modificacion_pendiente = datos_actuales != self._datos_originales

        return registro_pendiente or modificacion_pendiente


    def guardar_pendientes(self):
        if any([
            self.var_codigo_nuevo.get().strip(),
            self.var_nombre_nuevo.get().strip(),
            self.var_capacidad_nueva.get().strip(),
        ]):
            exito, mensaje = registrar_sala(
                self.var_codigo_nuevo.get(),
                self.var_nombre_nuevo.get(),
                self.var_capacidad_nueva.get(),
                self.var_estado_nuevo.get(),
            )

            if not exito:
                return False, mensaje

            self.var_codigo_nuevo.set("")
            self.var_nombre_nuevo.set("")
            self.var_capacidad_nueva.set("")
            self.var_estado_nuevo.set("disponible")

        if self._datos_originales is not None:
            datos_actuales = (
                self.var_codigo.get(),
                self.var_nombre.get(),
                self.var_capacidad.get(),
                self.var_estado.get(),
            )

            if datos_actuales != self._datos_originales:
                exito, mensaje = modificar_sala(
                    self.var_codigo.get(),
                    self.var_nombre.get(),
                    self.var_capacidad.get(),
                    self.var_estado.get(),
                )

                if not exito:
                    return False, mensaje

                self._datos_originales = datos_actuales

        return True, ""

def abrir_ventana_de_prueba():
    from database.inicializacion import inicializar_base_datos

    if not inicializar_base_datos():
        return

    raiz = tk.Tk()
    raiz.title("Gestión de salas")
    raiz.geometry("850x700")
    raiz.minsize(750, 600)

    vista = VistaSalas(raiz)
    vista.pack(fill="both", expand=True)

    raiz.mainloop()


if __name__ == "__main__":
    abrir_ventana_de_prueba()