"""
Vistas gráficas (Tkinter) de P2: RF-05, RF-06, RF-07 y RF-08.

Cada vista es un ttk.Frame independiente que la ventana principal puede
montar donde prefiera (pestaña, marco intercambiable, etc.):

    VistaCrearReservacion(padre, on_volver=None, on_cambio=None)
    VistaConsultarReservaciones(padre, on_volver=None)
    VistaBuscarPorEstudiante(padre, on_volver=None)
    VistaDisponibilidad(padre, on_volver=None)

    on_volver -> se llama al pulsar "Volver al panel" (RNF-04).
    on_cambio -> se llama después de crear una reservación, para que el
                 panel principal se actualice (RF-15).

Las vistas no ejecutan SQL: solo llaman funciones de los módulos de
lógica (RNF-07). Cualquier error inesperado se muestra con un mensaje
comprensible, sin trazas técnicas (RNF-04 / RNF-05).

Prueba independiente:  python -m interfaz.vistas_reservaciones
"""

import functools
import tkinter as tk
from datetime import date
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from estudiantes.gestion_estudiantes import consultar_estudiantes
from reservaciones.disponibilidad import consultar_disponibilidad
from reservaciones.gestion_reservaciones import (
    buscar_por_estudiante, consultar_reservaciones, crear_reservacion,
)
from salas.gestion_salas import consultar_salas

# Etiquetas únicas para los mismos datos en todas las vistas (RNF-04).
ETIQUETAS = {
    "carne": "Carné",
    "sala": "Sala",
    "fecha": "Fecha (AAAA-MM-DD)",
    "hora_inicio": "Hora de inicio",
    "duracion": "Duración (horas)",
    "cantidad": "Cantidad de personas",
}

HORAS_DISPONIBLES = [f"{hora:02d}:00" for hora in range(8, 20)]
DURACIONES = ["1", "2"]

COLOR_EXITO = "#1d6b3a"
COLOR_ERROR = "#9f1d24"
COLOR_SECUNDARIO = "#5c5f66"

MENSAJE_ERROR_INESPERADO = (
    "Ocurrió un error inesperado. La operación no se completó; "
    "intente de nuevo o reinicie la aplicación."
)


def manejar_errores(metodo):
    """Evita que una excepción no controlada llegue a la persona usuaria."""
    @functools.wraps(metodo)
    def envoltura(*args, **kwargs):
        try:
            return metodo(*args, **kwargs)
        except Exception:
            messagebox.showerror("Error", MENSAJE_ERROR_INESPERADO)
            return None
    return envoltura


def texto_estado(estado):
    return {
        "activa": "Activa",
        "cancelada": "Cancelada",
        "disponible": "Disponible",
        "fuera_de_servicio": "Fuera de servicio",
    }.get(estado, estado)


def opciones_de_salas():
    """Textos del combo de salas; el código siempre va primero."""
    opciones = []
    for codigo, nombre, capacidad, estado in consultar_salas():
        texto = f"{codigo} - {nombre} (capacidad {capacidad})"
        if estado != "disponible":
            texto += ", fuera de servicio"
        opciones.append(texto)
    return opciones


def codigo_desde_opcion(texto):
    return texto.split(" ", 1)[0].strip() if texto else ""


# ---------------------------------------------------------------------------
# Componentes comunes
# ---------------------------------------------------------------------------

class VistaBase(ttk.Frame):
    """Título, zona de contenido y barra de botones comunes."""

    titulo = ""
    descripcion = ""

    def __init__(self, padre, on_volver=None):
        super().__init__(padre, padding=(20, 16))
        self.on_volver = on_volver

        ttk.Label(self, text=self.titulo, style="Titulo.TLabel").pack(anchor="w")
        if self.descripcion:
            ttk.Label(self, text=self.descripcion, foreground=COLOR_SECUNDARIO,
                      wraplength=640, justify="left").pack(anchor="w", pady=(2, 12))

        self.contenido = ttk.Frame(self)
        self.contenido.pack(fill="both", expand=True)

        self.botones = ttk.Frame(self)
        self.botones.pack(fill="x", pady=(12, 0))

        if on_volver is not None:
            ttk.Button(self.botones, text="Volver al panel",
                       command=self._volver).pack(side="right")

    def _volver(self):
        self.limpiar()
        self.on_volver()

    def limpiar(self):
        """Descarta la operación en curso sin guardar cambios."""

    def refrescar(self):
        """Recarga los datos que dependen de otros módulos."""


def agregar_campo(formulario, fila, etiqueta, widget, ayuda=None, ancho_completo=False):
    ttk.Label(formulario, text=etiqueta).grid(row=fila, column=0, sticky="w",
                                              padx=(0, 12), pady=4)
    widget.grid(row=fila, column=1, sticky="w", pady=4,
                columnspan=2 if ancho_completo else 1)
    if ayuda is not None:
        ayuda.grid(row=fila, column=2, sticky="w", padx=(10, 0))


