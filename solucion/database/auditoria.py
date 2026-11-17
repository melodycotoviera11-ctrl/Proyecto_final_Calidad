"""
RF-17. Registro de auditoría compartido por todos los módulos.

Corrección del hallazgo H-02 (Fase 3, Grupo 07): la auditoría solo se
registraba en las operaciones de reservaciones. Esta función vive en la
capa de datos para que estudiantes, salas y reservaciones la usen sin
crear dependencias circulares entre módulos.

La inserción se hace con la MISMA conexión de la operación auditada,
por lo que se confirma o se revierte junto con ella: un cambio que
falla no deja un registro de auditoría "exitoso".
"""

from datetime import datetime

ENTIDAD_ESTUDIANTE = "estudiante"
ENTIDAD_SALA = "sala"
ENTIDAD_RESERVACION = "reservación"

ACCION_CREACION = "creación"
ACCION_MODIFICACION = "modificación"
ACCION_CANCELACION = "cancelación"


def registrar_auditoria(conexion, tipo_accion, entidad, identificador):
    """
    Inserta un registro en la tabla auditoria con fecha y hora,
    tipo de acción, entidad e identificador afectado.

    No confirma la transacción: eso le corresponde a quien llama.
    """
    conexion.execute(
        """
        INSERT INTO auditoria
            (fecha_hora, tipo_accion, entidad, identificador)
        VALUES (?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tipo_accion,
            entidad,
            str(identificador),
        ),
    )
