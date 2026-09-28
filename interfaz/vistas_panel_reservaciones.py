
"""
Panel unificado para la gestión de reservaciones.

Integra:
- RF-05 Crear reservación.
- RF-06 Consultar reservaciones.
- RF-07 Buscar por estudiante.
- RF-08 Consultar disponibilidad.
- RF-09 Cancelar reservación.
- RF-13 Modificar reservación.
- RF-14 Crear reservaciones recurrentes.
- RF-15 Mostrar panel y disponibilidad.
"""

import tkinter as tk
from datetime import date, datetime
from tkinter import ttk

from reservaciones.gestion_reservaciones import (
    consultar_reservaciones,
)

from salas.gestion_salas import (
    consultar_salas,
)

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

# ============================================================================
# RF-15. PANEL PRINCIPAL
# ============================================================================

class VistaPanelPrincipal(ttk.Frame):
    """
    RF-15. Panel principal para mostrar información actualizada
    de las reservaciones y ocupación de las salas.

    Permite:
    - Consultar las reservaciones del día.
    - Mostrar las próximas reservaciones.
    - Mostrar la ocupación por sala.
    - Filtrar por fecha.
    - Filtrar por sala.
    - Filtrar por estado.
    - Combinar los filtros.
    - Mostrar un mensaje cuando no existen resultados.
    - Actualizarse después de crear, modificar o cancelar.
    """

    def __init__(self, padre):
        super().__init__(
            padre,
            padding=(20, 16),
        )

        self.var_fecha = tk.StringVar(
            value=date.today().isoformat()
        )

        self.var_sala = tk.StringVar(
            value="Todas"
        )

        self.var_estado = tk.StringVar(
            value="Todos"
        )

        self.var_mensaje = tk.StringVar()

        self.salas = []

        self._crear_interfaz()
        self.refrescar()

    # ----------------------------------------------------------------------
    # Construcción de interfaz
    # ----------------------------------------------------------------------

    def _crear_interfaz(self):

        ttk.Label(
            self,
            text="Panel principal",
            font=("TkDefaultFont", 16, "bold"),
        ).pack(
            anchor="w"
        )

        ttk.Label(
            self,
            text=(
                "Consulte las reservaciones del día, las próximas "
                "reservaciones y la ocupación de las salas."
            ),
            foreground="#5c5f66",
        ).pack(
            anchor="w",
            pady=(2, 12),
        )

        # ------------------------------------------------------------------
        # Filtros
        # ------------------------------------------------------------------

        filtros = ttk.LabelFrame(
            self,
            text="Filtros",
            padding=10,
        )

        filtros.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Label(
            filtros,
            text="Fecha (AAAA-MM-DD)",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 6),
            pady=4,
        )

        ttk.Entry(
            filtros,
            textvariable=self.var_fecha,
            width=15,
        ).grid(
            row=0,
            column=1,
            sticky="w",
            pady=4,
        )

        ttk.Label(
            filtros,
            text="Sala",
        ).grid(
            row=0,
            column=2,
            sticky="w",
            padx=(18, 6),
            pady=4,
        )

        self.combo_sala = ttk.Combobox(
            filtros,
            textvariable=self.var_sala,
            width=28,
            state="readonly",
        )

        self.combo_sala.grid(
            row=0,
            column=3,
            sticky="w",
            pady=4,
        )

        ttk.Label(
            filtros,
            text="Estado",
        ).grid(
            row=0,
            column=4,
            sticky="w",
            padx=(18, 6),
            pady=4,
        )

        self.combo_estado = ttk.Combobox(
            filtros,
            textvariable=self.var_estado,
            values=(
                "Todos",
                "Activa",
                "Cancelada",
            ),
            width=12,
            state="readonly",
        )

        self.combo_estado.grid(
            row=0,
            column=5,
            sticky="w",
            pady=4,
        )

        ttk.Button(
            filtros,
            text="Aplicar filtros",
            command=self.refrescar,
        ).grid(
            row=0,
            column=6,
            padx=(18, 4),
            pady=4,
        )

        ttk.Button(
            filtros,
            text="Limpiar",
            command=self.limpiar_filtros,
        ).grid(
            row=0,
            column=7,
            pady=4,
        )

        # ------------------------------------------------------------------
        # Mensaje
        # ------------------------------------------------------------------

        ttk.Label(
            self,
            textvariable=self.var_mensaje,
            foreground="#5c5f66",
        ).pack(
            anchor="w",
            pady=(0, 8),
        )

        # ------------------------------------------------------------------
        # Reservaciones del día
        # ------------------------------------------------------------------

        marco_dia = ttk.LabelFrame(
            self,
            text="Reservaciones del día",
            padding=8,
        )

        marco_dia.pack(
            fill="both",
            expand=True,
            pady=(0, 8),
        )

        self.tabla_dia = self._crear_tabla(
            marco_dia,
            (
                ("id", "ID", 50),
                ("sala", "Sala", 60),
                ("fecha", "Fecha", 90),
                ("inicio", "Inicio", 65),
                ("fin", "Fin", 65),
                ("personas", "Personas", 80),
                ("estado", "Estado", 90),
            ),
        )

        # ------------------------------------------------------------------
        # Próximas reservaciones
        # ------------------------------------------------------------------

        marco_proximas = ttk.LabelFrame(
            self,
            text="Próximas reservaciones",
            padding=8,
        )

        marco_proximas.pack(
            fill="both",
            expand=True,
            pady=(0, 8),
        )

        self.tabla_proximas = self._crear_tabla(
            marco_proximas,
            (
                ("id", "ID", 50),
                ("sala", "Sala", 60),
                ("fecha", "Fecha", 90),
                ("inicio", "Inicio", 65),
                ("fin", "Fin", 65),
                ("estudiante", "Estudiante", 170),
                ("personas", "Personas", 80),
            ),
        )

        # ------------------------------------------------------------------
        # Ocupación por sala
        # ------------------------------------------------------------------

        marco_ocupacion = ttk.LabelFrame(
            self,
            text="Ocupación por sala",
            padding=8,
        )

        marco_ocupacion.pack(
            fill="both",
            expand=True,
        )

        self.tabla_ocupacion = self._crear_tabla(
            marco_ocupacion,
            (
                ("sala", "Sala", 70),
                ("capacidad", "Capacidad", 80),
                ("reservas", "Reservas activas", 110),
                ("personas", "Personas", 90),
                ("ocupacion", "Ocupación", 100),
                ("estado", "Estado sala", 120),
            ),
        )

    def _crear_tabla(self, padre, columnas):
        """
        Crea una tabla Treeview reutilizable.
        """

        identificadores = [
            columna[0]
            for columna in columnas
        ]

        tabla = ttk.Treeview(
            padre,
            columns=identificadores,
            show="headings",
            height=5,
        )

        for identificador, titulo, ancho in columnas:

            tabla.heading(
                identificador,
                text=titulo,
            )

            tabla.column(
                identificador,
                width=ancho,
                anchor=(
                    "w"
                    if identificador == "estudiante"
                    else "center"
                ),
                stretch=(
                    identificador == "estudiante"
                ),
            )

        barra = ttk.Scrollbar(
            padre,
            orient="vertical",
            command=tabla.yview,
        )

        tabla.configure(
            yscrollcommand=barra.set,
        )

        tabla.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        barra.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        padre.rowconfigure(
            0,
            weight=1,
        )

        padre.columnconfigure(
            0,
            weight=1,
        )

        return tabla

    # ----------------------------------------------------------------------
    # Aplicar filtros
    # ----------------------------------------------------------------------

    def _filas_filtradas(self, filas):
        """
        Aplica los filtros seleccionados por el usuario.

        Los filtros pueden combinarse:
        - Fecha.
        - Sala.
        - Estado.
        """

        fecha = self.var_fecha.get().strip()
        sala = self.var_sala.get().strip()
        estado = self.var_estado.get().strip().lower()

        # Validar fecha.
        if fecha:
            try:
                date.fromisoformat(fecha)
            except ValueError:
                raise ValueError(
                    "La fecha debe tener formato AAAA-MM-DD."
                )

        codigo_sala = ""

        if sala and sala != "Todas":
            codigo_sala = sala.split(
                " - ",
                1,
            )[0]

        return [
            fila
            for fila in filas
            if (
                not fecha
                or fila[5] == fecha
            )
            and (
                not codigo_sala
                or fila[3] == codigo_sala
            )
            and (
                estado == "todos"
                or fila[9] == estado
            )
        ]

    # ----------------------------------------------------------------------
    # Reservaciones del día
    # ----------------------------------------------------------------------

    def _mostrar_dia(self, filas):

        self.tabla_dia.delete(
            *self.tabla_dia.get_children()
        )

        for fila in filas:

            self.tabla_dia.insert(
                "",
                "end",
                values=(
                    fila[0],
                    fila[3],
                    fila[5],
                    fila[6],
                    fila[7],
                    fila[8],
                    fila[9].capitalize(),
                ),
            )

    # ----------------------------------------------------------------------
    # Próximas reservaciones
    # ----------------------------------------------------------------------

    def _mostrar_proximas(self, filas):

        self.tabla_proximas.delete(
            *self.tabla_proximas.get_children()
        )

        ahora = datetime.now()

        futuras = []

        for fila in filas:

            if fila[9] != "activa":
                continue

            try:
                inicio = datetime.strptime(
                    f"{fila[5]} {fila[6]}",
                    "%Y-%m-%d %H:%M",
                )
            except ValueError:
                continue

            if inicio >= ahora:
                futuras.append(
                    (
                        inicio,
                        fila,
                    )
                )

        futuras.sort(
            key=lambda elemento: elemento[0]
        )

        for _, fila in futuras[:8]:

            self.tabla_proximas.insert(
                "",
                "end",
                values=(
                    fila[0],
                    fila[3],
                    fila[5],
                    fila[6],
                    fila[7],
                    fila[2] or "",
                    fila[8],
                ),
            )

    # ----------------------------------------------------------------------
    # Ocupación por sala
    # ----------------------------------------------------------------------

    def _mostrar_ocupacion(self, filas):

        self.tabla_ocupacion.delete(
            *self.tabla_ocupacion.get_children()
        )

        fecha = self.var_fecha.get().strip()
        sala_filtro = self.var_sala.get().strip()

        codigo_filtro = ""

        if sala_filtro and sala_filtro != "Todas":
            codigo_filtro = sala_filtro.split(
                " - ",
                1,
            )[0]

        filas_activas = [
            fila
            for fila in filas
            if fila[9] == "activa"
        ]

        # La ocupación corresponde a la fecha consultada.
        if fecha:
            filas_activas = [
                fila
                for fila in filas_activas
                if fila[5] == fecha
            ]

        if codigo_filtro:
            filas_activas = [
                fila
                for fila in filas_activas
                if fila[3] == codigo_filtro
            ]

        for codigo, nombre, capacidad, estado in self.salas:

            reservas = [
                fila
                for fila in filas_activas
                if fila[3] == codigo
            ]

            cantidad_reservas = len(reservas)

            cantidad_personas = sum(
                fila[8]
                for fila in reservas
            )

            porcentaje = (
                cantidad_personas / capacidad * 100
                if capacidad
                else 0
            )

            texto_estado = (
                "Fuera de servicio"
                if estado != "disponible"
                else "Disponible"
            )

            self.tabla_ocupacion.insert(
                "",
                "end",
                values=(
                    codigo,
                    capacidad,
                    cantidad_reservas,
                    cantidad_personas,
                    f"{porcentaje:.0f}%",
                    texto_estado,
                ),
            )

    # ----------------------------------------------------------------------
    # Refrescar
    # ----------------------------------------------------------------------

    def refrescar(self):

        try:

            filas = consultar_reservaciones()

            self.salas = consultar_salas()

            # --------------------------------------------------------------
            # Actualizar lista de salas del filtro.
            # --------------------------------------------------------------

            valores_salas = (
                "Todas",
            ) + tuple(
                f"{codigo} - {nombre}"
                for codigo, nombre, _capacidad, _estado
                in self.salas
            )

            self.combo_sala["values"] = valores_salas

            if self.var_sala.get() not in valores_salas:
                self.var_sala.set("Todas")

            # --------------------------------------------------------------
            # Aplicar filtros.
            # --------------------------------------------------------------

            filtradas = self._filas_filtradas(
                filas
            )

            # --------------------------------------------------------------
            # Reservaciones de la fecha seleccionada.
            # --------------------------------------------------------------

            fecha = self.var_fecha.get().strip()

            filas_dia = [
                fila
                for fila in filtradas
                if (
                    not fecha
                    or fila[5] == fecha
                )
            ]

            self._mostrar_dia(
                filas_dia
            )

            # --------------------------------------------------------------
            # Próximas reservaciones.
            # --------------------------------------------------------------

            self._mostrar_proximas(
                filtradas
            )

            # --------------------------------------------------------------
            # Ocupación por sala.
            # --------------------------------------------------------------

            self._mostrar_ocupacion(
                filtradas
            )

            # --------------------------------------------------------------
            # Mensaje de resultados.
            # --------------------------------------------------------------

            if filas_dia:

                self.var_mensaje.set(
                    f"{len(filas_dia)} reservaciones "
                    "para los filtros seleccionados."
                )

            else:

                self.var_mensaje.set(
                    "No hay reservaciones para "
                    "los filtros seleccionados."
                )

        except ValueError as error:

            self.tabla_dia.delete(
                *self.tabla_dia.get_children()
            )

            self.tabla_proximas.delete(
                *self.tabla_proximas.get_children()
            )

            self.tabla_ocupacion.delete(
                *self.tabla_ocupacion.get_children()
            )

            self.var_mensaje.set(
                str(error)
            )

        except RuntimeError as error:

            self.var_mensaje.set(
                str(error)
            )

    # ----------------------------------------------------------------------
    # Limpiar filtros
    # ----------------------------------------------------------------------

    def limpiar_filtros(self):

        self.var_fecha.set(
            date.today().isoformat()
        )

        self.var_sala.set(
            "Todas"
        )

        self.var_estado.set(
            "Todos"
        )

        self.refrescar()


