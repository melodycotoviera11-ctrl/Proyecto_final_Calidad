# Proyecto_final_Calidad
En este repositorio se presenta todo el código fuente del proyecto final "Sistema de reservación de salas de estudio" 

## Requisitos

- Python 3.10 o superior (probado en 3.12). Solo se usa la biblioteca estándar (`sqlite3`, `tkinter`, `unittest`), por lo que no hay dependencias externas que instalar.
- En Linux puede ser necesario instalar Tkinter aparte (por ejemplo, `sudo apt install python3-tk`).

## Pruebas automatizadas

Desde la raíz del repositorio:

```bash
python -m unittest discover -s tests -t .
```

Las pruebas crean una base de datos temporal con la inicialización oficial, por lo que nunca modifican `database/reservaciones.db`.

## Módulo de reservaciones (RF-05 a RF-08)

| Archivo | Responsabilidad |
|---|---|
| `reservaciones/validaciones.py` | Validaciones sin base de datos: fecha, hora, duración, cantidad, horario permitido y superposición (RN-02 a RN-07, RN-09, RN-10). |
| `reservaciones/reglas.py` | Reglas que consultan la base de datos: estudiante activo, sala disponible, capacidad, conflictos y límite de tres reservaciones (RN-01, RN-07 a RN-11). Reutilizable para modificar (RF-13) y recurrencia (RF-14). |
| `reservaciones/gestion_reservaciones.py` | RF-05 crear, RF-06 consultar y RF-07 buscar por estudiante. Registra la creación en `auditoria` dentro de la misma transacción. |
| `reservaciones/disponibilidad.py` | RF-08 consultar disponibilidad (solo lectura). |
| `interfaz/vistas_reservaciones.py` | Vistas Tkinter de RF-05 a RF-08. No ejecutan SQL. |

Para probar las vistas antes de integrarlas a la ventana principal:

```bash
python -m interfaz.vistas_reservaciones
```
