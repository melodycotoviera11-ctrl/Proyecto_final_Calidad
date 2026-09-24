# Fase 2 — Entrega de P2 (RF-05 a RF-08)

## 1. Qué se implementó

| Requerimiento | Función de lógica | Vista |
|---|---|---|
| RF-05 Crear reservación | `gestion_reservaciones.crear_reservacion()` | `VistaCrearReservacion` |
| RF-06 Consultar reservaciones | `gestion_reservaciones.consultar_reservaciones()` | `VistaConsultarReservaciones` |
| RF-07 Buscar por estudiante | `gestion_reservaciones.buscar_por_estudiante()` | `VistaBuscarPorEstudiante` |
| RF-08 Consultar disponibilidad | `disponibilidad.consultar_disponibilidad()` | `VistaDisponibilidad` |

Convenciones (alineadas con el código de P1):

- Las validaciones lanzan `ValueError` con un mensaje que nombra el dato inválido.
- Las operaciones devuelven una tupla `(exito, mensaje, dato)`; `dato` es el ID creado, la lista de filas o el booleano de disponibilidad.
- `consultar_reservaciones()` sigue el patrón de `consultar_estudiantes()`: devuelve una lista o lanza `RuntimeError`.
- Las filas de reservaciones siguen el orden de `COLUMNAS_RESERVACION`.
- Las funciones con reglas de tiempo aceptan `ahora=` para fijar la fecha y hora en pruebas.

## 2. Reglas de negocio cubiertas

| Regla | Dónde se aplica | Pruebas |
|---|---|---|
| RN-01 Estudiante registrado y activo | `reglas.obtener_estudiante_activo` | `test_estudiante_inexistente`, `test_estudiante_inactivo` |
| RN-02 Fecha AAAA-MM-DD, no anterior | `validaciones.validar_fecha`, `validar_momento_futuro` | `TestFecha`, `test_fecha_pasada` |
| RN-03 Hoy, después de la hora actual | `validaciones.validar_momento_futuro` | `TestMomentoFuturo`, `test_hoy_hora_pasada` |
| RN-04 24 horas, hora completa | `validaciones.validar_hora_inicio` | `TestHora`, `test_hora_no_completa` |
| RN-05 08:00 a 20:00 | `validaciones.validar_horario_permitido` | `TestHorarioPermitido`, `test_fuera_de_horario` |
| RN-06 Duración 1 o 2 horas | `validaciones.validar_duracion` | `TestDuracionYCantidad`, `test_duracion_invalida` |
| RN-07 Cantidad entera, > 0, ≤ capacidad | `validar_cantidad_personas`, `validar_capacidad` | `test_capacidad_superada`, `test_capacidad_exacta_permitida` |
| RN-08 Sala fuera de servicio | `reglas.obtener_sala_disponible` | `test_sala_fuera_de_servicio` (crear y disponibilidad) |
| RN-09 Sin superposición | `reglas.buscar_conflictos` | `test_superposicion_rechazada`, `test_conflicto_no_disponible` |
| RN-10 Consecutivas válidas | `validaciones.hay_superposicion` | `test_consecutivas_permitidas`, `test_consecutiva_disponible` |
| RN-11 Máximo tres vigentes | `reglas.contar_reservaciones_vigentes` | `test_maximo_tres_vigentes`, `test_reservacion_en_curso_cuenta_para_el_limite` |
| RN-12 Canceladas no bloquean | filtro `estado = 'activa'` | `test_cancelada_no_bloquea_horario`, `test_cancelada_no_bloquea` |
| RN-13 IDs no reutilizados | `AUTOINCREMENT` del esquema de P1 | `test_ids_unicos_y_no_reutilizados` |

Decisiones de interpretación que conviene validar con el equipo:

- **RN-03**: una reservación de hoy debe iniciar estrictamente después de la hora actual; a las 10:00 exactas ya no se puede reservar a las 10:00.
- **RN-11**: "presente" incluye una reservación en curso (hoy a las 09:30, una de 09:00 a 11:00 todavía cuenta).
- **RN-04**: se acepta `8:00` y se guarda normalizada como `08:00`.
- **RF-08**: una sala fuera de servicio se informa como "no disponible" (no como error de datos).

## 3. Requerimientos no funcionales atendidos en este bloque

- **RNF-03**: sin rutas absolutas; la BD se abre con la ruta relativa de P1. Hay una prueba que lo verifica.
- **RNF-04**: mismas etiquetas en todas las vistas; cada vista tiene "Volver al panel", que descarta la operación en curso.
- **RNF-05**: batería de 22 entradas inválidas sin cierres ni cambios en la BD; las vistas atrapan cualquier error inesperado.
- **RNF-06**: crear reservación usa `BEGIN IMMEDIATE`, con `commit` o `rollback` explícito; la auditoría entra en la misma transacción.
- **RNF-07**: la interfaz no ejecuta SQL (prueba automática que revisa la carpeta `interfaz/`).
- **RNF-08**: prueba con nombres que tienen tildes y ñ.
- **RNF-09**: prueba con 1 000 estudiantes y 5 000 reservaciones; cada consulta de P2 queda muy por debajo de 2 s.
- **RNF-10**: 73 pruebas con `unittest` sobre una BD temporal, ejecutables con un solo comando.

## 4. Puntos de integración con el resto del equipo

**P3 — RF-09 y RF-13**

- RF-13 puede reutilizar toda la validación:
  `reglas.validar_reservacion(conexion, ..., excluir_id=id_original)`.
  `excluir_id` evita que la reservación choque consigo misma en superposición y en el límite de tres.
- Para que las vistas de consulta se actualicen después de cancelar o modificar, basta con llamar `refrescar()` de cada vista.

**P4 — RF-14, RF-15 y RF-17**

- **RF-14**: por cada ocurrencia, `validar_reservacion(...)`; luego `insertar_reservacion(conexion, datos, serie_id=...)` dentro de una sola transacción.
- **RF-15**: `VistaCrearReservacion(..., on_cambio=panel.refrescar)` avisa al panel después de cada creación.
- **RF-16**: `consultar_reservaciones()` y `COLUMNAS_RESERVACION` ya traen estudiante, sala, fecha, horario, personas y estado.
- **RF-17**: hoy la creación se registra con `tipo_accion='creación'` y `entidad='reservación'`. Si P4 define otra convención o su propia función, solo hay que cambiar `gestion_reservaciones.registrar_auditoria()`.

**Ventana principal (quien la construya)**

- Llamar `configurar_estilos(raiz)` una vez.
- Montar las cuatro vistas pasando `on_volver` para regresar al panel.

## 5. Pendientes que no son de P2 pero afectan la versión candidata

- `main.py` todavía solo inicializa la BD; falta la ventana principal que monte todas las vistas.
- El repositorio incluye carpetas `__pycache__` y `database/reservaciones.db` (esta última con un estudiante de prueba, María López, que no está en los datos iniciales). Se agregó un `.gitignore` para `__pycache__`. Conviene decidir en equipo si la BD se versiona, porque RF-01 ya la crea al iniciar.
- Datos iniciales de reservaciones: si el equipo quiere que el evaluador vea reservaciones desde el inicio, se deben generar con fechas relativas al día de ejecución (una fecha fija quedaría en el pasado).
