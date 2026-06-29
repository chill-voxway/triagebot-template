# Iteración 4 - Frontend (tablero)

## Objetivo
Servir en `GET /` una página HTML con formulario de creación, tablero de tickets
y filtros, usando HTMX para refrescar sin recargar.

## Contexto
Depende de la Iteración 3 (necesita `POST /tickets` y `GET /tickets`). Es la capa
de presentación; sin los endpoints no hay datos que mostrar.

## Solución propuesta
Según `SPEC.md` §6:
- `app/main.py`: ruta `GET /` que renderiza Jinja2 (devuelve HTML, no JSON).
- `templates/index.html`: formulario (`title`, `description`) + botón "Crear
  ticket" que hace `POST /tickets` vía HTMX y refresca la tabla; tres selects de
  filtro (`category`/`priority`/`status`); Tailwind por CDN.
- `templates/_tickets_table.html`: parcial con la tabla (id, title, category con
  color, priority badge, tags, status, created_at) reutilizado por HTMX.

## Tareas
- [ ] Ruta `GET /` con Jinja2Templates
- [ ] `templates/index.html` con formulario + filtros + HTMX
- [ ] `templates/_tickets_table.html` (parcial de la tabla)
- [ ] Endpoint/respuesta parcial para que HTMX refresque la tabla tras crear/filtrar

## Ficheros afectados
- `app/main.py`
- `templates/index.html`
- `templates/_tickets_table.html`

## Criterio de completado
`pytest` sigue verde y, manualmente (`uvicorn app.main:app --reload`), se puede
crear un ticket desde el navegador y verlo aparecer en el tablero sin recargar.

## Estado
PENDIENTE
