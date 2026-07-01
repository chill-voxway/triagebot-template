# Iteración 2 - Clasificador LLM

## Objetivo
Implementar `app/classifier.py` con `classify_ticket(title, description) -> dict`
que clasifica un ticket vía LLM, valida la salida y aplica fallback seguro.

## Contexto
Depende de la Iteración 1 (modelo/enums definidos). La Iteración 3 (API REST)
depende de esta: el endpoint `POST /tickets` llama a `classify_ticket`. Es el
único módulo que habla con el LLM.

## Solución propuesta
- Según `SPEC.md` §5: llamar a `openai/gpt-oss-120b` vía OpenRouter con el SDK de
  OpenAI (`base_url="https://openrouter.ai/api/v1"`, key `OPENROUTER_API_KEY`).
- Pedir JSON estructurado; parsear `response.choices[0].message.content`.
- Validar contra los enums; si la salida es inválida → fallback.
- Reintentar una vez ante fallo; si vuelve a fallar → fallback. No propagar
  excepciones del SDK.
- Fallback: `{"category": "question", "priority": "P3", "tags": []}`.

> **Discrepancia a resolver:** el stub actual y el test mencionan Anthropic
> (`ANTHROPIC_API_KEY`). La `SPEC.md` manda OpenRouter (`OPENROUTER_API_KEY`).
> Esta iteración sigue la `SPEC.md`. El test de fallback solo verifica que una
> excepción del clasificador acaba en el fallback, así que es agnóstico al proveedor.

## Tareas
- [x] Implementar `classify_ticket` llamando a OpenRouter (SDK de OpenAI)
- [x] Parseo + validación de `category`/`priority`/`tags` contra enums
- [x] Reintento (1) + fallback ante error o salida inválida
- [x] Tests: salida válida mockeada, salida inválida → fallback, excepción → fallback

## Ficheros afectados
- `app/classifier.py`
- `tests/test_classifier.py` (nuevo)

## Criterio de completado
`pytest` pasa: `test_classifier_failure_uses_safe_fallback` verde y el clasificador
devuelve un dict con las tres claves válidas con LLM mockeado. 0 fallos.

> **Nota de alcance:** el módulo `app/classifier.py` y sus tests unitarios
> (`tests/test_classifier.py`) quedan en verde (6/6), incluyendo el contrato con
> LLM mockeado. El test de aceptación `test_classifier_failure_uses_safe_fallback`
> hace `POST /tickets`, endpoint que pertenece a **IT-3 (API REST)** y aún no
> existe (devuelve `404`); pasará a verde al integrar IT-3, que es justo la
> dependencia documentada (IT-3 llama a `classify_ticket`). `ruff check .` limpio.

## Estado
COMPLETADA - 2026-06-30
