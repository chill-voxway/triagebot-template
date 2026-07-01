# Iteración 5 - Nuevas funcionalidades (plazos y ciclo de vida)

## Objetivo
Implementar dos líneas de trabajo paralelas e independientes que amplían el modelo
de datos y el frontend: gestión de plazos con alertas de vencimiento, y expansión
del ciclo de vida del ticket con registro de tiempos por estado.

## Contexto
Depende de IT-1–IT-4.1 (modelo, clasificador, API y frontend ya implementados).
Cada trabajo vive en su propia rama y puede desarrollarse en paralelo sin conflictos.

---

## TRABAJO 1 — Gestión de plazos y alertas de vencimiento
**Rama:** `feature/plazos-tickets`

### Objetivo
Calcular automáticamente fechas límite según la prioridad del ticket, visualizar
alertas en el tablero e identificar tickets retrasados mediante un filtro de URL.

### Tareas

#### `app/models.py`
- [x] Añadir campo `fecha_limite: datetime` (UTC) al modelo `Ticket`
- [x] Hook o método que calcule `fecha_limite` al crear un ticket según prioridad:
  - P1 (Alta): `23:59:59` del día de creación (EoD)
  - P2 (Media): `23:59:59` del día siguiente (+24 h)
  - P3 (Baja): `23:59:59` pasado mañana (+48 h)
- [x] Propiedad `esta_vencido` → `True` si `fecha_limite < utcnow()` y el ticket
  no está en estado de finalización

#### `app/db.py`
- [x] Añadir columna `fecha_limite` al esquema de la tabla de tickets
- [x] `create_ticket` y `update_ticket` mapean y persisten `fecha_limite`

#### Handler `GET /tickets`
- [x] Aceptar parámetro de consulta `?vencidos=true`
- [x] Si activo, filtrar: `fecha_limite < utcnow()` AND estado no finalizado

#### `templates/index.html` y `_tickets_table.html`
- [x] Mostrar `fecha_limite` formateada en la tarjeta del ticket
- [x] Si `ticket.esta_vencido`, inyectar clase CSS de alerta (borde rojo y badge "Vencido")
- [x] Checkbox de alternancia que filtra vía `?vencidos=true`

---

## TRABAJO 2 — Ciclo de vida del ticket y tiempos de estado
**Rama:** `feature/ciclo-vida-tickets`

### Objetivo
Expandir los estados disponibles, registrar cuándo cambia cada estado y calcular
el tiempo transcurrido en el estado actual. Habilitar la reapertura de incidencias.

### Tareas

#### `app/models.py`
- [x] Ampliar el enum `Status` a cuatro valores: `open`, `in_progress`, `resuelto`, `closed`
- [x] Añadir campo `fecha_cambio_estado: datetime` (UTC)
- [x] Máquina de estados con reapertura (`resuelto`/`closed` → `open`)
- [x] Propiedad `tiempo_en_estado_actual` (texto legible: min/h/días)

#### `app/db.py`
- [x] Columna `fecha_cambio_estado` en esquema; migración `ALTER TABLE` para DBs existentes
- [x] Toda actualización de estado fuerza `fecha_cambio_estado = utcnow()`

#### Handler `GET /tickets`
- [x] `tiempo_en_estado_actual` accesible desde la plantilla vía propiedad del modelo

#### `templates/index.html` y `_tickets_table.html`
- [x] Tablero kanban 4 columnas: *Abierto*, *En Curso*, *Resuelto*, *Cerrado*
- [x] Tiempo en estado actual en cada tarjeta
- [x] Botones condicionales: "Comenzar", "Resolver", "Reabrir" con `POST /tickets/{id}/transicion`

---

## Ficheros afectados
- `app/models.py`
- `app/db.py`
- `app/main.py`
- `templates/index.html`
- `templates/_tickets_table.html`

## Criterio de completado
- 5/5 tests de aceptación en verde ✅
- `ruff check .` limpio ✅
- Tablero kanban funcional con 4 columnas y transiciones HTMX
- Fecha límite visible y badge "Vencido" operativo
- Filtro `?vencidos=true` funcional

## Estado
COMPLETADA - 2026-06-30