class TablaReservaciones(ttk.Frame):
    """Tabla con el mismo detalle en RF-06 y RF-07."""

    COLUMNAS = (
        ("id", "ID", 50, "center"),
        ("carne", ETIQUETAS["carne"], 100, "w"),
        ("estudiante", "Estudiante", 170, "w"),
        ("sala", ETIQUETAS["sala"], 60, "center"),
        ("fecha", "Fecha", 95, "center"),
        ("inicio", "Inicio", 60, "center"),
        ("fin", "Fin", 60, "center"),
        ("personas", "Personas", 80, "center"),
        ("estado", "Estado", 90, "center"),
    )

    def __init__(self, padre):
        super().__init__(padre)
        identificadores = [c[0] for c in self.COLUMNAS]
        self.arbol = ttk.Treeview(self, columns=identificadores, show="headings",
                                  height=12, selectmode="browse")
        for ident, titulo, ancho, alineacion in self.COLUMNAS:
            self.arbol.heading(ident, text=titulo)
            self.arbol.column(ident, width=ancho, anchor=alineacion,
                              stretch=(ident == "estudiante"))
        self.arbol.tag_configure("cancelada", foreground=COLOR_SECUNDARIO)

        barra_v = ttk.Scrollbar(self, orient="vertical", command=self.arbol.yview)
        barra_h = ttk.Scrollbar(self, orient="horizontal", command=self.arbol.xview)
        self.arbol.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)

        self.arbol.grid(row=0, column=0, sticky="nsew")
        barra_v.grid(row=0, column=1, sticky="ns")
        barra_h.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def mostrar(self, filas):
        self.arbol.delete(*self.arbol.get_children())
        for (id_r, carne, estudiante, codigo_sala, _nombre_sala, fecha,
             inicio, fin, personas, estado) in filas:
            self.arbol.insert(
                "", "end",
                values=(id_r, carne, estudiante or "", codigo_sala, fecha,
                        inicio, fin, personas, texto_estado(estado)),
                tags=(estado,),
            )


# ---------------------------------------------------------------------------
# RF-05. Crear reservación
# ---------------------------------------------------------------------------

class VistaCrearReservacion(VistaBase):

    titulo = "Crear reservación"
    descripcion = ("Complete todos los campos. El sistema valida horario, "
                   "capacidad, disponibilidad y el límite de reservaciones "
                   "antes de guardar.")

    def __init__(self, padre, on_volver=None, on_cambio=None):
        super().__init__(padre, on_volver)
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
        self.var_nombre = tk.StringVar()

        self.combo_carne = ttk.Combobox(formulario, textvariable=self.var_carne, width=16)
        agregar_campo(formulario, 0, ETIQUETAS["carne"], self.combo_carne,
                      ttk.Label(formulario, textvariable=self.var_nombre,
                                foreground=COLOR_SECUNDARIO))
        self.var_carne.trace_add("write", lambda *_: self._mostrar_nombre())

        self.combo_sala = ttk.Combobox(formulario, textvariable=self.var_sala,
                                       width=46, state="readonly")
        agregar_campo(formulario, 1, ETIQUETAS["sala"], self.combo_sala,
                      ancho_completo=True)

        agregar_campo(formulario, 2, ETIQUETAS["fecha"],
                      ttk.Entry(formulario, textvariable=self.var_fecha, width=16))
        agregar_campo(formulario, 3, ETIQUETAS["hora_inicio"],
                      ttk.Combobox(formulario, textvariable=self.var_hora,
                                   values=HORAS_DISPONIBLES, width=8),
                      ttk.Label(formulario, text="Formato de 24 horas, hora completa",
                                foreground=COLOR_SECUNDARIO))
        agregar_campo(formulario, 4, ETIQUETAS["duracion"],
                      ttk.Combobox(formulario, textvariable=self.var_duracion,
                                   values=DURACIONES, width=8, state="readonly"))
        agregar_campo(formulario, 5, ETIQUETAS["cantidad"],
                      ttk.Spinbox(formulario, textvariable=self.var_cantidad,
                                  from_=1, to=99, width=8))

        ttk.Button(self.botones, text="Crear reservación", style="Primario.TButton",
                   command=self.crear).pack(side="left")
        ttk.Button(self.botones, text="Limpiar",
                   command=self.limpiar).pack(side="left", padx=(8, 0))

        self.limpiar()
        self.refrescar()

    @manejar_errores
    def refrescar(self):
        activos = [e for e in consultar_estudiantes() if e[3] == "activo"]
        self.nombres_por_carne = {e[0].upper(): e[1] for e in activos}
        self.combo_carne["values"] = sorted(self.nombres_por_carne)
        self.combo_sala["values"] = opciones_de_salas()
        self._mostrar_nombre()

    def _mostrar_nombre(self):
        carne = self.var_carne.get().strip().upper()
        self.var_nombre.set(self.nombres_por_carne.get(carne, ""))

    def limpiar(self):
        self.var_carne.set("")
        self.var_sala.set("")
        self.var_fecha.set(date.today().isoformat())
        self.var_hora.set("")
        self.var_duracion.set("1")
        self.var_cantidad.set("1")

    @manejar_errores
    def crear(self):
        exito, mensaje, _ = crear_reservacion(
            self.var_carne.get(),
            codigo_desde_opcion(self.var_sala.get()),
            self.var_fecha.get(),
            self.var_hora.get(),
            self.var_duracion.get(),
            self.var_cantidad.get(),
        )

        if not exito:
            # Se conservan los datos para que la persona corrija solo el campo indicado.
            messagebox.showerror("No se creó la reservación", mensaje, parent=self)
            return

        messagebox.showinfo("Reservación creada", mensaje, parent=self)
        self.limpiar()
        if self.on_cambio is not None:
            self.on_cambio()


