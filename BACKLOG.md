# BACKLOG — TriageBot

> Épicas, historias y tareas con criterios de aceptación verificables.
> Se actualiza continuamente; absorbe los cambios de alcance e iteraciones en curso.

---

## Estado global

| Iteración | Descripción | Estado |
|-----------|-------------|--------|
| [IT-1](#iteración-1) | Modelo de datos y persistencia | COMPLETADA |
| [IT-2](#iteración-2) | Clasificador LLM | COMPLETADA |
| [IT-3](#iteración-3) | API REST | COMPLETADA |
| [IT-4](#iteración-4) | Frontend | COMPLETADA |
| [IT-4.1](#iteración-4) | Frontend · persistencia de filtros en URL | COMPLETADA |
| [IT-5](#iteración-5) | Nuevas funcionalidades (plazos + ciclo de vida) | COMPLETADA |
| [IT-6](#iteración-6) | Calidad y entrega | PENDIENTE |
| [IT-7](#iteración-7) | Estadísticas (GET /tickets/stats) | COMPLETADA |

**Iteración activa:** IT-5 (feat/iteracion-05 · PR #16)

> Un estado `EN PROGRESO` siempre está respaldado por una rama remota
> `feat/iteracion-XX` + un Draft PR en `Ceballooss/triagebot-Grupo06`. Esa es la
> señal compartida de fichaje: humanos y el comando `/detectar-siguiente-iteracion`
> leen el estado igual. No marques `EN PROGRESO` sin su rama/PR.

---

## Épica 1 — Modelo de datos y persistencia

### Historia 1.1 — Entidad Ticket
**Iteración:** IT-1 | **Depende de:** — | **Bloqueada por:** —

- [x] Crear `app/models.py` con `Ticket` (SQLModel)
- [x] Campos: `id`, `title`, `description`, `category`, `priority`, `tags`, `status`, `created_at`, `updated_at`
- [x] Enums: `category` ∈ {bug, feature_request, question, urgent} · `priority` ∈ {P1, P2, P3} · `status` ∈ {open, in_progress, closed}
- [x] `status` default `open`; timestamps UTC generados en servidor
- [x] Crear `app/db.py`: engine SQLite, `create_db_and_tables()`, `get_session()`

**Criterio de aceptación:** modelo importable sin errores; enums rechazan valores fuera de lista.

---

## Épica 2 — Clasificador LLM

### Historia 2.1 — Módulo `app/classifier.py`
**Iteración:** IT-2 | **Depende de:** H1.1 | **Bloqueada por:** —

- [x] Expone `classify_ticket(title: str, description: str) -> dict`
- [x] Llama a `openai/gpt-oss-120b` vía OpenRouter (`base_url`, key `OPENROUTER_API_KEY`)
- [x] Valida salida contra enums; fallback si inválida o si el LLM falla dos veces
- [x] No propaga excepciones del SDK

Fallback: `{"category": "question", "priority": "P3", "tags": []}`

**Criterio de aceptación:** `test_classifier_module_contract` verde; con LLM mockeado devuelve dict con las tres claves válidas.

---

## Épica 3 — API REST

### Historia 3.1 — `POST /tickets`
**Iteración:** IT-3 | **Depende de:** H1.1, H2.1 | **Bloqueada por:** H2.1

- [x] Acepta `{title, description}`, llama a `classify_ticket`, persiste y devuelve `201`
- [x] `422` si `title` o `description` vacíos o fuera de límite
- [x] Nunca `5xx` por fallo del LLM

**Criterio de aceptación:** `test_post_ticket_creates_with_classification` verde · `test_post_ticket_empty_title_returns_422` verde.

### Historia 3.2 — `GET /tickets`
**Iteración:** IT-3 | **Depende de:** H1.1 | **Bloqueada por:** H1.1

- [x] Lista tickets ordenados por `created_at` desc
- [x] Filtros opcionales: `category`, `priority`, `status`

**Criterio de aceptación:** `test_get_tickets_returns_list` verde.

### Historia 3.3 — `GET /tickets/{id}`
**Iteración:** IT-3 | **Depende de:** H1.1 | **Bloqueada por:** H1.1

- [x] `200` con ticket si existe; `404` si no

**Criterio de aceptación:** `test_get_ticket_by_id_not_found` verde.

### Historia 3.4 — `PATCH /tickets/{id}`
**Iteración:** IT-3 | **Depende de:** H1.1 | **Bloqueada por:** H1.1

- [x] Actualiza solo `status` y/o `priority`
- [x] `404` si no existe; `422` si valor fuera de enum

**Criterio de aceptación:** PATCH inválido → `422`; PATCH válido → `200` con ticket actualizado.

---

## Épica 4 — Frontend

### Historia 4.1 — Tablero (`GET /`)
**Iteración:** IT-4 | **Depende de:** H3.1, H3.2 | **Bloqueada por:** H3.1, H3.2

- [x] `GET /` con `Jinja2Templates`: página única con form (`title`, `description`) + botón "Crear ticket"
- [x] Capa HTML separada de la JSON: `GET /tickets/tablero` (fragmento filtrado) y `POST /tickets/crear` (crea + devuelve tablero) devuelven HTML; `POST /tickets` y `GET /tickets` siguen siendo JSON
- [x] HTMX refresca `#tablero` (`hx-swap="innerHTML"`) sin recargar; form se resetea tras éxito
- [x] Tabla: `id`, `title`, `category` (badge color), `priority` (badge), `tags`, `status`, `created_at`
- [x] Tres selects de filtro combinables: `category`, `priority` (`P1/P2/P3`), `status` (`open/in_progress/closed`)
- [x] Estado vacío "No hay tickets que coincidan"; fallo del backend/IA no rompe la página

**Criterio de aceptación:** crear ticket desde navegador → aparece en tablero sin recarga de página; filtros combinables sin recarga.

### Historia 4.2 — Persistir los filtros del tablero en la URL
**Iteración:** IT-4.1 | **Depende de:** H4.1 | **Bloqueada por:** H4.1

- [x] Filtros enrutados a `GET /` (no `/tickets/tablero`): cada select con `hx-get="/"`, `hx-include="#filtros"`, `hx-target="#tablero"`, `hx-select="#tablero"`, `hx-swap="outerHTML"`, `hx-push-url="true"`, `hx-trigger="change"`
- [x] `GET /` acepta `category`/`priority`/`status` opcionales: filtra `#tablero` y pasa el dict `filtros` a la plantilla (query solo con params con valor)
- [x] `<option selected>` según `filtros` en los tres selects (estado visible tras recarga)
- [x] Una sola función de filtrado reutilizada (sin duplicar la consulta); `POST /tickets/crear` intacto
- [x] Sin cabeceras de respuesta (no `HX-Push-Url`), sin `localStorage`/`sessionStorage`, sin JS manual

**Criterio de aceptación:** al filtrar, la URL pasa a `/?...` (nunca a `/tickets/tablero?...`); recargar reproduce tablero filtrado + selects en la opción correcta; atrás/adelante y enlace copiado reproducen el estado; sin cabeceras de respuesta, sin storage, sin JS manual.

---

## Épica 5 — Nuevas funcionalidades (plazos + ciclo de vida)

### Historia 5.1 — Gestión de plazos y alertas de vencimiento
**Iteración:** IT-5 | **Depende de:** H4.1, H4.2 | **Bloqueada por:** IT-4.1
**Rama:** `feature/plazos-tickets`

- [x] Campo `fecha_limite` (DateTime UTC) en `app/models.py`; calculado al crear según prioridad (P1=EoD, P2=+24 h, P3=+48 h)
- [x] Propiedad `esta_vencido` en el modelo (compara `fecha_limite` con `utcnow()` si no finalizado)
- [x] Columna `fecha_limite` en esquema (`app/db.py`); `create_ticket`/`update_ticket` la mapean
- [x] `GET /tickets` acepta `?vencidos=true` y filtra tickets caducados no cerrados

### Historia 5.2 — Frontend de plazos
**Iteración:** IT-5 | **Depende de:** H5.1 | **Bloqueada por:** H5.1

- [x] `templates/index.html`: mostrar `fecha_limite` formateada en la tarjeta
- [x] Badge/clase CSS "Vencido" cuando `ticket.esta_vencido` es verdadero
- [x] Botón/checkbox de alternancia que filtra vía `?vencidos=true`

### Historia 5.3 — Ciclo de vida y tiempos de estado
**Iteración:** IT-5 | **Depende de:** H4.1, H4.2 | **Bloqueada por:** IT-4.1
**Rama:** `feature/ciclo-vida-tickets`

- [x] Ampliar enum `status` a: `open`, `in_progress`, `resuelto`, `closed`
- [x] Campo `fecha_cambio_estado` (DateTime UTC) en `app/models.py`; se actualiza en cada cambio de estado
- [x] Propiedad `tiempo_en_estado_actual` que devuelve texto legible (min/h/días)
- [x] Máquina de estados con reapertura explícita (`resuelto`/`cerrado` → `open`)
- [x] Columna `fecha_cambio_estado` en esquema (`app/db.py`); forzar `= utcnow()` al cambiar estado
- [x] Handler `GET /tickets` expone `tiempo_en_estado_actual` a la plantilla

### Historia 5.4 — Frontend de ciclo de vida
**Iteración:** IT-5 | **Depende de:** H5.3 | **Bloqueada por:** H5.3

- [x] Tablero reorganizado en 4 columnas: *Abierto*, *En Curso*, *Resuelto*, *Cerrado*
- [x] Métrica de tiempo en cada tarjeta (ej. `"En curso desde hace 45 min"`)
- [x] Botones condicionales: "Comenzar" (open→in_progress), "Resolver" (in_progress→resuelto), "Reabrir" (resuelto/closed→open)

---

## Épica 6 — Calidad y entrega

### Historia 6.1 — Tests verdes
**Iteración:** IT-6 | **Depende de:** H5.1–H5.4 | **Bloqueada por:** IT-5

- [ ] Los 5 tests de `tests/test_acceptance.py` pasan (`pytest -v`)
- [ ] `ruff check .` sin errores

### Historia 6.2 — CI en GitHub Actions
**Iteración:** IT-6 | **Depende de:** H6.1 | **Bloqueada por:** H6.1

- [ ] Workflow `.github/workflows/ci.yml`: ruff + pytest en cada push a `main`
- [ ] Badge de estado en `README.md`

### Historia 6.3 — README
**Iteración:** IT-6 | **Depende de:** — | **Bloqueada por:** —

- [ ] Instrucciones de arranque: clonar, crear `.env`, `uvicorn app.main:app --reload`
- [ ] Prerequisitos: Python 3.11+, `pip install -r requirements.txt`

---

## Épica 7 — Estadísticas

### Historia 7.1 — Endpoint GET /tickets/stats
**Iteración:** IT-7 | **Depende de:** H5.3 (enum Status completo) | **Bloqueada por:** IT-5

- [x] `GET /tickets/stats` en `app/main.py` (declarado antes de `GET /tickets/{id}`)
- [x] JSON: `total`, `by_category`, `by_priority`, `by_status`
- [x] Conteos inicializados a 0 para todos los valores de enum (sin KeyError con BD vacía)

**Criterio de aceptación:** `GET /tickets/stats` → 200 JSON con las cuatro claves; `ruff` limpio; tests en verde.

---

## Dependencias entre iteraciones

```
IT-1 (modelos)
  └── IT-2 (clasificador)
        └── IT-3 (API REST)  ←── también depende de IT-1
              └── IT-4 (frontend)
                    └── IT-4.1 (persistencia de filtros en URL)
                          └── IT-5 (plazos + ciclo de vida)
                                ├── IT-6 (calidad y entrega)
                                └── IT-7 (estadísticas)  ← paralelo con IT-6
```
