# Iteración 7 - Estadísticas de tickets (GET /tickets/stats)

## Objetivo
Añadir un endpoint JSON analítico que devuelva conteos globales de tickets
agrupados por categoría, prioridad y estado. Sin cambios de frontend.

## Contexto
Depende de IT-5 (el enum `Status` tiene los cuatro estados definitivos:
`open`, `in_progress`, `resuelto`, `closed`). Se puede desarrollar en paralelo
con IT-6 (calidad y entrega) sin bloquearse mutuamente.

## Solución propuesta
Añadir `GET /tickets/stats` en `app/main.py`, declarado antes de
`GET /tickets/{ticket_id}` para que FastAPI no intente parsear `"stats"` como
un entero. La lógica itera sobre todos los tickets y acumula conteos por valor
de enum, inicializando a 0 todos los valores posibles para garantizar que la
respuesta siempre incluye todas las claves aunque estén vacías.

## Tareas

### `app/main.py`
- [ ] Añadir endpoint `GET /tickets/stats` (antes de `GET /tickets/{id}`)
- [ ] Devolver JSON con `total`, `by_category`, `by_priority`, `by_status`
- [ ] Inicializar conteos a 0 para todos los valores de cada enum

## Estructura del JSON de respuesta
```json
{
  "total": 47,
  "by_category": {
    "bug": 18,
    "feature_request": 20,
    "question": 9,
    "urgent": 0
  },
  "by_priority": {
    "P1": 5,
    "P2": 15,
    "P3": 27
  },
  "by_status": {
    "open": 20,
    "in_progress": 10,
    "resuelto": 12,
    "closed": 5
  }
}
```

## Ficheros afectados
- `app/main.py`

## Criterio de completado
`GET /tickets/stats` devuelve 200 con JSON válido; todos los conteos son 0
cuando no hay tickets; `ruff check .` limpio; suite de tests en verde.

## Estado
COMPLETADA - 2026-06-30