# ============================================================================
# PANEL UNIFICADO DE RESERVACIONES
# ============================================================================

class PanelReservaciones(ttk.Frame):

    def __init__(self, padre):
        super().__init__(padre)

        self.pestanas = ttk.Notebook(self)

        self.pestanas.pack(
            fill="both",
            expand=True,
        )

        # ------------------------------------------------------------------
        # RF-15. Panel principal.
        # ------------------------------------------------------------------

        self.vista_panel = VistaPanelPrincipal(
            self.pestanas
        )

        # ------------------------------------------------------------------
        # RF-06. Consulta general.
        #
        # Otras vistas pueden solicitar que se actualice después
        # de crear, modificar o cancelar una reservación.
        # ------------------------------------------------------------------

        self.vista_consultar = VistaConsultarReservaciones(
            self.pestanas
        )

        # ------------------------------------------------------------------
        # RF-05. Crear reservación.
        # ------------------------------------------------------------------

        self.vista_crear = VistaCrearReservacion(
            self.pestanas,
            on_cambio=self._actualizar_reservaciones,
        )

        # ------------------------------------------------------------------
        # RF-07. Buscar por estudiante.
        # ------------------------------------------------------------------

        self.vista_buscar = VistaBuscarPorEstudiante(
            self.pestanas
        )

        # ------------------------------------------------------------------
        # RF-08. Consultar disponibilidad.
        # ------------------------------------------------------------------

        self.vista_disponibilidad = VistaDisponibilidad(
            self.pestanas
        )

        # ------------------------------------------------------------------
        # RF-09 / RF-13. Gestionar reservaciones.
        # ------------------------------------------------------------------

        self.vista_gestionar = VistaGestionReservaciones(
            self.pestanas,
            on_cambio=self._actualizar_reservaciones,
        )

        # ------------------------------------------------------------------
        # RF-14. Crear reservaciones recurrentes.
        # ------------------------------------------------------------------

        self.vista_recurrencia = VistaReservacionRecurrente(
            self.pestanas,
            on_cambio=self._actualizar_reservaciones,
        )

        # ------------------------------------------------------------------
        # RF-16. Generar reporte.
        # ------------------------------------------------------------------

        self.vista_reportes = VistaReportes(
            self.pestanas
        )

        # ------------------------------------------------------------------
        # RF-17. Historial de auditoría.
        # ------------------------------------------------------------------

        self.vista_auditoria = VistaAuditoria(
            self.pestanas
        )

        # ------------------------------------------------------------------
        # Lista de vistas.
        # ------------------------------------------------------------------

        self.vistas = [
            self.vista_panel,
            self.vista_crear,
            self.vista_consultar,
            self.vista_buscar,
            self.vista_disponibilidad,
            self.vista_gestionar,
            self.vista_recurrencia,
            self.vista_reportes,
            self.vista_auditoria,
        ]

        # ------------------------------------------------------------------
        # Nombres de las pestañas.
        # ------------------------------------------------------------------

        nombres = [
            "Panel principal",
            "Crear",
            "Reservaciones",
            "Buscar por estudiante",
            "Disponibilidad",
            "Gestionar reservaciones",
            "Recurrentes",
            "Reportes",
            "Auditoría",
        ]

        for vista, nombre in zip(
            self.vistas,
            nombres,
        ):
            self.pestanas.add(
                vista,
                text=nombre,
            )

        self.pestanas.bind(
            "<<NotebookTabChanged>>",
            self._cambiar_pestana,
        )

    # ----------------------------------------------------------------------
    # RF-15. Actualizar información.
    # ----------------------------------------------------------------------

    def _actualizar_reservaciones(self):
        """
        Actualiza las vistas que dependen del estado de las reservaciones
        después de crear, modificar o cancelar una reservación.
        """

        # RF-06
        self.vista_consultar.refrescar()

        # RF-15
        self.vista_panel.refrescar()

    # ----------------------------------------------------------------------
    # Actualizar al cambiar de pestaña.
    # ----------------------------------------------------------------------

    def _cambiar_pestana(self, _evento=None):

        indice = self.pestanas.index(
            "current"
        )

        vista = self.vistas[indice]

        refrescar = getattr(
            vista,
            "refrescar",
            None,
        )

        if callable(refrescar):
            refrescar()

    # ----------------------------------------------------------------------
    # Cambios pendientes.
    # ----------------------------------------------------------------------

    def hay_cambios_pendientes(self):

        return (
            self.vista_crear.hay_cambios_pendientes()
            or self.vista_gestionar.hay_cambios_pendientes()
        )

    # ----------------------------------------------------------------------
    # Guardar cambios pendientes.
    # ----------------------------------------------------------------------

    def guardar_pendientes(self):

        for vista in (
            self.vista_crear,
            self.vista_gestionar,
        ):

            exito, mensaje = vista.guardar_pendientes()

            if not exito:
                return False, mensaje

        return True, ""


# ============================================================================
# VENTANA DE PRUEBA
# ============================================================================

def abrir_ventana_de_prueba():
    """
    Abre el panel completo de reservaciones
    antes de integrarlo con la ventana principal.
    """

    from database.inicializacion import (
        inicializar_base_datos,
    )

    if not inicializar_base_datos():
        return

    raiz = tk.Tk()

    raiz.title(
        "Sistema de Reservación de Salas"
    )

    raiz.geometry(
        "1100x850"
    )

    raiz.minsize(
        950,
        700,
    )

    configurar_estilos(
        raiz
    )

    panel = PanelReservaciones(
        raiz
    )

    panel.pack(
        fill="both",
        expand=True,
    )

    raiz.mainloop()


# ============================================================================
# EJECUCIÓN DIRECTA
# ============================================================================

if __name__ == "__main__":
    abrir_ventana_de_prueba()