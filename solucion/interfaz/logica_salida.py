"""
RF-10. Lógica de la salida controlada, separada de Tkinter.

Corrección del hallazgo H-05 (Fase 3, Grupo 07):
- Antes, al salir solo existían "Sí" (guardar) y "No" (quedarse), por lo
  que un formulario incompleto impedía cerrar la aplicación.
- Ahora la persona usuaria elige entre tres opciones:
  Guardar y salir, Salir sin guardar o Cancelar.
- Si al guardar alguna vista rechaza los datos, se informa el motivo y se
  vuelve a ofrecer Salir sin guardar o Cancelar.

Definición de "cambios pendientes" adoptada en la especificación refinada:
datos escritos en un formulario de registro o modificación que todavía no
se han guardado en la base de datos. Estos datos son un borrador: si la
persona usuaria elige salir sin guardar, se descartan.

Este módulo no importa tkinter, por lo que puede probarse sin abrir la
interfaz gráfica (RNF-10).
"""

GUARDAR_Y_SALIR = "guardar_y_salir"
SALIR_SIN_GUARDAR = "salir_sin_guardar"
CANCELAR = "cancelar"

OPCIONES_SALIDA = (
    GUARDAR_Y_SALIR,
    SALIR_SIN_GUARDAR,
    CANCELAR,
)

OPCIONES_TRAS_ERROR = (
    SALIR_SIN_GUARDAR,
    CANCELAR,
)


def vistas_con_cambios(vistas):
    """Devuelve las vistas que informan cambios pendientes."""

    resultado = []

    for vista in vistas:

        verificar = getattr(
            vista,
            "hay_cambios_pendientes",
            None,
        )

        if callable(verificar) and verificar():
            resultado.append(vista)

    return resultado


def guardar_vistas(vistas):
    """
    Guarda los cambios pendientes de cada vista.

    Se detiene en la primera vista que no pueda guardar.

    Devuelve:
        (True, "") si todas las vistas guardaron.
        (False, mensaje) con el motivo de la primera falla.
    """

    for vista in vistas:

        guardar = getattr(
            vista,
            "guardar_pendientes",
            None,
        )

        if not callable(guardar):
            continue

        exito, mensaje = guardar()

        if not exito:
            return False, mensaje

    return True, ""


def resolver_salida(
    vistas,
    preguntar_opcion,
    preguntar_tras_error,
):
    """
    Decide si la aplicación debe cerrarse.

    Parámetros:
        vistas: vistas editables de la aplicación.
        preguntar_opcion: función sin argumentos que muestra las tres
            opciones y devuelve GUARDAR_Y_SALIR, SALIR_SIN_GUARDAR o
            CANCELAR.
        preguntar_tras_error: función que recibe el mensaje de error y
            devuelve SALIR_SIN_GUARDAR o CANCELAR.

    Devuelve:
        True si la aplicación debe cerrarse.
        False si debe permanecer abierta sin perder la información.
    """

    pendientes = vistas_con_cambios(vistas)

    # Sin cambios pendientes se cierra sin pedir confirmación.
    if not pendientes:
        return True

    opcion = preguntar_opcion()

    if opcion == SALIR_SIN_GUARDAR:
        return True

    if opcion != GUARDAR_Y_SALIR:
        # Cancelar, cerrar el cuadro o cualquier valor no previsto
        # mantienen la aplicación abierta.
        return False

    exito, mensaje = guardar_vistas(pendientes)

    if exito:
        return True

    opcion_error = preguntar_tras_error(mensaje)

    return opcion_error == SALIR_SIN_GUARDAR
