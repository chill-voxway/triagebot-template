# Iteración 4 - Frontend (página única HTMX)

## Objetivo

Servir en `GET /` una **única página** con tres bloques verticales —formulario
de creación, filtros y tablero— donde todas las interacciones se resuelven con
**HTMX** pidiendo **fragmentos de HTML** ya renderizados al servidor e
insertándolos en el DOM, **sin recargar la página**.

## Contexto

Depende de la Iteración 3 (capa JSON ya implementada: `POST /tickets` y
`GET /tickets` con filtros combinables en `app/main.py`). Esta iteración es la
capa de presentación; sin esos endpoints no hay datos que mostrar.

**Restricciones duras (innegociables):**

- **Cero build tools:** sin webpack, sin `npm install`. Tailwind y HTMX entran
  por CDN.
- **Cero estado en cliente:** el estado vive en el servidor; HTMX no mantiene
  store ni context.
- **El HTML vive en `templates/`,** nunca como strings en `app/main.py`.
- Sin login, roles, frameworks JS de cliente (React/Vue) ni edición inline
  avanzada.

## Stack frontend

| Pieza | Elección | Estado en el repo |
|---|---|---|
| Markup | HTML semántico + Jinja2 | `templates/` |
| Plantillas | `Jinja2Templates` de FastAPI | A montar en `main.py` |
| Interactividad | HTMX por CDN (`htmx.org@2.0.4`) | Ya enlazado en `index.html` |
| Estilos | Tailwind por CDN | Ya enlazado en `index.html` |

## Valores reales del backend (resuelven el "pendiente de confirmar" del spec)

Aterrizados contra el código, **no son propuestas**:

- **`status`** (`app/models.py`, enum `Status`): `open` · `in_progress` ·
  `closed`. ⚠️ El filtro y la columna de estado usan **exactamente** estos tres
  (no `nuevo/en_progreso/resuelto/cerrado`).
- **`category`** (`Category`): `bug` · `feature_request` · `question` · `urgent`.
- **`priority`** (`Priority`): `P1` · `P2` · `P3`.
- **`tags`**: `list[str]` → se itera directamente en Jinja2.
- **`created_at`**: objeto `datetime` UTC → en plantilla
  `ticket.created_at.strftime('%Y-%m-%d %H:%M')`.

## Estructura de la página (`GET /`)

Página vertical, tres bloques en este orden:

```
┌──────────────────────────────────────────────┐
│  Bloque 1 · FORMULARIO crear ticket           │
├──────────────────────────────────────────────┤
│  Bloque 2 · FILTROS (category / priority /     │
│             status)                            │
├──────────────────────────────────────────────┤
│  Bloque 3 · TABLERO  (#tablero)                │
│             lista de tickets                   │
└──────────────────────────────────────────────┘
```

El tablero se envuelve en un contenedor `id="tablero"`. Es el **único** punto que
se refresca: tanto el formulario como los filtros lo apuntan.

### Bloque 1 — Formulario de creación

| Campo | Tipo | Obligatorio |
|---|---|---|
| `title` | `input[type=text]` | Sí (`required`) |
| `description` | `textarea` | Sí (`required`) |

Botón "Crear ticket" (`type="submit"`). Al enviar: `POST /tickets/crear` →
`hx-target="#tablero"`, `hx-swap="innerHTML"`; el form se resetea tras éxito con
`hx-on::after-request="if (event.detail.successful) this.reset()"`.

### Bloque 2 — Filtros

Tres `select` envueltos en `<form id="filtros">` (sin submit), cada uno con una
opción "Todos" (valor vacío) como primera entrada. Cada select hace
`hx-get="/tickets/tablero"`, `hx-trigger="change"`, `hx-include="#filtros"`,
`hx-target="#tablero"`, `hx-swap="innerHTML"` → así envía los tres valores en
cada petición y los filtros se **combinan**.

| Filtro | Opciones |
|---|---|
| `category` | Todas · `bug` · `feature_request` · `question` · `urgent` |
| `priority` | Todas · `P1` · `P2` · `P3` |
| `status` | Todos · `open` · `in_progress` · `closed` |

### Bloque 3 — Tablero

Tabla con una fila por ticket. Columnas (en orden):

| Columna | Origen | Render |
|---|---|---|
| `id` | `ticket.id` | Texto plano |
| `title` | `ticket.title` | Texto plano |
| `category` | `ticket.category` | Etiqueta con color (ver Mapeo visual) |
| `priority` | `ticket.priority` | Badge con color |
| `tags` | `ticket.tags` | Chips pequeños neutros |
| `status` | `ticket.status` | Badge neutro |
| `created_at` | `ticket.created_at` | `YYYY-MM-DD HH:MM` |

**Estado vacío:** si no hay tickets (o el filtro no devuelve ninguno), mostrar una
fila/mensaje "No hay tickets que coincidan".

## Endpoints — dos capas separadas

Cada endpoint devuelve **un único content-type**.

### Capa HTML / HTMX (alimenta la UI) — a implementar

| Método | Ruta | Devuelve | Propósito |
|---|---|---|---|
| `GET` | `/` | HTML página | Renderiza `index.html` (los 3 bloques) |
| `GET` | `/tickets/tablero` | HTML fragmento | Tablero filtrado. Query: `category`, `priority`, `status` (vacío/ausente = sin filtrar) |
| `POST` | `/tickets/crear` | HTML fragmento | Form `title`+`description` → crea+clasifica+persiste → devuelve el tablero refrescado |

