---
description: Detecta la siguiente iteración desarrollable del BACKLOG, la fichea (rama + Draft PR) para notificar al equipo, la implementa end-to-end y la marca como completada dejando el PR listo para revisar.
allowed-tools: Bash(git switch:*), Bash(git pull:*), Bash(git fetch:*), Bash(git branch:*), Bash(git status:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(gh repo set-default:*), Bash(gh pr list:*), Bash(gh pr create:*), Bash(gh pr ready:*), Bash(gh pr view:*), Bash(pytest:*), Bash(ruff:*), Read, Edit, Write
---

# /detectar-siguiente-iteracion

Eres el coordinador autónomo de iteraciones de TriageBot. Ejecuta el proceso
**end-to-end**: detectar → fichar (notificar al equipo) → implementar → completar.
Trabajas en equipo sobre un repo compartido, así que **la verdad sobre qué está
cogido es el remoto**, no el `BACKLOG.md` local.

> ⚠️ **El repo es un fork** de `chill-voxway/triagebot-template`. TODOS los
> comandos `gh pr *` deben llevar `-R Ceballooss/triagebot-Grupo06` para que el
> PR sea interno a TU fork y NUNCA apunte al upstream.

Sigue las fases en orden. No te saltes el fichaje: hay que **notificar el inicio
de desarrollo desde el primer instante**, antes de escribir código de feature.

## Fase 0 — Sincronizar la verdad remota

1. Comprueba `git status`. Si el working tree está **sucio** o no estás en
   `main` → **DETENTE** e informa al usuario (no fiches encima de trabajo a
   medias). No continúes.
2. `gh repo set-default Ceballooss/triagebot-Grupo06`
3. `git switch main && git pull origin main`
4. `git fetch --prune origin`
5. `gh pr list -R Ceballooss/triagebot-Grupo06 --state open --json number,title,headRefName,isDraft`
6. Lista las ramas remotas con `git branch -r`.

## Fase 1 — Calcular el estado efectivo de cada iteración

Lee la tabla de estado global de `BACKLOG.md` y el `## Estado` de cada
`iteracion-0N.md`. Para cada IT-N determina el estado **efectivo**:

- **COMPLETADA** → ya desarrollada. Saltar.
- **EN PROGRESO**, o existe una rama remota `origin/feat/iteracion-0N*`, o hay un
  PR abierto cuyo `headRefName` empieza por `feat/iteracion-0N` → **la está
  haciendo otra persona del equipo. No tocar** (evitar colisión). Saltar.
- **PENDIENTE** y sin rama/PR remoto asociado → **candidata**.

## Fase 2 — Elegir la siguiente iteración desarrollable

De las candidatas, en orden ascendente de N:

- Mira el campo **"Depende de"** de sus historias en `BACKLOG.md`.
- Elige la **primera** candidata cuyas dependencias estén **todas COMPLETADA**.
- Si una candidata tiene dependencias sin cerrar → sáltala (no se puede empezar
  todavía).
- Si **no hay ninguna desarrollable** (todo completado, en progreso o bloqueado)
  → informa con un resumen del estado de cada iteración y **termina** sin fichar.

Anuncia al usuario qué iteración has elegido y por qué (qué dependencias cumple).

## Fase 3 — Fichar la iteración (notificar al equipo YA)

Esto ocurre **antes de escribir una sola línea de código de feature**:

1. `git switch -c feat/iteracion-0N-<slug-corto>` desde `main` actualizado.
2. Edita `BACKLOG.md`: en la tabla global pon IT-N → **EN PROGRESO** y actualiza
   la línea **"Iteración activa:"** a IT-N. (Respeta la regla: solo una
   iteración EN PROGRESO por persona a la vez.)
3. Edita `iteracion-0N.md`: `## Estado` → **EN PROGRESO**.
4. `git add -A && git commit -m "chore: reclamar iteración 0N (EN PROGRESO)"`
5. `git push -u origin feat/iteracion-0N-<slug-corto>`
6. `gh pr create -R Ceballooss/triagebot-Grupo06 --base main --head feat/iteracion-0N-<slug-corto> --draft --title "feat(IT-0N): <descripción>" --body "Fichaje automático de la iteración 0N. Implementación en curso."`

**Lock optimista:** si el `git push` se rechaza (non-fast-forward) o al re-listar
PRs/ramas aparece que otra persona acaba de fichar esa misma iteración →
**abandona el fichaje**, vuelve a `main`, re-ejecuta Fase 0–1 y elige otra
iteración. Nunca pises trabajo ajeno.

Confirma al usuario: rama creada + Draft PR abierto (con su URL). El equipo ya
está notificado.

## Fase 4 — Implementar la iteración end-to-end

1. Lee `iteracion-0N.md` completo (objetivo, solución propuesta, tareas, ficheros
   afectados, criterio de completado).
2. Implementa código y tests según la lista de tareas. **No modifiques
   `tests/test_acceptance.py`.**
3. Commits pequeños y frecuentes (Conventional Commits).
4. Ejecuta `ruff check .` y `pytest -v`. Itera hasta dejarlos en **verde**.

## Fase 5 — Completar y dejar el PR listo

1. Verifica el **criterio de completado** de la iteración (pytest verde, 0 fallos).
2. Edita `BACKLOG.md`: marca las tareas de la historia como `[x]`, pon IT-N →
   **COMPLETADA** en la tabla global y avanza/limpia "Iteración activa".
3. Edita `iteracion-0N.md`: `## Estado` → `COMPLETADA - <fecha de hoy>`.
4. `git add -A && git commit -m "docs: marcar iteración 0N como completada"`
   y `git push`.
5. `gh pr ready <num> -R Ceballooss/triagebot-Grupo06` (quita el estado Draft).
6. **NO mergees** a `main`. El merge lo hace otra persona del equipo tras review
   y CI verde.
7. Resumen final al usuario: iteración completada, qué se implementó, resultado
   de `pytest`, URL del PR, y aviso de que queda pendiente de revisión.
