# Iteración 4.1 - Persistencia de los filtros del tablero en la URL

> Sub-iteración del **frontend (Iteración 4)** y **la siguiente a realizar**:
> completa el tablero de IT-4 haciendo que el estado de los filtros sobreviva a
> recargas y enlaces. Depende de IT-4.

## Objetivo

Que el estado de los filtros del tablero (`category`, `priority`, `status`)
**sobreviva a una recarga**, al botón "atrás/adelante" del navegador y a compartir
un enlace, persistiéndolo en la **URL** (query params). Todo de forma
**declarativa** (atributos HTMX + lectura de query params en el servidor), sin
tocar la creación de tickets.

## Contexto

Stack: FastAPI + Jinja2 + HTMX + Tailwind. Los filtros son tres `select`
(`category`, `priority`, `status`) dentro de `<form id="filtros">`, y `#tablero`
es el contenedor del tablero.

Hoy (tras la Iteración 4) los selects hacen `hx-get="/tickets/tablero"` y el
estado del filtro **solo vive en el DOM** tras el swap: al recargar la página se
pierde (el navegador vuelve a `/` sin query, los selects vuelven a "Todos" y el
tablero sale sin filtrar). Es la continuación natural de la Iteración 4 (frontend
ya implementado), de la que depende.

## Restricciones duras

- **No** establecer ninguna cabecera de respuesta (nada de `HX-Push-Url` desde el
  servidor).
- **No** usar `localStorage` ni `sessionStorage`.
- **No** escribir JavaScript a mano.
- Todo el comportamiento se logra con **atributos HTMX** + **lectura de query
  params** en el servidor.

## Solución propuesta

Enrutar el filtrado a `GET /` (la página real) en lugar de a
`GET /tickets/tablero`, y dejar que HTMX empuje esa URL al historial.

### 1. `templates/index.html` — selects apuntando a `GET /`

Cada uno de los tres `select` usa estos atributos:

```html
hx-get="/"
hx-include="#filtros"
hx-target="#tablero"
hx-select="#tablero"
hx-swap="outerHTML"
hx-push-url="true"
hx-trigger="change"
```

- `hx-get="/"` + `hx-include="#filtros"`: al cambiar un select se pide
  `GET /?category=...&priority=...&status=...` con los tres valores.
- `hx-select="#tablero"`: de la **página completa** que devuelve `GET /`, HTMX
  extrae únicamente el elemento `#tablero`.
- `hx-target="#tablero"` + `hx-swap="outerHTML"`: reemplaza el elemento
  `#tablero` por el `#tablero` de la respuesta (el `id` se conserva porque el
  contenedor de la respuesta también lo lleva).
- `hx-push-url="true"`: empuja al historial la **URL real de la petición**
  (`/?category=bug&...`), que es exactamente la página que reproduce el estado al
  recargar o al compartir el enlace.

### 2. `app/main.py` — `GET /` acepta los filtros por query param

`GET /` admite `category`, `priority`, `status` opcionales. Con ellos:

- (a) **filtra** y renderiza `#tablero` ya filtrado (reutilizando la **misma**
  función de filtrado del backend, sin duplicar la consulta), y
- (b) pasa a la plantilla un dict `filtros` con los valores activos (vacío/None
  donde no haya filtro). La query incluye **solo** los parámetros con valor.

### 3. `templates/index.html` — `selected` según `filtros`

En cada `<option>` de los tres selects, marcar `selected` cuando su valor
coincida con el de `filtros`, para que al recargar los desplegables muestren la
opción activa (y no "Todos").

### Notas de diseño

- **`GET /` ya existía** (Iteración 4): aquí se le añaden los query params y el
  contexto `filtros`. Se **reutiliza** la función de filtrado existente
  (`_filtered_tickets` + coerción de vacío/inválido a `None`), no se duplica.
- **Fuera de alcance:** `POST /tickets/crear` y la creación de tickets **no se
  tocan**. (El refresco del tablero tras crear sigue como en IT-4; armonizarlo
  con los filtros activos, si se quiere, sería trabajo de otra iteración.)
- El endpoint `GET /tickets/tablero` deja de usarse para el filtrado; se decide
  en implementación si se conserva o se retira (no es objetivo de esta iteración).

## Tareas

- [ ] `GET /` acepta `category`/`priority`/`status` opcionales: filtra `#tablero`
      y pasa el dict `filtros` a la plantilla (query solo con params con valor),
      reutilizando la función de filtrado existente
- [ ] `templates/index.html`: cambiar los tres selects a `hx-get="/"`,
      `hx-include="#filtros"`, `hx-target="#tablero"`, `hx-select="#tablero"`,
      `hx-swap="outerHTML"`, `hx-push-url="true"`, `hx-trigger="change"`
- [ ] `templates/index.html`: marcar `selected` en cada `<option>` según `filtros`
- [ ] No duplicar la consulta de filtrado (una sola función backend reutilizada)
- [ ] No tocar `POST /tickets/crear` ni la creación de tickets

## Ficheros afectados

- `app/main.py` — `GET /` con query params + contexto `filtros`
- `templates/index.html` — atributos HTMX de los selects + `selected`

## Criterio de completado

`pytest` sigue verde, `ruff check .` limpio y se cumplen:

- [ ] Al filtrar, la barra de direcciones pasa a `/?...` con los filtros activos
      (nunca a `/tickets/tablero?...`).
- [ ] Al refrescar con filtros aplicados: el tablero sale filtrado y los tres
      selects muestran la opción correcta.
- [ ] El botón "atrás/adelante" y un enlace copiado reproducen el mismo estado.
- [ ] No se establece ninguna cabecera de respuesta, ni se usa
      `localStorage`/`sessionStorage`, ni JavaScript manual.

## Estado

EN PROGRESO