- `GET /tickets/tablero` reutiliza la misma lógica de filtrado que `GET /tickets`.
- `POST /tickets/crear` reutiliza la misma lógica de creación que `POST /tickets`
  (clasificación vía `app.classifier`, fallback seguro). En error de validación,
  devuelve un fragmento con el mensaje de error **sin romper la página** (sin
  `5xx`, sin pantalla en blanco).

### Capa JSON (API / tests) — ya existe

| Método | Ruta | Devuelve |
|---|---|---|
| `POST` | `/tickets` | JSON `201` |
| `GET` | `/tickets` | JSON (lista filtrable) |

### Nota de diseño

Se separan JSON y HTML en endpoints distintos para que cada uno tenga un único
content-type y propósito claro. La alternativa —un solo `POST /tickets` que
negocie el formato según la cabecera `HX-Request`— es válida pero mezcla
responsabilidades, por eso se **descarta** como diseño principal.

## Comportamiento HTMX (los 4 patrones)

1. **Form sin recargar** → `hx-post="/tickets/crear"`, `hx-target="#tablero"`,
   `hx-swap="innerHTML"`, reset del form tras éxito.
2. **Filtrar al cambiar un select** → `hx-get="/tickets/tablero"`,
   `hx-trigger="change"`, `hx-include="#filtros"`, `hx-target="#tablero"`.
3. **El backend devuelve HTML, no JSON** → los endpoints de la capa HTML
   renderizan parciales Jinja2, no serializan JSON.
4. **Reemplazar contenido** → siempre `hx-swap="innerHTML"` sobre `#tablero`
   (no `outerHTML`, para no perder el `id` del contenedor).

## Mapeo visual (clases Tailwind)

**`category` (etiqueta con color):**

| Valor | Clases Tailwind |
|---|---|
| `bug` | `bg-red-100 text-red-800` |
| `feature_request` | `bg-blue-100 text-blue-800` |
| `question` | `bg-slate-100 text-slate-700` |
| `urgent` | `bg-orange-100 text-orange-800` |

**`priority` (badge):**

| Valor | Clases Tailwind |
|---|---|
| `P1` (crítica) | `bg-red-600 text-white` |
| `P2` (media) | `bg-amber-500 text-white` |
| `P3` (baja) | `bg-emerald-600 text-white` |

**`tags`:** chips pequeños neutros `bg-gray-100 text-gray-700`.

**`status` (badge neutro):** color sugerido por estado real —
`open` → `bg-slate-100 text-slate-700`, `in_progress` → `bg-blue-100 text-blue-800`,
`closed` → `bg-emerald-100 text-emerald-800`.

## Plantillas Jinja2

```
templates/
├── index.html             # página completa: formulario + filtros + #tablero
└── _tickets_table.html    # parcial: tabla + filas (o estado vacío)
```

- `index.html` **incluye** `_tickets_table.html` dentro de `#tablero` para el
  render inicial server-side (sin parpadeo).
- `GET /tickets/tablero` y `POST /tickets/crear` **devuelven**
  `_tickets_table.html` renderizado con la lista ya filtrada/actualizada.
- Una sola fuente de verdad para el tablero ⇒ no se duplica el markup de filas.

> El spec de Marta llama al parcial `_tablero.html`; en este repo se mantiene el
> nombre ya existente `_tickets_table.html` (el stub está creado y referenciado).
> Son equivalentes.

## Tareas

- [x] Montar `Jinja2Templates(directory="templates")` y ruta `GET /` que renderiza
      `index.html` (devuelve HTML, no JSON)
- [x] `GET /tickets/tablero` → fragmento `_tickets_table.html` filtrado por
      `category`/`priority`/`status` (vacío = todos), reutilizando la lógica de
      filtrado existente
- [x] `POST /tickets/crear` → crea+clasifica+persiste (misma lógica que
      `POST /tickets`) y devuelve el tablero refrescado; error de validación →
      fragmento con mensaje, sin romper la página
- [x] `templates/index.html`: tres bloques (form HTMX + filtros `#filtros` +
      contenedor `#tablero` que incluye el parcial)
- [x] `templates/_tickets_table.html`: filas con `id`, `title`, `category` (color),
      `priority` (badge), `tags` (chips), `status` (badge), `created_at` formateado,
      + estado vacío "No hay tickets que coincidan"

## Ficheros afectados

- `app/main.py` — `Jinja2Templates`, `GET /`, `GET /tickets/tablero`,
  `POST /tickets/crear`
- `templates/index.html`
- `templates/_tickets_table.html`

## Criterio de completado

`pytest` sigue verde y se cumplen los criterios de aceptación del frontend:

- [x] `GET /` devuelve una página con los tres bloques.
- [x] Crear un ticket desde el formulario lo añade al tablero **sin recargar**.
- [x] El formulario se resetea tras una creación correcta.
- [x] Cambiar cualquier filtro actualiza el tablero **sin recargar**.
- [x] Los filtros se combinan (categoría + prioridad + estado simultáneos).
- [x] Cada fila muestra: id · title · category (color) · priority (badge) · tags ·
      status · created_at.
- [x] Estado vacío visible cuando no hay coincidencias.
- [x] Un fallo del backend/IA no rompe la página (fallback seguro, sin pantalla
      en blanco).
- [x] El HTML vive en `templates/`, no como strings en `main.py`.

Verificación manual: `py -3.12 -m uvicorn app.main:app --reload`, crear un ticket
desde el navegador y verlo aparecer en el tablero sin recargar.

## Estado

COMPLETADA - 2026-06-30