# ---------------------------------------------------------------------------
# RF-06. Consultar reservaciones
# ---------------------------------------------------------------------------

class VistaConsultarReservaciones(VistaBase):

    titulo = "Reservaciones"
    descripcion = ("Historial completo, incluidas las canceladas, ordenado por "
                   "fecha y hora.")

    def __init__(self, padre, on_volver=None):
        super().__init__(padre, on_volver)
        self.var_resumen = tk.StringVar()
        ttk.Label(self.contenido, textvariable=self.var_resumen,
                  foreground=COLOR_SECUNDARIO).pack(anchor="w", pady=(0, 6))
        self.tabla = TablaReservaciones(self.contenido)
        self.tabla.pack(fill="both", expand=True)

        ttk.Button(self.botones, text="Actualizar",
                   command=self.refrescar).pack(side="left")
        self.refrescar()

    @manejar_errores
    def refrescar(self):
        try:
            filas = consultar_reservaciones()
        except RuntimeError as error:
            self.tabla.mostrar([])
            self.var_resumen.set(str(error))
            return

        self.tabla.mostrar(filas)
        if not filas:
            self.var_resumen.set("Todavía no hay reservaciones registradas. "
                                 "Use Crear reservación para registrar la primera.")
        else:
            activas = sum(1 for f in filas if f[-1] == "activa")
            self.var_resumen.set(f"{len(filas)} reservaciones: {activas} activas y "
                                 f"{len(filas) - activas} canceladas.")


# ---------------------------------------------------------------------------
# RF-07. Buscar por estudiante
# ---------------------------------------------------------------------------

class VistaBuscarPorEstudiante(VistaBase):

    titulo = "Buscar reservaciones por estudiante"
    descripcion = "Escriba el carné; no importa si usa mayúsculas o minúsculas."

    def __init__(self, padre, on_volver=None):
        super().__init__(padre, on_volver)
        barra = ttk.Frame(self.contenido)
        barra.pack(anchor="w", pady=(0, 8))

        self.var_carne = tk.StringVar()
        ttk.Label(barra, text=ETIQUETAS["carne"]).pack(side="left", padx=(0, 8))
        entrada = ttk.Entry(barra, textvariable=self.var_carne, width=18)
        entrada.pack(side="left")
        entrada.bind("<Return>", lambda _evento: self.buscar())
        ttk.Button(barra, text="Buscar", style="Primario.TButton",
                   command=self.buscar).pack(side="left", padx=(8, 0))

        self.var_mensaje = tk.StringVar()
        self.etiqueta_mensaje = ttk.Label(self.contenido, textvariable=self.var_mensaje,
                                          wraplength=640, justify="left")
        self.etiqueta_mensaje.pack(anchor="w", pady=(0, 6))

        self.tabla = TablaReservaciones(self.contenido)
        self.tabla.pack(fill="both", expand=True)

        ttk.Button(self.botones, text="Limpiar",
                   command=self.limpiar).pack(side="left")

    def limpiar(self):
        self.var_carne.set("")
        self.var_mensaje.set("")
        self.tabla.mostrar([])

    @manejar_errores
    def buscar(self):
        exito, mensaje, filas = buscar_por_estudiante(self.var_carne.get())
        self.var_mensaje.set(mensaje)
        self.etiqueta_mensaje.configure(
            foreground=COLOR_SECUNDARIO if exito else COLOR_ERROR)
        self.tabla.mostrar(filas)


# ---------------------------------------------------------------------------
# RF-08. Consultar disponibilidad
# ---------------------------------------------------------------------------

