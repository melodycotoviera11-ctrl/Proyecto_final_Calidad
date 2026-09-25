"""
Vista para modificar y cancelar reservaciones.

Permite:
- RF-09 Cancelar reservación.
- RF-13 Modificar reservación.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from reservaciones.gestion_reservaciones import (
    cancelar_reservacion,
    consultar_reservaciones,
    modificar_reservacion,
)

from interfaz.vistas_reservaciones import (
    DURACIONES,
    HORAS_DISPONIBLES,
    TablaReservaciones,
    codigo_desde_opcion,
    opciones_de_salas,
)


class VistaGestionReservaciones(ttk.Frame):

    def __init__(self, padre, on_volver=None, on_cambio=None):
        super().__init__(padre, padding=(20, 16))

        self.on_volver = on_volver
        self.on_cambio = on_cambio
        self._datos_originales = None

        ttk.Label(
            self,
            text="Gestionar reservaciones",
            style="Titulo.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            self,
            text=(
                "Seleccione una reservación para modificar sus datos "
                "o cancelar una reservación activa."
            ),
        ).pack(anchor="w", pady=(2, 12))

        self._crear_tabla()
        self._crear_formulario()
        self._crear_botones()

        self.refrescar()

    def _crear_tabla(self):
        self.tabla = TablaReservaciones(self)
        self.tabla.pack(
            fill="both",
            expand=True,
            pady=(0, 12),
        )

        self.tabla.arbol.bind(
            "<<TreeviewSelect>>",
            self._seleccionar_reservacion,
        )

    def _crear_formulario(self):
        marco = ttk.LabelFrame(
            self,
            text="Reservación seleccionada",
            padding=12,
        )
        marco.pack(fill="x")

        self.var_id = tk.StringVar()
        self.var_sala = tk.StringVar()
        self.var_fecha = tk.StringVar()
        self.var_hora = tk.StringVar()
        self.var_duracion = tk.StringVar()
        self.var_cantidad = tk.StringVar()

        ttk.Label(
            marco,
            text="ID",
        ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)

        ttk.Entry(
            marco,
            textvariable=self.var_id,
            state="readonly",
            width=12,
        ).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(
            marco,
            text="Sala",
        ).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)

        self.combo_sala = ttk.Combobox(
            marco,
            textvariable=self.var_sala,
            state="readonly",
            width=46,
        )

        self.combo_sala.grid(
            row=1,
            column=1,
            sticky="w",
            pady=4,
        )

        ttk.Label(
            marco,
            text="Fecha (AAAA-MM-DD)",
        ).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)

        ttk.Entry(
            marco,
            textvariable=self.var_fecha,
            width=16,
        ).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(
            marco,
            text="Hora de inicio",
        ).grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)

        ttk.Combobox(
            marco,
            textvariable=self.var_hora,
            values=HORAS_DISPONIBLES,
            width=10,
        ).grid(row=3, column=1, sticky="w", pady=4)

        ttk.Label(
            marco,
            text="Duración",
        ).grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)

        ttk.Combobox(
            marco,
            textvariable=self.var_duracion,
            values=DURACIONES,
            state="readonly",
            width=10,
        ).grid(row=4, column=1, sticky="w", pady=4)

        ttk.Label(
            marco,
            text="Cantidad de personas",
        ).grid(row=5, column=0, sticky="w", padx=(0, 8), pady=4)

        ttk.Spinbox(
            marco,
            textvariable=self.var_cantidad,
            from_=1,
            to=99,
            width=10,
        ).grid(row=5, column=1, sticky="w", pady=4)

    def _crear_botones(self):
        botones = ttk.Frame(self)
        botones.pack(fill="x", pady=(12, 0))

        ttk.Button(
            botones,
            text="Guardar cambios",
            style="Primario.TButton",
            command=self.modificar,
        ).pack(side="left")

        ttk.Button(
            botones,
            text="Cancelar reservación",
            command=self.cancelar,
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            botones,
            text="Actualizar",
            command=self.refrescar,
        ).pack(side="left", padx=(8, 0))

        if self.on_volver is not None:
            ttk.Button(
                botones,
                text="Volver al panel",
                command=self.on_volver,
            ).pack(side="right")

    def refrescar(self):
        try:
            filas = consultar_reservaciones()

            self.tabla.mostrar(filas)
            self.combo_sala["values"] = opciones_de_salas()

            self.limpiar_seleccion()

        except Exception:
            messagebox.showerror(
                "Error",
                "No fue posible cargar las reservaciones.",
                parent=self,
            )

    def limpiar_seleccion(self):
        self.var_id.set("")
        self.var_sala.set("")
        self.var_fecha.set("")
        self.var_hora.set("")
        self.var_duracion.set("1")
        self.var_cantidad.set("1")
        self._datos_originales = None

    def _seleccionar_reservacion(self, _evento=None):
        seleccion = self.tabla.arbol.selection()

        if not seleccion:
            return

        valores = self.tabla.arbol.item(
            seleccion[0],
            "values",
        )

        id_reservacion = valores[0]
        codigo_sala = valores[3]
        fecha = valores[4]
        hora_inicio = valores[5]
        hora_fin = valores[6]
        cantidad = valores[7]

        hora_inicio_numero = int(
            str(hora_inicio).split(":")[0]
        )

        hora_fin_numero = int(
            str(hora_fin).split(":")[0]
        )

        duracion = hora_fin_numero - hora_inicio_numero

        self.var_id.set(id_reservacion)
        self.var_fecha.set(fecha)
        self.var_hora.set(hora_inicio)
        self.var_duracion.set(str(duracion))
        self.var_cantidad.set(cantidad)

        for opcion in self.combo_sala["values"]:
            if str(opcion).startswith(f"{codigo_sala} "):
                self.var_sala.set(opcion)
                break

        self._datos_originales = (
            self.var_id.get(),
            codigo_desde_opcion(self.var_sala.get()),
            self.var_fecha.get(),
            self.var_hora.get(),
            self.var_duracion.get(),
            self.var_cantidad.get(),
        )

    def modificar(self):
        id_reservacion = self.var_id.get()

        if not id_reservacion:
            messagebox.showerror(
                "Seleccione una reservación",
                "Debe seleccionar una reservación antes de modificarla.",
                parent=self,
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar modificación",
            f"¿Desea guardar los cambios de la reservación {id_reservacion}?",
            parent=self,
        )

        if not confirmar:
            return

        try:
            exito, mensaje, _ = modificar_reservacion(
                id_reservacion,
                codigo_desde_opcion(
                    self.var_sala.get()
                ),
                self.var_fecha.get(),
                self.var_hora.get(),
                self.var_duracion.get(),
                self.var_cantidad.get(),
            )

            if not exito:
                messagebox.showerror(
                    "No se modificó la reservación",
                    mensaje,
                    parent=self,
                )
                return

            messagebox.showinfo(
                "Reservación modificada",
                mensaje,
                parent=self,
            )

            self.refrescar()

            if self.on_cambio is not None:
                self.on_cambio()

        except Exception:
            messagebox.showerror(
                "Error",
                "Ocurrió un error inesperado. La operación no se completó.",
                parent=self,
            )

    def cancelar(self):
        id_reservacion = self.var_id.get()

        if not id_reservacion:
            messagebox.showerror(
                "Seleccione una reservación",
                "Debe seleccionar una reservación antes de cancelarla.",
                parent=self,
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar cancelación",
            f"¿Desea cancelar la reservación {id_reservacion}?",
            parent=self,
        )

        if not confirmar:
            return

        try:
            exito, mensaje, _ = cancelar_reservacion(
                id_reservacion
            )

            if not exito:
                messagebox.showerror(
                    "No se canceló la reservación",
                    mensaje,
                    parent=self,
                )
                return

            messagebox.showinfo(
                "Reservación cancelada",
                mensaje,
                parent=self,
            )

            self.refrescar()

            if self.on_cambio is not None:
                self.on_cambio()

        except Exception:
            messagebox.showerror(
                "Error",
                "Ocurrió un error inesperado. La operación no se completó.",
                parent=self,
            )

    def hay_cambios_pendientes(self):
        if self._datos_originales is None:
            return False

        datos_actuales = (
            self.var_id.get(),
            codigo_desde_opcion(self.var_sala.get()),
            self.var_fecha.get(),
            self.var_hora.get(),
            self.var_duracion.get(),
            self.var_cantidad.get(),
        )

        return datos_actuales != self._datos_originales


    def guardar_pendientes(self):
        if not self.hay_cambios_pendientes():
            return True, ""

        exito, mensaje, _ = modificar_reservacion(
            self.var_id.get(),
            codigo_desde_opcion(self.var_sala.get()),
            self.var_fecha.get(),
            self.var_hora.get(),
            self.var_duracion.get(),
            self.var_cantidad.get(),
        )

        if not exito:
            return False, mensaje

        return True, mensaje

def abrir_ventana_de_prueba():
    from database.inicializacion import inicializar_base_datos
    from interfaz.vistas_reservaciones import configurar_estilos

    if not inicializar_base_datos():
        return

    raiz = tk.Tk()
    raiz.title("Gestión de reservaciones")
    raiz.geometry("900x750")
    raiz.minsize(820, 650)

    configurar_estilos(raiz)

    vista = VistaGestionReservaciones(raiz)
    vista.pack(
        fill="both",
        expand=True,
    )

    raiz.mainloop()


if __name__ == "__main__":
    abrir_ventana_de_prueba()