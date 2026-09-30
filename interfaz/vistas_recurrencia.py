"""
Vista para RF-14: creación de reservaciones recurrentes.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date

from estudiantes.gestion_estudiantes import consultar_estudiantes

from reservaciones.gestion_recurrencia import (
    crear_reservacion_recurrente,
)

from interfaz.vistas_reservaciones import (
    DURACIONES,
    HORAS_DISPONIBLES,
    VistaBase,
    agregar_campo,
    opciones_de_salas,
    codigo_desde_opcion,
    manejar_errores,
    ETIQUETAS,
    COLOR_SECUNDARIO,
)


class VistaReservacionRecurrente(VistaBase):

    titulo = "Reservación recurrente"

    descripcion = (
        "Cree una serie de reservaciones semanales. "
        "La cantidad de ocurrencias debe estar entre 2 y 8."
    )

    def __init__(self, padre, on_cambio=None):
        super().__init__(padre)

        self.on_cambio = on_cambio
        self.nombres_por_carne = {}

        formulario = ttk.Frame(self.contenido)
        formulario.pack(anchor="w")

        self.var_carne = tk.StringVar()
        self.var_sala = tk.StringVar()
        self.var_fecha = tk.StringVar()
        self.var_hora = tk.StringVar()
        self.var_duracion = tk.StringVar()
        self.var_cantidad = tk.StringVar()
        self.var_ocurrencias = tk.StringVar()
        self.var_nombre = tk.StringVar()

        self.combo_carne = ttk.Combobox(
            formulario,
            textvariable=self.var_carne,
            width=16,
        )

        agregar_campo(
            formulario,
            0,
            ETIQUETAS["carne"],
            self.combo_carne,
            ttk.Label(
                formulario,
                textvariable=self.var_nombre,
                foreground=COLOR_SECUNDARIO,
            ),
        )

        self.var_carne.trace_add(
            "write",
            lambda *_: self._mostrar_nombre(),
        )

        self.combo_sala = ttk.Combobox(
            formulario,
            textvariable=self.var_sala,
            width=46,
            state="readonly",
        )

        agregar_campo(
            formulario,
            1,
            ETIQUETAS["sala"],
            self.combo_sala,
            ancho_completo=True,
        )

        agregar_campo(
            formulario,
            2,
            ETIQUETAS["fecha"],
            ttk.Entry(
                formulario,
                textvariable=self.var_fecha,
                width=16,
            ),
        )

        agregar_campo(
            formulario,
            3,
            ETIQUETAS["hora_inicio"],
            ttk.Combobox(
                formulario,
                textvariable=self.var_hora,
                values=HORAS_DISPONIBLES,
                width=8,
            ),
            ttk.Label(
                formulario,
                text="Formato de 24 horas, hora completa",
                foreground=COLOR_SECUNDARIO,
            ),
        )

        agregar_campo(
            formulario,
            4,
            ETIQUETAS["duracion"],
            ttk.Combobox(
                formulario,
                textvariable=self.var_duracion,
                values=DURACIONES,
                width=8,
                state="readonly",
            ),
        )

        agregar_campo(
            formulario,
            5,
            ETIQUETAS["cantidad"],
            ttk.Spinbox(
                formulario,
                textvariable=self.var_cantidad,
                from_=1,
                to=99,
                width=8,
            ),
        )

        agregar_campo(
            formulario,
            6,
            "Cantidad de ocurrencias",
            ttk.Spinbox(
                formulario,
                textvariable=self.var_ocurrencias,
                from_=2,
                to=8,
                width=8,
            ),
        )

        ttk.Button(
            self.botones,
            text="Crear serie recurrente",
            style="Primario.TButton",
            command=self.crear,
        ).pack(side="left")

        ttk.Button(
            self.botones,
            text="Limpiar",
            command=self.limpiar,
        ).pack(
            side="left",
            padx=(8, 0),
        )

        self.limpiar()
        self.refrescar()

    @manejar_errores
    def refrescar(self):
        activos = [
            estudiante
            for estudiante in consultar_estudiantes()
            if estudiante[3] == "activo"
        ]

        self.nombres_por_carne = {
            estudiante[0].upper(): estudiante[1]
            for estudiante in activos
        }

        self.combo_carne["values"] = sorted(
            self.nombres_por_carne
        )

        self.combo_sala["values"] = opciones_de_salas()

        self._mostrar_nombre()

    def _mostrar_nombre(self):
        carne = self.var_carne.get().strip().upper()

        self.var_nombre.set(
            self.nombres_por_carne.get(
                carne,
                "",
            )
        )

    def limpiar(self):
        self.var_carne.set("")
        self.var_sala.set("")
        self.var_fecha.set(
            date.today().isoformat()
        )
        self.var_hora.set("")
        self.var_duracion.set("1")
        self.var_cantidad.set("1")
        self.var_ocurrencias.set("2")

    def hay_cambios_pendientes(self):
        """
        RF-10.

        Indica si se ingresaron datos para una reservación recurrente
        que todavía no ha sido guardada.
        """

        return any([
            self.var_carne.get().strip(),
            self.var_sala.get().strip(),
            self.var_hora.get().strip(),
            self.var_fecha.get().strip() != date.today().isoformat(),
            self.var_duracion.get().strip() != "1",
            self.var_cantidad.get().strip() != "1",
            self.var_ocurrencias.get().strip() != "2",
        ])

    def guardar_pendientes(self):
        """
        RF-10.

        Intenta guardar la serie recurrente pendiente antes
        de cerrar la aplicación.
        """

        if not self.hay_cambios_pendientes():
            return True, ""

        try:
            crear_reservacion_recurrente(
                carne=self.var_carne.get().strip(),
                codigo_sala=codigo_desde_opcion(
                    self.var_sala.get()
                ),
                fecha_inicio=self.var_fecha.get().strip(),
                hora_inicio=self.var_hora.get().strip(),
                duracion=self.var_duracion.get().strip(),
                cantidad_personas=self.var_cantidad.get().strip(),
                cantidad_ocurrencias=self.var_ocurrencias.get().strip(),
            )

        except ValueError as error:
            return False, str(error)

        except Exception:
            return (
                False,
                "Ocurrió un error inesperado. "
                "La serie recurrente no pudo guardarse."
            )

        self.limpiar()

        if self.on_cambio is not None:
            self.on_cambio()

        return True, "Serie recurrente guardada correctamente."

    @manejar_errores
    def crear(self):
        carne = self.var_carne.get().strip()
        codigo_sala = codigo_desde_opcion(
            self.var_sala.get()
        )
        fecha_inicio = self.var_fecha.get().strip()
        hora_inicio = self.var_hora.get().strip()
        duracion = self.var_duracion.get().strip()
        cantidad_personas = self.var_cantidad.get().strip()
        cantidad_ocurrencias = self.var_ocurrencias.get().strip()

        try:
            resultado = crear_reservacion_recurrente(
                carne=carne,
                codigo_sala=codigo_sala,
                fecha_inicio=fecha_inicio,
                hora_inicio=hora_inicio,
                duracion=duracion,
                cantidad_personas=cantidad_personas,
                cantidad_ocurrencias=cantidad_ocurrencias,
            )

        except ValueError as error:
            messagebox.showerror(
                "No se creó la serie recurrente",
                str(error),
                parent=self,
            )
            return

        except Exception:
            messagebox.showerror(
                "Error",
                (
                    "Ocurrió un error inesperado. "
                    "La serie no fue creada."
                ),
                parent=self,
            )
            return

        serie_id = resultado["serie_id"]
        ids = resultado["ids"]

        messagebox.showinfo(
            "Serie recurrente creada",
            (
                f"La serie recurrente se creó correctamente.\n\n"
                f"Serie: {serie_id}\n"
                f"Ocurrencias creadas: {len(ids)}\n"
                f"IDs: {', '.join(str(id_) for id_ in ids)}"
            ),
            parent=self,
        )

        self.limpiar()

        if self.on_cambio is not None:
            self.on_cambio()

def abrir_ventana_de_prueba():
    from database.inicializacion import inicializar_base_datos
    from interfaz.vistas_reservaciones import configurar_estilos

    if not inicializar_base_datos():
        return

    raiz = tk.Tk()

    raiz.title("Reservaciones recurrentes")
    raiz.geometry("900x750")
    raiz.minsize(820, 650)

    configurar_estilos(raiz)

    vista = VistaReservacionRecurrente(raiz)
    vista.pack(
        fill="both",
        expand=True,
    )

    raiz.mainloop()


if __name__ == "__main__":
    abrir_ventana_de_prueba()
