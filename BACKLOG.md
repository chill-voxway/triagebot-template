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
| [IT-4](#iteración-4) | Frontend | PENDIENTE |
| [IT-5](#iteración-5) | Calidad y entrega | PENDIENTE |

**Iteración activa:** — (ninguna EN PROGRESO; siguiente candidata: IT-4)

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

- [ ] Template Jinja2: formulario (`title`, `description`) + botón "Crear ticket"
- [ ] HTMX: `POST /tickets` refresca la lista sin recargar
- [ ] Tabla: `id`, `title`, `category` (badge color), `priority` (badge), `tags`, `status`, `created_at`
- [ ] Tres selects de filtro: `category`, `priority`, `status`

**Criterio de aceptación:** crear ticket desde navegador → aparece en tablero sin recarga de página.

---

## Épica 5 — Calidad y entrega

### Historia 5.1 — Tests verdes
**Iteración:** IT-5 | **Depende de:** H3.1–H3.4, H2.1 | **Bloqueada por:** IT-3

- [ ] Los 5 tests de `tests/test_acceptance.py` pasan (`pytest -v`)
- [ ] `ruff check .` sin errores

### Historia 5.2 — CI en GitHub Actions
**Iteración:** IT-5 | **Depende de:** H5.1 | **Bloqueada por:** H5.1

- [ ] Workflow `.github/workflows/ci.yml`: ruff + pytest en cada push a `main`
- [ ] Badge de estado en `README.md`

### Historia 5.3 — README
**Iteración:** IT-5 | **Depende de:** — | **Bloqueada por:** —

- [ ] Instrucciones de arranque: clonar, crear `.env`, `uvicorn app.main:app --reload`
- [ ] Prerequisitos: Python 3.11+, `pip install -r requirements.txt`

---

## Dependencias entre iteraciones

```
IT-1 (modelos)
  └── IT-2 (clasificador)
        └── IT-3 (API REST)  ←── también depende de IT-1
              └── IT-4 (frontend)
                    └── IT-5 (calidad y entrega)
```
