
from database.conexion import obtener_conexion


def main():
    conexion = None

    try:
        conexion = obtener_conexion()

        print("Conexión con la base de datos establecida correctamente.")

    except Exception:
        print("No fue posible abrir la base de datos.")

    finally:
        if conexion is not None:
            conexion.close()


if __name__ == "__main__":
    main()