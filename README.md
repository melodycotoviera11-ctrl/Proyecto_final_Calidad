# Sistema de Reservación de Salas de Estudio

Proyecto final del curso **TI-3603 Calidad en Sistemas de Información**.

La aplicación permite administrar estudiantes, salas y reservaciones de salas de estudio mediante una interfaz gráfica de escritorio desarrollada en Python y persistencia local con SQLite.

---

## Requerimientos de ejecución

- Python 3.10 o superior.
- Tkinter.
- SQLite mediante el módulo estándar `sqlite3`.

El proyecto utiliza únicamente bibliotecas incluidas en Python, por lo que no requiere instalar dependencias externas mediante `pip`.

En algunas distribuciones de Linux puede ser necesario instalar Tkinter por separado.

---

## Ejecución de la aplicación

Desde la raíz del proyecto ejecutar:

python main.py

Al iniciar, el sistema abre la base de datos ubicada en:
database/reservaciones.db

Si la base de datos no existe, el sistema la crea automáticamente junto con su estructura y los datos iniciales.

## Datos iniciales
Estudiantes
- A001234567 - Andrea Solano - activo
- B009876543 - Carlos Méndez - activo
- C004567890 - Daniela Rojas - inactivo
Salas
- S01 - Sala Biblioteca 1 - capacidad 4 - disponible
- S02 - Sala Biblioteca 2 - capacidad 6 - disponible
- S03 - Laboratorio de estudio - capacidad 10 - disponible
- S04 - Sala multimedia - capacidad 8 - fuera de servicio
- S05 - Cubículo individual - capacidad 1 - disponible

## Funcionalidades principales
La aplicación incluye:
- Panel principal con reservaciones del día, próximas reservaciones y ocupación de salas.
- Registro, consulta y modificación de estudiantes.
- Registro, consulta y modificación de salas.
- Creación de reservaciones.
- Consulta del historial de reservaciones.
- Búsqueda de reservaciones por estudiante.
- Consulta de disponibilidad.
- Modificación y cancelación de reservaciones.
- Creación de reservaciones recurrentes.
- Cancelación individual y de ocurrencias futuras de una serie.
- Generación de reportes en formato CSV.
- Consulta del historial de auditoría.
- Salida controlada con verificación de cambios pendientes.
Los identificadores de reservación utilizan el formato:
R0001
R0002
R0003
...
Los identificadores se generan automáticamente y no se reutilizan.

## Navegación
La aplicación utiliza un único menú lateral.
Las opciones disponibles son:

Panel principal

Gestión
- Estudiantes
- Salas

Reservaciones
- Crear reservación
- Consultar reservaciones
- Buscar por estudiante
- Consultar disponibilidad
- Modificar / cancelar
- Reservaciones recurrentes

Otros
- Reportes
- Historial de auditoría

Salir
El botón Salir y el cierre mediante la X de la ventana utilizan el mismo procedimiento de salida controlada.
Si existen cambios pendientes, el sistema solicita confirmación e intenta guardarlos antes de cerrar.

## Estructura del proyecto
Proyecto_final_Calidad/
│
├── database/
│   ├── conexion.py
│   ├── inicializacion.py
│   └── reservaciones.db
│
├── estudiantes/
│   └── gestion_estudiantes.py
│
├── salas/
│   └── gestion_salas.py
│
├── reservaciones/
│   ├── disponibilidad.py
│   ├── gestion_recurrencia.py
│   ├── gestion_reservaciones.py
│   ├── reglas.py
│   ├── reportes.py
│   └── validaciones.py
│
├── interfaz/
│   ├── ventana_principal.py
│   ├── vistas_auditoria.py
│   ├── vistas_estudiantes.py
│   ├── vistas_gestion_reservas.py
│   ├── vistas_panel_reservaciones.py
│   ├── vistas_recurrencia.py
│   ├── vistas_reportes.py
│   ├── vistas_reservaciones.py
│   └── vistas_salas.py
│
├── tests/
│   └── pruebas automatizadas del sistema
│
├── main.py
└── README.md

La aplicación mantiene separadas las responsabilidades de interfaz, lógica de negocio, validaciones y persistencia.
Los módulos de interfaz no ejecutan sentencias SQL directamente.

## Persistencia
La información se almacena localmente mediante SQLite.
Las principales entidades almacenadas son:
- estudiantes;
- salas;
- reservaciones;
- auditoría.
Las operaciones de escritura utilizan transacciones para evitar información parcial cuando una validación u operación falla.

## Restaurar los datos iniciales
Para restaurar la aplicación a su estado inicial:
1. Cerrar completamente la aplicación.
2. Eliminar el archivo:
database/reservaciones.db

3. Ejecutar nuevamente:
python main.py
El sistema crea automáticamente una nueva base de datos con los estudiantes y salas iniciales.

## Reportes
Los reportes de reservaciones pueden generarse desde la opción Reportes.
La persona usuaria selecciona:
- fecha inicial;
- fecha final;
- ubicación del archivo.
El reporte se genera en formato CSV con codificación UTF-8.

## Pruebas automatizadas
Las pruebas se ejecutan desde la raíz del proyecto con:
python -m unittest discover -s tests -t . -v

Las pruebas utilizan bases de datos temporales independientes, por lo que no modifican:
database/reservaciones.db

La suite incluye pruebas sobre:
- validaciones;
- estudiantes;
- salas;
- creación de reservaciones;
- disponibilidad;
- consultas;
- cancelación;
- modificación;
- reservaciones recurrentes;
- reportes;
- auditoría;
- persistencia;
- integridad;
- arquitectura;
- rendimiento.

## Consideraciones de portabilidad
El proyecto utiliza rutas relativas, por lo que puede ejecutarse desde otra computadora sin modificar rutas del código fuente.
Para ejecutar la aplicación en otro equipo:
1. Copiar o clonar el repositorio.
2. Verificar que Python 3.10 o superior esté instalado.
3. Abrir una terminal en la raíz del proyecto.
4. Ejecutar:
python main.py

No se requieren credenciales ni configuraciones personales para iniciar la aplicación.