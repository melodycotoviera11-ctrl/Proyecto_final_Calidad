from tkinter import messagebox

from database.inicializacion import inicializar_base_datos
from interfaz.ventana_principal import iniciar_interfaz


def main():

    if not inicializar_base_datos():
        messagebox.showerror(
            "Error",
            "No fue posible inicializar la base de datos.",
        )
        return

    iniciar_interfaz()


if __name__ == "__main__":
    main()