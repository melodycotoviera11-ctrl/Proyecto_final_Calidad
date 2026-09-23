
from database.inicializacion import inicializar_base_datos


def main():

    resultado = inicializar_base_datos()

    if resultado:
        print("Base de datos inicializada correctamente.")
    else:
        print("No fue posible inicializar la base de datos.")


if __name__ == "__main__":
    main()