# CLAUDE.md

> **Equipo B (Spec-Driven):** este archivo es vuestro. Completadlo con vuestras
> convenciones como parte del trabajo de hoy — es tan importante como el `SPEC.md`
> que vais a escribir. Claude Code lo lee automáticamente al abrir el repo.
>
> **Equipo A (Vibe):** podéis ignorarlo. No estáis obligados a tocarlo.

Este repo es una plantilla docente para construir **TriageBot**, una aplicación
FastAPI que clasifica tickets de soporte con un LLM (gpt-oss-120b vía OpenRouter).

## Stack (innegociable)

- Python 3.11+
- FastAPI
- SQLite
- HTMX + Jinja2
- Tailwind (por CDN)
- SDK de OpenAI (apuntado a OpenRouter)
- pytest
- ruff

## Reglas del taller (para todos los equipos)

Estas reglas no son metodología: son condiciones del bootcamp. Se cumplen seas
del equipo que seas.

1. No modifiques `tests/test_acceptance.py` salvo que el profesor lo indique
   expresamente.
2. Nunca hardcodees una API key en el código.
3. Lee la API key desde la variable de entorno `OPENROUTER_API_KEY`.
4. `.env` nunca se commitea. Comprueba que está en `.gitignore` antes de tu
   primer commit.

## Comandos útiles

```bash
pytest -v
pytest --cov=app
ruff check .
uvicorn app.main:app --reload
```

## Política de ramas (Git workflow)

Estas reglas aplican a todo el equipo y a Claude Code. **Objetivo: `main` siempre
estable y desplegable.**

### Reglas

1. **Nunca commitees ni hagas push directamente sobre `main`.** Todo cambio entra
   vía Pull Request.
2. **Una rama por tarea.** Cada feature, fix o cambio vive en su propia rama; no
   acumules trabajo sin relación en la misma rama.
3. **Parte siempre de `main` actualizado:**
   ```bash
   git switch main && git pull origin main
   git switch -c <tipo>/<descripcion-corta>
   ```
4. **Convención de nombres:** `<tipo>/<descripcion-en-kebab-case>`, corta y
   descriptiva. Tipos permitidos:
   | Prefijo | Uso |
   |---|---|
   | `feat/` | Nueva funcionalidad |
   | `fix/` | Corrección de bug |
   | `docs/` | Documentación |
   | `refactor/` | Refactor sin cambio de comportamiento |
   | `test/` | Solo tests |
   | `chore/` | Mantenimiento, config, dependencias |

   Ejemplos: `feat/post-tickets`, `fix/validacion-titulo`, `docs/nombre-iker`.
5. **Commits pequeños y frecuentes** (cada 20–30 min), con mensajes en formato
   Conventional Commits: `<tipo>: <descripción en imperativo>`.
6. **Sincroniza con `main` a menudo** para evitar conflictos grandes:
   `git switch main && git pull` y luego `git merge main` (o rebase) en tu rama.
7. **Abre el PR contra `main`.** No se mergea hasta que:
   - la CI esté en verde (ruff + pytest), y
   - al menos otra persona del equipo lo haya revisado.
8. **No fuerces el push** (`--force`) sobre ramas compartidas. Si necesitas
   reescribir historia, usa `--force-with-lease` y solo en tu rama propia.
9. **Borra la rama tras el merge:**
   ```bash
   git switch main && git pull
   git branch -d <rama>
   ```

### Comandos del flujo

```bash
git switch -c feat/mi-tarea          # 1. crear rama desde main actualizado
git add . && git commit -m "feat: ..."  # 2. commits pequeños
git push -u origin feat/mi-tarea     # 3. subir la rama
gh pr create --base main --fill      # 4. abrir PR
# 5. CI verde + review -> merge en GitHub -> borrar rama
```

## Protocolo de inicio de sesión

Antes de escribir cualquier línea de código, Claude Code sigue estos pasos:

