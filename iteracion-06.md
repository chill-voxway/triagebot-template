# Iteración 6 - Calidad y entrega

## Objetivo
Dejar el proyecto entregable: los 5 tests de aceptación verdes, ruff limpio, CI
verde en GitHub Actions y README con instrucciones de arranque.

## Contexto
Última iteración. Depende de las Iteraciones 1–5 (toda la funcionalidad debe estar
implementada). Cierra los criterios de aceptación finales del `SPEC.md` §8.

## Solución propuesta
- Verificar `tests/test_acceptance.py` (intocable): los 5 pasan.
- `ruff check .` sin errores; corregir lint pendiente.
- `.github/workflows/ci.yml`: confirmar que ejecuta ruff + pytest en push/PR a
  `main` (ya existe; ajustar si hace falta) y añadir badge de estado.
- `README.md`: instrucciones de arranque (clonar, crear `.env` desde
  `.env.example`, `pip install -r requirements.txt`, `uvicorn app.main:app --reload`),
  prerequisitos (Python 3.11+).

## Tareas
- [ ] Los 5 tests de aceptación verdes (`pytest -v`)
- [ ] `ruff check .` limpio
- [ ] CI ejecuta ruff + pytest; badge en README
- [ ] README con arranque y prerequisitos

## Ficheros afectados
- `.github/workflows/ci.yml`
- `README.md`

## Criterio de completado
`pytest` pasa los 5 tests de aceptación, 0 fallos; `ruff check .` sin errores; CI
verde en el último commit del PR.

## Estado
PENDIENTE
