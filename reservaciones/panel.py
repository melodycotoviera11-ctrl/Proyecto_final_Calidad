"""
RF-15. Lógica del panel principal, sin dependencias de Tkinter.

Corrección del hallazgo H-01 (Fase 3, Grupo 07): las "Próximas
reservaciones" se calculaban sobre las filas ya filtradas por la fecha
del panel. Como la fecha por defecto es hoy, las reservaciones de los
días siguientes nunca aparecían. Ahora las próximas se calculan con
todas las reservaciones activas que inician desde el momento actual,
aplicando solo los filtros de sala y estado.

La lógica se separó de la vista para poder probarla sin automatizar
clics sobre la interfaz (RNF-10), tal como recomienda H-01 y H-07.

Cada fila tiene el formato de consultar_reservaciones():
    (id, carne, estudiante, codigo_sala, sala, fecha,
     hora_inicio, hora_fin, cantidad_personas, estado)
"""

from datetime import date, datetime

LIMITE_PROXIMAS = 8

SALA_TODAS = "Todas"
ESTADO_TODOS = "todos"
ESTADOS_VALIDOS = (ESTADO_TODOS, "activa", "cancelada")

MENSAJE_SIN_RESULTADOS = "No hay reservaciones para los filtros seleccionados."


def interpretar_filtros(fecha="", sala="", estado=""):
    """
    Normaliza los filtros tal como llegan de la interfaz.

    - fecha: "" (todas) o AAAA-MM-DD.
    - sala: "Todas", "" o "S01 - Nombre" / "S01".
    - estado: "Todos", "activa" o "cancelada" (sin distinguir mayúsculas).

    Devuelve (fecha, codigo_sala, estado). Lanza ValueError si la fecha
    o el estado no son válidos.
    """
    fecha = (fecha or "").strip()
    sala = (sala or "").strip()
    estado = (estado or "").strip().lower() or ESTADO_TODOS

    if fecha:
        try:
            date.fromisoformat(fecha)
        except ValueError:
            raise ValueError("La fecha debe tener formato AAAA-MM-DD.") from None

    codigo_sala = ""
    if sala and sala != SALA_TODAS:
        codigo_sala = sala.split(" - ", 1)[0].strip().upper()

    if estado not in ESTADOS_VALIDOS:
        raise ValueError("El estado debe ser Todos, activa o cancelada.")

    return fecha, codigo_sala, estado


def _cumple_sala_estado(fila, codigo_sala, estado):
    return (
        (not codigo_sala or str(fila[3]).upper() == codigo_sala)
        and (estado == ESTADO_TODOS or fila[9] == estado)
    )


def filtrar_reservaciones(filas, fecha="", codigo_sala="", estado=ESTADO_TODOS):
    """Aplica los filtros combinados (fecha, sala y estado) con AND."""
    return [
        fila
        for fila in filas
        if (not fecha or fila[5] == fecha)
        and _cumple_sala_estado(fila, codigo_sala, estado)
    ]


def obtener_proximas(filas, ahora, codigo_sala="", estado=ESTADO_TODOS,
                     limite=LIMITE_PROXIMAS):
    """
    Próximas reservaciones: activas que inician en `ahora` o después,
    ordenadas por fecha y hora. No dependen del filtro de fecha (H-01);
    sí respetan los filtros de sala y estado.
    """
    futuras = []

    for fila in filas:
        if fila[9] != "activa" or not _cumple_sala_estado(fila, codigo_sala, estado):
            continue

        try:
            inicio = datetime.strptime(f"{fila[5]} {fila[6]}", "%Y-%m-%d %H:%M")
        except ValueError:
            continue

        if inicio >= ahora:
            futuras.append((inicio, fila))

    futuras.sort(key=lambda elemento: elemento[0])
    return [fila for _, fila in futuras[:limite]]


def calcular_ocupacion(filas_filtradas, salas):
    """
    Ocupación por sala con las reservaciones activas ya filtradas.

    Devuelve una tupla por sala:
        (codigo, capacidad, reservas_activas, personas, "NN%", estado)
    """
    activas = [fila for fila in filas_filtradas if fila[9] == "activa"]
    resultado = []

    for codigo, _nombre, capacidad, estado in salas:
        reservas = [fila for fila in activas if fila[3] == codigo]
        personas = sum(fila[8] for fila in reservas)
        porcentaje = personas / capacidad * 100 if capacidad else 0

        resultado.append(
            (
                codigo,
                capacidad,
                len(reservas),
                personas,
                f"{porcentaje:.0f}%",
                "Disponible" if estado == "disponible" else "Fuera de servicio",
            )
        )

    return resultado


def mensaje_panel(cantidad_dia, cantidad_proximas):
    """Mensaje de resultados que se muestra bajo los filtros."""
    if cantidad_dia:
        return f"{cantidad_dia} reservaciones para los filtros seleccionados."

    if cantidad_proximas:
        return (
            f"{MENSAJE_SIN_RESULTADOS} Hay {cantidad_proximas} "
            "próximas reservaciones en la tabla inferior."
        )

    return MENSAJE_SIN_RESULTADOS


def datos_panel(filas, salas, fecha="", sala="", estado="", ahora=None):
    """
    Calcula todo lo que muestra el panel principal.

    Devuelve un diccionario con:
        dia        filas que cumplen los tres filtros;
        proximas   activas desde `ahora`, con filtros de sala y estado;
        ocupacion  tuplas de calcular_ocupacion();
        mensaje    texto informativo.

    Lanza ValueError si los filtros no son válidos.
    """
    if ahora is None:
        ahora = datetime.now()

    fecha, codigo_sala, estado = interpretar_filtros(fecha, sala, estado)

    dia = filtrar_reservaciones(filas, fecha, codigo_sala, estado)
    proximas = obtener_proximas(filas, ahora, codigo_sala, estado)

    return {
        "dia": dia,
        "proximas": proximas,
        "ocupacion": calcular_ocupacion(dia, salas),
        "mensaje": mensaje_panel(len(dia), len(proximas)),
    }