1. Leer este fichero completo.
2. Leer `BACKLOG.md` → identificar la iteración activa.
3. Leer `iteracion-[ITER].md` → objetivo y criterio de completado.

`BACKLOG.md` contiene épicas, historias y tareas con criterios de aceptación verificables (estilo Scrum). Se actualiza continuamente y absorbe los cambios de alcance.

Cada `iteracion-XX.md` documenta: objetivo, contexto, solución propuesta, tareas, ficheros afectados, criterio de completado y estado.

## Lógica de modificación del BACKLOG.md

Estas reglas dictan cuándo y cómo Claude Code debe editar `BACKLOG.md`.

### Cuándo modificarlo

| Evento | Qué actualizar |
|--------|---------------|
| Se completa una tarea | Marcar `[ ]` → `[x]` en la historia correspondiente |
| Se completa una historia | Marcar todas sus tareas `[x]`; actualizar estado de iteración en la tabla global si procede |
| Cambia la iteración activa | Actualizar la línea `**Iteración activa:**` y el estado en la tabla global (PENDIENTE → EN PROGRESO → COMPLETADA) |
| Se descubre una nueva tarea | Añadirla bajo la historia correcta con `[ ]`; si afecta dependencias, actualizar los campos "Depende de" / "Bloqueada por" |
| Cambia el alcance | Añadir/modificar/eliminar historias; nunca borrar historial completado, marcar como `~~tachado~~` si se descarta |
| Se crea una iteración nueva | Añadir fila a la tabla global y crear el fichero `iteracion-XX.md` correspondiente |

### Reglas de integridad

1. **No reordenar épicas** sin motivo: el orden refleja dependencias de implementación.
2. **Actualizar siempre el grafo de dependencias** al final del fichero si se añaden o eliminan historias.
3. **Una historia bloqueada no se marca EN PROGRESO** hasta que su bloqueo esté resuelto.
4. **El campo "Iteración activa" debe coincidir** con el estado EN PROGRESO de la tabla global. Solo una iteración puede estar EN PROGRESO al mismo tiempo.
5. **No modificar criterios de aceptación** de historias ya completadas; si cambian, crear una historia nueva.

## Comando `/detectar-siguiente-iteracion` y protocolo de fichaje

Comando autónomo (`.claude/commands/detectar-siguiente-iteracion.md`) que lleva
una iteración **end-to-end**: detectar → fichar → implementar → completar.
Trabajamos en equipo, así que estas reglas evitan colisiones:

1. **La verdad del fichaje es el remoto, no el `BACKLOG.md` local.** Una
   iteración está "cogida" si tiene una rama remota `feat/iteracion-XX` o un PR
   abierto. Antes de decidir nada, el comando hace `git fetch` + `gh pr list`.
2. **Notificar desde el primer instante.** Al elegir iteración, lo primero (antes
   de tocar código de feature) es crear la rama, marcar `EN PROGRESO` en
   `BACKLOG.md` + `iteracion-XX.md`, commitear, **push** y abrir un **Draft PR**.
   Ese Draft PR es la señal que ve el resto del equipo.
3. **Respeta dependencias.** Solo se ficha una iteración PENDIENTE cuyas
   dependencias ("Depende de" en el `BACKLOG.md`) estén todas COMPLETADA.
4. **Lock optimista.** Si el `push` del fichaje se rechaza (alguien fichó antes)
   → re-fetch y elegir otra iteración. Nunca pisar trabajo ajeno.
5. **Una sola iteración EN PROGRESO por persona.**
6. **El comando nunca mergea a `main`.** Al completar, marca `COMPLETADA - fecha`
   y deja el PR `ready`; el merge lo hace otra persona tras review (política de
   ramas).
7. **El repo es un fork de `chill-voxway/triagebot-template`.** Todos los
   `gh pr create|list|ready` llevan `-R Ceballooss/triagebot-Grupo06` (y se fija
   `gh repo set-default Ceballooss/triagebot-Grupo06`) para que los PR queden
   **internos al fork** y NUNCA apunten al upstream.
