
import sqlite3

from database.conexion import obtener_conexion


def validar_estudiante(carne, nombre, correo):

    # Comprobar que todos los datos sean texto.
    if not all(isinstance(dato, str) for dato in (carne, nombre, correo)):
        raise ValueError("Todos los campos deben ser texto.")

    # Eliminar espacios iniciales y finales.
    carne = carne.strip().upper()
    nombre = nombre.strip()
    correo = correo.strip()

    # Validar carné.
    if len(carne) != 10 or not carne.isascii() or not carne.isalnum():
        raise ValueError(
            "El carné debe contener exactamente 10 caracteres alfanuméricos."
        )

    # Validar nombre.
    if len(nombre.replace(" ", "")) < 3:
        raise ValueError(
            "El nombre debe contener al menos tres caracteres distintos de espacios."
        )

    # Validar correo electrónico.
    if correo.count("@") != 1:
        raise ValueError(
            "El correo debe contener exactamente un símbolo @."
        )

    parte_local, dominio = correo.split("@")

    if not parte_local or "." not in dominio:
        raise ValueError(
            "El correo electrónico no tiene un formato válido."
        )

    if dominio.startswith(".") or dominio.endswith("."):
        raise ValueError(
            "El dominio del correo electrónico no es válido."
        )

    return carne, nombre, correo


def registrar_estudiante(carne, nombre, correo):
 
    # Validar primero los datos.
    try:
        carne, nombre, correo = validar_estudiante(
            carne, nombre, correo
        )

    except ValueError as error:
        return False, str(error)

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion:
            conexion.execute("""
                INSERT INTO estudiantes
                    (carne, nombre_completo, correo, estado)
                VALUES (?, ?, ?, 'activo')
            """, (carne, nombre, correo))

        return True, "Estudiante registrado correctamente."

    except sqlite3.IntegrityError:
        return False, "El carné ya se encuentra registrado."

    except sqlite3.Error:
        return False, "No fue posible guardar el estudiante."

    finally:
        if conexion is not None:
            conexion.close()


def consultar_estudiantes():
   # Se devuelve una lista
    conexion = None

    try:
        conexion = obtener_conexion()

        cursor = conexion.execute("""
            SELECT carne, nombre_completo, correo, estado
            FROM estudiantes
            ORDER BY nombre_completo COLLATE NOCASE ASC
        """)

        estudiantes = cursor.fetchall()

        return estudiantes

    except sqlite3.Error as error:
        raise RuntimeError(
            "No fue posible consultar los estudiantes."
        ) from error

    finally:
        if conexion is not None:
            conexion.close()


def modificar_estudiante(carne, nombre, correo, estado):
    """
    RF-11. Modifica el nombre, correo y estado de un estudiante registrado.

    El carné se utiliza únicamente para identificar al estudiante
    y no puede modificarse.

    Devuelve:
        (True, mensaje) si la modificación se realiza correctamente.
        (False, mensaje) si los datos son inválidos o el estudiante no existe.
    """

    # Reutilizar las mismas validaciones utilizadas al registrar estudiantes.
    try:
        carne, nombre, correo = validar_estudiante(
            carne,
            nombre,
            correo,
        )
    except ValueError as error:
        return False, str(error)

    # Validar el estado.
    if not isinstance(estado, str):
        return False, "El estado del estudiante debe ser activo o inactivo."

    estado = estado.strip().lower()

    if estado not in ("activo", "inactivo"):
        return False, "El estado del estudiante debe ser activo o inactivo."

    conexion = None

    try:
        conexion = obtener_conexion()

        # Comprobar que el estudiante exista antes de modificarlo.
        estudiante = conexion.execute(
            """
            SELECT carne
            FROM estudiantes
            WHERE carne = ?
            """,
            (carne,),
        ).fetchone()

        if estudiante is None:
            return (
                False,
                f"El carné {carne} no corresponde a ningún estudiante registrado.",
            )

        with conexion:
            conexion.execute(
                """
                UPDATE estudiantes
                SET nombre_completo = ?,
                    correo = ?,
                    estado = ?
                WHERE carne = ?
                """,
                (
                    nombre,
                    correo,
                    estado,
                    estudiante[0],
                ),
            )

        return True, "La información del estudiante se modificó correctamente."

    except sqlite3.Error:
        return False, "No fue posible modificar la información del estudiante."

    finally:
        if conexion is not None:
            conexion.close()