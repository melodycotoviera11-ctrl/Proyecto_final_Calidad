"""
Validaciones puras de reservaciones (sin base de datos ni interfaz).

Cada función recibe los datos por parámetro, devuelve el valor normalizado
y lanza ValueError con un mensaje que identifica el dato inválido.
De esta forma pueden probarse de manera automatizada (RNF-10) y
reutilizarse en RF-05, RF-08, RF-13 y RF-14.

Reglas cubiertas: RN-02, RN-03, RN-04, RN-05, RN-06, RN-07 (formato) y
RN-09 / RN-10 (cálculo de superposición).
"""

import re
from datetime import date, datetime

HORA_APERTURA = 8
HORA_CIERRE = 20
DURACIONES_PERMITIDAS = (1, 2)

_PATRON_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PATRON_HORA = re.compile(r"^(\d{1,2}):(\d{2})$")
_PATRON_ENTERO = re.compile(r"^\d+$")


def _texto_obligatorio(valor, etiqueta):
    """Comprueba que el valor sea texto no vacío y lo devuelve sin espacios."""
    if valor is None:
        raise ValueError(f"El campo {etiqueta} es obligatorio.")

    if not isinstance(valor, str):
        valor = str(valor)

    valor = valor.strip()

    if not valor:
        raise ValueError(f"El campo {etiqueta} es obligatorio.")

    return valor


def _entero(valor, etiqueta, mensaje_invalido):
    """
    Convierte a entero un int o un texto formado solo por dígitos.
    Rechaza booleanos, decimales y textos como '2.5' o 'dos'.
    """
    if isinstance(valor, bool):
        raise ValueError(mensaje_invalido)

    if isinstance(valor, int):
        return valor

    texto = _texto_obligatorio(valor, etiqueta)

    if not _PATRON_ENTERO.match(texto):
        raise ValueError(mensaje_invalido)

    return int(texto)


def normalizar_carne(carne):
    """El carné se compara sin distinguir mayúsculas (RF-07)."""
    return _texto_obligatorio(carne, "carné").upper()


def normalizar_codigo_sala(codigo_sala):
    return _texto_obligatorio(codigo_sala, "sala").upper()


def validar_fecha(fecha):
    """RN-02 (formato): AAAA-MM-DD y fecha existente en el calendario."""
    texto = _texto_obligatorio(fecha, "fecha")

    if not _PATRON_FECHA.match(texto):
        raise ValueError(
            "La fecha debe tener el formato AAAA-MM-DD (por ejemplo, 2026-10-15)."
        )

    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(
            f"La fecha {texto} no existe en el calendario."
        ) from None


def validar_hora_inicio(hora_inicio):
    """
    RN-04: formato de 24 horas y comienzo exacto en una hora completa.
    Acepta '8:00' o '08:00' y devuelve la hora como entero (8).
    """
    texto = _texto_obligatorio(hora_inicio, "hora de inicio")
    coincidencia = _PATRON_HORA.match(texto)

    if not coincidencia:
        raise ValueError(
            "La hora de inicio debe tener el formato de 24 horas HH:MM (por ejemplo, 14:00)."
        )

    hora = int(coincidencia.group(1))
    minutos = int(coincidencia.group(2))

    if hora > 23 or minutos > 59:
        raise ValueError(
            "La hora de inicio no es una hora válida en formato de 24 horas."
        )

    if minutos != 0:
        raise ValueError(
            "La hora de inicio debe comenzar en una hora completa (minutos en 00)."
        )

    return hora


def validar_duracion(duracion):
    """RN-06: la duración permitida es de una o dos horas."""
    mensaje = "La duración debe ser de 1 o 2 horas."
    valor = _entero(duracion, "duración", mensaje)

    if valor not in DURACIONES_PERMITIDAS:
        raise ValueError(mensaje)

    return valor


def validar_cantidad_personas(cantidad):
    """RN-07 (formato): número entero mayor que cero."""
    mensaje = "La cantidad de personas debe ser un número entero mayor que cero."
    valor = _entero(cantidad, "cantidad de personas", mensaje)

    if valor <= 0:
        raise ValueError(mensaje)

    return valor


def validar_capacidad(cantidad, capacidad, codigo_sala):
    """RN-07 (capacidad): la cantidad no puede superar la capacidad de la sala."""
    if cantidad > capacidad:
        raise ValueError(
            f"La cantidad de personas ({cantidad}) supera la capacidad "
            f"de la sala {codigo_sala} ({capacidad})."
        )


def validar_horario_permitido(hora_inicio, duracion):
    """RN-05: horario de 08:00 a 20:00 sin finalizar después de las 20:00."""
    hora_fin = hora_inicio + duracion

    if hora_inicio < HORA_APERTURA or hora_fin > HORA_CIERRE:
        raise ValueError(
            "El horario permitido es de 08:00 a 20:00; la reservación "
            f"solicitada ({formatear_hora(hora_inicio)} a "
            f"{formatear_hora(hora_fin)}) queda fuera de ese rango."
        )


def validar_momento_futuro(fecha, hora_inicio, ahora):
    """
    RN-02: la fecha no puede ser anterior a la fecha del sistema.
    RN-03: si la reservación es para hoy, debe iniciar después de la hora actual.
    """
    if fecha < ahora.date():
        raise ValueError(
            "La fecha no puede ser anterior a la fecha actual "
            f"({ahora.date().isoformat()})."
        )

    if fecha == ahora.date():
        inicio = datetime.combine(fecha, datetime.min.time()).replace(hour=hora_inicio)

        if inicio <= ahora:
            raise ValueError(
                "Para una reservación de hoy, la hora de inicio debe ser "
                f"posterior a la hora actual ({ahora.strftime('%H:%M')})."
            )


def hay_superposicion(inicio_a, duracion_a, inicio_b, duracion_b):
    """
    RN-09 / RN-10: dos intervalos [inicio, fin) se superponen si cada uno
    empieza antes de que termine el otro. Si uno inicia exactamente al
    finalizar el otro, NO hay superposición.
    """
    return inicio_a < inicio_b + duracion_b and inicio_b < inicio_a + duracion_a


def formatear_hora(hora):
    return f"{hora:02d}:00"


def validar_datos_de_horario(codigo_sala, fecha, hora_inicio, duracion, ahora):
    """
    Validaciones sin base de datos comunes a RF-05 y RF-08:
    sala (obligatoria), fecha, hora, duración, RN-02, RN-03 y RN-05.
    Devuelve un diccionario con los datos normalizados.
    """
    datos = {
        "codigo_sala": normalizar_codigo_sala(codigo_sala),
        "fecha": validar_fecha(fecha),
        "hora_inicio": validar_hora_inicio(hora_inicio),
        "duracion": validar_duracion(duracion),
    }

    validar_momento_futuro(datos["fecha"], datos["hora_inicio"], ahora)
    validar_horario_permitido(datos["hora_inicio"], datos["duracion"])

    return datos


def validar_datos_basicos(carne, codigo_sala, fecha, hora_inicio, duracion,
                          cantidad_personas, ahora):
    """
    Todas las validaciones de una reservación que no requieren la base de
    datos (RF-05, RF-13, RF-14). Todos los campos son obligatorios.
    """
    carne = normalizar_carne(carne)
    datos = validar_datos_de_horario(codigo_sala, fecha, hora_inicio, duracion, ahora)
    datos["carne"] = carne
    datos["cantidad_personas"] = validar_cantidad_personas(cantidad_personas)
    return datos


def fecha_a_texto(fecha):
    return fecha.isoformat() if isinstance(fecha, date) else str(fecha)
