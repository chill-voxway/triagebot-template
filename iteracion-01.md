# Iteración 1 - Modelo de datos y persistencia

## Objetivo
Definir la entidad `Ticket` (SQLModel) y la capa de persistencia SQLite para que
el resto de iteraciones tengan modelo y base de datos sobre los que construir.

## Contexto
Es la primera iteración: no depende de ninguna otra. Todas las demás (clasificador,
API, frontend) dependen de que exista el modelo `Ticket` y la sesión de base de
datos. Sin esto, nada puede persistir tickets.

## Solución propuesta
- `app/models.py`: modelo `Ticket` (SQLModel, `table=True`) con los campos del
  `SPEC.md` §3: `id`, `title`, `description`, `category`, `priority`, `tags`,
  `status`, `created_at`, `updated_at`.
- Enums vinculantes: `category` ∈ {bug, feature_request, question, urgent},
  `priority` ∈ {P1, P2, P3}, `status` ∈ {open, in_progress, closed}.
- `status` por defecto `open`; `created_at`/`updated_at` en UTC generados en
  servidor. `tags` serializados (JSON en columna) — máx. 5 tags, máx. 30 chars.
- `app/db.py`: engine SQLite (ruta desde `DATABASE_URL`, default `triagebot.db`),
  `create_db_and_tables()` y un helper `get_session()`.

## Tareas
- [ ] Definir `Ticket` en `app/models.py` con campos y enums
- [ ] Implementar engine + `create_db_and_tables()` + `get_session()` en `app/db.py`
- [ ] Soportar `DATABASE_URL` (los tests lo usan para aislar la BD)
- [ ] Tests unitarios del modelo: import sin error, enums rechazan valores inválidos

## Ficheros afectados
- `app/models.py`
- `app/db.py`
- `tests/test_models.py` (nuevo)

## Criterio de completado
`pytest` pasa: el modelo se importa sin errores y los enums rechazan valores
fuera de lista. 0 fallos.

## Estado
COMPLETADA - 2026-06-29
