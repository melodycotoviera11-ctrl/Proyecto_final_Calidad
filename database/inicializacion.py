
from database.conexion import obtener_conexion


def crear_tablas(conexion):
  
    cursor = conexion.cursor()

    # Tabla de estudiantes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            carne TEXT PRIMARY KEY COLLATE NOCASE,
            nombre_completo TEXT NOT NULL,
            correo TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'activo'
                CHECK (estado IN ('activo', 'inactivo'))
        )
    """)

    # Tabla de salas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salas (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            capacidad INTEGER NOT NULL CHECK (capacidad > 0),
            estado TEXT NOT NULL DEFAULT 'disponible'
                CHECK (estado IN ('disponible', 'fuera_de_servicio'))
        )
    """)

    # Tabla de reservaciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            carne TEXT NOT NULL,
            codigo_sala TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora_inicio TEXT NOT NULL,
            duracion INTEGER NOT NULL CHECK (duracion IN (1, 2)),
            cantidad_personas INTEGER NOT NULL
                CHECK (cantidad_personas > 0),
            estado TEXT NOT NULL DEFAULT 'activa'
                CHECK (estado IN ('activa', 'cancelada')),
            serie_id TEXT,

            FOREIGN KEY (carne) REFERENCES estudiantes(carne),
            FOREIGN KEY (codigo_sala) REFERENCES salas(codigo)
        )
    """)

    # Tabla de auditoría
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            tipo_accion TEXT NOT NULL,
            entidad TEXT NOT NULL,
            identificador TEXT NOT NULL
        )
    """)


def cargar_datos_iniciales(conexion):
    """
    Registra los estudiantes y salas iniciales.
    No duplica registros existentes.
    """

    estudiantes = [
        (
            "A001234567",
            "Andrea Solano",
            "andrea@universidad.ac.cr",
            "activo"
        ),
        (
            "B009876543",
            "Carlos Méndez",
            "carlos@universidad.ac.cr",
            "activo"
        ),
        (
            "C004567890",
            "Daniela Rojas",
            "daniela@universidad.ac.cr",
            "inactivo"
        )
    ]

    salas = [
        ("S01", "Sala Biblioteca 1", 4, "disponible"),
        ("S02", "Sala Biblioteca 2", 6, "disponible"),
        ("S03", "Laboratorio de estudio", 10, "disponible"),
        ("S04", "Sala multimedia", 8, "fuera_de_servicio"),
        ("S05", "Cubículo individual", 1, "disponible")
    ]

    conexion.executemany("""
        INSERT OR IGNORE INTO estudiantes
        (carne, nombre_completo, correo, estado)
        VALUES (?, ?, ?, ?)
    """, estudiantes)

    conexion.executemany("""
        INSERT OR IGNORE INTO salas
        (codigo, nombre, capacidad, estado)
        VALUES (?, ?, ?, ?)
    """, salas)


def verificar_integridad(conexion):
   
    resultado = conexion.execute(
        "PRAGMA integrity_check"
    ).fetchone()

    if resultado is None or resultado[0] != "ok":
        raise RuntimeError(
            "La base de datos presenta errores de integridad."
        )


def verificar_estructura(conexion):
  
    estructura_esperada = {
        "estudiantes": {
            "carne",
            "nombre_completo",
            "correo",
            "estado"
        },

        "salas": {
            "codigo",
            "nombre",
            "capacidad",
            "estado"
        },

        "reservaciones": {
            "id",
            "carne",
            "codigo_sala",
            "fecha",
            "hora_inicio",
            "duracion",
            "cantidad_personas",
            "estado",
            "serie_id"
        },

        "auditoria": {
            "id",
            "fecha_hora",
            "tipo_accion",
            "entidad",
            "identificador"
        }
    }

    for tabla, campos_esperados in estructura_esperada.items():

        columnas = conexion.execute(
            f"PRAGMA table_info({tabla})"
        ).fetchall()

        campos_actuales = {
            columna[1] for columna in columnas
        }

        if not campos_esperados.issubset(campos_actuales):
            raise RuntimeError(
                f"La estructura de la tabla {tabla} está incompleta."
            )


def inicializar_base_datos():
    """
    Abre la base de datos, comprueba su integridad,
    crea las tablas y carga los datos iniciales.
    """

    conexion = None

    try:
        conexion = obtener_conexion()

        # Comprobar la integridad del archivo SQLite.
        verificar_integridad(conexion)

        with conexion:
            crear_tablas(conexion)
            verificar_estructura(conexion)
            cargar_datos_iniciales(conexion)

        return True

    except Exception:
        return False

    finally:
        if conexion is not None:
            conexion.close()