class VistaDisponibilidad(VistaBase):

    titulo = "Consultar disponibilidad"
    descripcion = ("Verifica si una sala está libre en un horario. "
                   "Esta consulta no crea ninguna reservación.")

    def __init__(self, padre, on_volver=None):
        super().__init__(padre, on_volver)
        formulario = ttk.Frame(self.contenido)
        formulario.pack(anchor="w")

        self.var_sala = tk.StringVar()
        self.var_fecha = tk.StringVar()
        self.var_hora = tk.StringVar()
        self.var_duracion = tk.StringVar()

        self.combo_sala = ttk.Combobox(formulario, textvariable=self.var_sala,
                                       width=46, state="readonly")
        agregar_campo(formulario, 0, ETIQUETAS["sala"], self.combo_sala,
                      ancho_completo=True)
        agregar_campo(formulario, 1, ETIQUETAS["fecha"],
                      ttk.Entry(formulario, textvariable=self.var_fecha, width=16))
        agregar_campo(formulario, 2, ETIQUETAS["hora_inicio"],
                      ttk.Combobox(formulario, textvariable=self.var_hora,
                                   values=HORAS_DISPONIBLES, width=8))
        agregar_campo(formulario, 3, ETIQUETAS["duracion"],
                      ttk.Combobox(formulario, textvariable=self.var_duracion,
                                   values=DURACIONES, width=8, state="readonly"))

        self.var_resultado = tk.StringVar()
        self.etiqueta_resultado = ttk.Label(self.contenido, textvariable=self.var_resultado,
                                            style="Resultado.TLabel",
                                            wraplength=640, justify="left")
        self.etiqueta_resultado.pack(anchor="w", pady=(14, 0))

        ttk.Button(self.botones, text="Consultar disponibilidad",
                   style="Primario.TButton", command=self.consultar).pack(side="left")
        ttk.Button(self.botones, text="Limpiar",
                   command=self.limpiar).pack(side="left", padx=(8, 0))

        self.limpiar()
        self.refrescar()

    @manejar_errores
    def refrescar(self):
        self.combo_sala["values"] = opciones_de_salas()

    def limpiar(self):
        self.var_sala.set("")
        self.var_fecha.set(date.today().isoformat())
        self.var_hora.set("")
        self.var_duracion.set("1")
        self.var_resultado.set("")

    @manejar_errores
    def consultar(self):
        exito, mensaje, disponible = consultar_disponibilidad(
            codigo_desde_opcion(self.var_sala.get()),
            self.var_fecha.get(),
            self.var_hora.get(),
            self.var_duracion.get(),
        )
        if exito and disponible:
            self.etiqueta_resultado.configure(foreground=COLOR_EXITO)
            self.var_resultado.set("Disponible. " + mensaje)
        elif exito:
            self.etiqueta_resultado.configure(foreground=COLOR_ERROR)
            self.var_resultado.set(mensaje)
        else:
            self.etiqueta_resultado.configure(foreground=COLOR_ERROR)
            self.var_resultado.set("Revise los datos. " + mensaje)


# ---------------------------------------------------------------------------
# Estilos y ventana de prueba del módulo
# ---------------------------------------------------------------------------

def configurar_estilos(raiz):
    """Estilos usados por estas vistas. La ventana principal puede llamarla una vez."""
    estilo = ttk.Style(raiz)
    familia = tkfont.nametofont("TkDefaultFont").actual()["family"]
    estilo.configure("Titulo.TLabel", font=(familia, 14, "bold"))
    estilo.configure("Resultado.TLabel", font=(familia, 11, "bold"))
    estilo.configure("Primario.TButton", padding=(12, 4))
    return estilo


def abrir_ventana_de_prueba():
    """Ventana independiente para probar RF-05 a RF-08 antes de integrar."""
    from database.inicializacion import inicializar_base_datos

    raiz = tk.Tk()
    raiz.title("Reservaciones (módulo P2)")
    raiz.minsize(820, 520)

    if not inicializar_base_datos():
        raiz.withdraw()
        messagebox.showerror("Error", "No fue posible abrir la base de datos.")
        raiz.destroy()
        return

    configurar_estilos(raiz)
    pestanas = ttk.Notebook(raiz)
    pestanas.pack(fill="both", expand=True, padx=8, pady=8)

    consultar = VistaConsultarReservaciones(pestanas)
    vistas = [
        VistaCrearReservacion(pestanas, on_cambio=consultar.refrescar),
        consultar,
        VistaBuscarPorEstudiante(pestanas),
        VistaDisponibilidad(pestanas),
    ]
    nombres = ["Crear", "Reservaciones", "Buscar por estudiante", "Disponibilidad"]
    for vista, nombre in zip(vistas, nombres):
        pestanas.add(vista, text=nombre)

    pestanas.bind("<<NotebookTabChanged>>",
                  lambda _e: vistas[pestanas.index("current")].refrescar())
    raiz.mainloop()


if __name__ == "__main__":
    abrir_ventana_de_prueba()
