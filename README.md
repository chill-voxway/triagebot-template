# TriageBot Template

Repo plantilla para el bootcamp **Prompt & Commit: Desarrollo de aplicaciones con IA Generativa**.

Durante el bootcamp construiréis una aplicación web interna para clasificar tickets de soporte usando IA generativa.

## Qué vais a construir

TriageBot permite:

- Crear tickets con `title` y `description`.
- Clasificarlos automáticamente con Claude en:
  - `category`: `bug`, `feature_request`, `question`, `urgent`
  - `priority`: `P1`, `P2`, `P3`
  - `tags`: lista de etiquetas cortas.
- Persistirlos en SQLite.
- Verlos en un tablero web con filtros.
- Ejecutar tests automáticos y CI en GitHub Actions.

## Stack obligatorio

| Capa | Herramienta |
|---|---|
| Lenguaje | Python 3.12 (fijo, vía `PYTHON_BIN`) |
| Backend | FastAPI |
| Datos | SQLite |
| Frontend | HTML + HTMX + Tailwind CDN |
| LLM | `openai/gpt-oss-120b` vía OpenRouter |
| Tests | pytest |
| CI/CD | GitHub Actions |
| IDE + IA | VS Code + Claude Code |

## Setup local

> **Sin entornos virtuales.** Este proyecto usa **siempre Python 3.12** (no 3.10
> —le falta `datetime.UTC`— ni 3.14 —no instala el `pydantic-core` fijado sin
> Rust). El intérprete se referencia con la variable **`PYTHON_BIN`** definida en
> `.env.example` (valor por defecto `py -3.12` con el py launcher de Windows).

```bash
git clone https://github.com/<tu-usuario>/triagebot-template.git
cd triagebot-template
cp .env.example .env                       # incluye PYTHON_BIN=py -3.12
py -3.12 -m pip install -r requirements.txt
```

Edita `.env` y añade tu API key de OpenRouter:

```bash
OPENROUTER_API_KEY=sk-or-...
```

Comprueba que `.env` está ignorado por Git:

```bash
git status
```

`.env` **no debe aparecer**.

## Ejecutar tests

```bash
py -3.12 -m pytest -v          # equivale a "$PYTHON_BIN -m pytest -v"
```

Al clonar el repo plantilla, los tests de aceptación deben fallar. Eso es lo esperado: todavía no habéis implementado TriageBot.

## Ejecutar la app

```bash
py -3.12 -m uvicorn app.main:app --reload
```

Abre:

```text
http://127.0.0.1:8000
```

## Contrato mínimo del producto

Los detalles obligatorios están en:

- [`BRIEF.md`](BRIEF.md): briefing del cliente.
- [`SPEC.md`](SPEC.md): contrato funcional recomendado.
- [`CLAUDE.md`](CLAUDE.md): instrucciones del repo para Claude Code.
- [`tests/test_acceptance.py`](tests/test_acceptance.py): los 5 tests obligatorios.

## Reglas del bootcamp

1. Lo que no acaba en GitHub no existe.
2. No se commitean API keys.
3. Commit pequeño cada 20–30 minutos.
4. Leed el diff antes de aceptar cambios de la IA.
5. Si Claude propone una dependencia, verificad que existe antes de instalarla.
6. Los tests son la red de seguridad.

## Equipo

Nombres: Ceballos, Iker

Metodología: `Spec-Driven`
