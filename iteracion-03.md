# Iteración 3 - API REST

## Objetivo
Implementar en `app/main.py` los cuatro endpoints JSON de tickets:
`POST /tickets`, `GET /tickets`, `GET /tickets/{id}`, `PATCH /tickets/{id}`.

## Contexto
Depende de la Iteración 1 (modelo/persistencia) y de la Iteración 2 (clasificador,
que usa `POST /tickets`). La Iteración 4 (frontend) consume estos endpoints.

## Solución propuesta
Según `SPEC.md` §4:
- `POST /tickets`: valida `title` (1–200) y `description` (1–5000) tras trim →
  `422` si inválido; llama a `classify_ticket`, persiste y devuelve `201` con el
  ticket clasificado. **Nunca `5xx` por fallo del LLM** (el clasificador ya da
  fallback, pero envolver en try/except por seguridad).
- `GET /tickets`: lista ordenada por `created_at` desc; filtros opcionales
  `category`/`priority`/`status` combinables.
- `GET /tickets/{id}`: `200` o `404`.
- `PATCH /tickets/{id}`: actualiza solo `status`/`priority`; `404` si no existe,
  `422` si fuera de enum; actualiza `updated_at`.

## Tareas
- [ ] `POST /tickets` con validación (Pydantic) y clasificación síncrona
- [ ] `GET /tickets` con filtros combinables
- [ ] `GET /tickets/{id}` con `404`
- [ ] `PATCH /tickets/{id}` (status/priority) con `404`/`422`
- [ ] Asegurar `create_db_and_tables()` en startup

## Ficheros afectados
- `app/main.py`
- (posible) `app/schemas.py` para los modelos de request/response

## Criterio de completado
`pytest` pasa: `test_post_ticket_creates_ticket_with_classification`,
`test_created_ticket_is_persisted_and_listed`, `test_post_ticket_rejects_invalid_input`
y `test_update_ticket_and_filter_by_status_priority_category` verdes. 0 fallos.

## Estado
EN PROGRESO
