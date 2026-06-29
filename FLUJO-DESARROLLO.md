# Flujo de desarrollo automatizado — TriageBot

> Documento ejecutivo. Explica cómo el equipo desarrolla TriageBot de forma
> coordinada y autónoma mediante el comando `/detectar-siguiente-iteracion`.

---

## 1. El problema

Varias personas (y la IA) desarrollan el mismo proyecto en paralelo sobre un
repositorio compartido. Sin un mecanismo de coordinación aparecen tres riesgos:

- **Colisiones:** dos personas implementan la misma iteración a la vez.
- **Orden incorrecto:** se empieza una iteración antes de que estén listas las de
  las que depende.
- **Falta de visibilidad:** nadie sabe qué está cogido y qué está libre.

## 2. La solución en una frase

Un único comando — `/detectar-siguiente-iteracion` — que detecta la siguiente
pieza de trabajo libre, **avisa al equipo al instante**, la desarrolla de
principio a fin y la deja lista para revisar; todo de forma automática y sin
pisar el trabajo de nadie.

## 3. Las tres fuentes de verdad

| Documento | Rol |
|-----------|-----|
| `SPEC.md` | **Qué** se construye: contrato funcional del producto. |
| `BACKLOG.md` | **En qué orden**: épicas, historias, dependencias y estado de cada iteración. |
| `iteracion-XX.md` | **Cómo**: objetivo, solución técnica, tareas y criterio de "hecho" de cada iteración. |

El estado real de "quién está haciendo qué" **no vive en un fichero local**: vive
en GitHub (ramas y Pull Requests). Esa es la señal que todo el equipo comparte.

## 4. Cómo funciona — el ciclo en 5 pasos

```
   ┌─────────────────────────────────────────────────────────────┐
   │  /detectar-siguiente-iteracion                              │
   └─────────────────────────────────────────────────────────────┘
                              │
   ① SINCRONIZAR    Lee el estado real desde GitHub (ramas + PRs).
                              │
   ② DETECTAR       Clasifica cada iteración:
                       ✓ Completada  → ya está
                       ⏳ En progreso → la hace otra persona, no tocar
                       ○ Pendiente   → candidata
                              │
   ③ ELEGIR         Toma la primera pendiente cuyas dependencias
                    estén todas completadas. Si ninguna es viable,
                    informa y para.
                              │
   ④ FICHAR (¡YA!)  Crea rama + marca "EN PROGRESO" + abre Draft PR.
                    → El equipo queda notificado ANTES de escribir código.
                              │
   ⑤ DESARROLLAR    Implementa código y tests hasta dejar todo en verde,
      Y CERRAR       marca la iteración COMPLETADA y deja el PR listo
                    para revisar. NO mergea: revisa otra persona.
```

## 5. Garantías clave (por qué es seguro)

- **Notificación inmediata.** El "fichaje" (rama + Draft PR) ocurre *antes* de
  escribir una sola línea de funcionalidad. Nadie se entera tarde.
- **Sin colisiones.** Si una iteración ya tiene rama o PR abierto, se considera
  ocupada y se evita. Si dos personas fichan a la vez, gana quien sube primero;
  el otro reintenta con otra iteración (*lock optimista*).
- **Orden correcto garantizado.** Nunca se empieza una iteración cuyas
  dependencias no estén cerradas.
- **Calidad antes de entregar.** Una iteración solo se marca completada cuando
  `pytest` y `ruff` están en verde.
- **Control humano en el merge.** El comando deja el PR listo, pero **no lo
  fusiona**: siempre revisa otra persona del equipo antes de integrar a `main`.

## 6. Mecanismo técnico (resumen)

- **Plataforma:** Git + GitHub (`gh` CLI).
- **Unidad de trabajo:** una rama `feat/iteracion-XX` por iteración, con su Draft
  PR como señal de "en curso".
- **Estado compartido:** `BACKLOG.md` (tabla global + dependencias) refleja lo
  que muestran las ramas y PRs remotos.
- **Repositorio:** el proyecto es un *fork*; todos los PR se crean internos al
  fork del equipo (`Ceballooss/triagebot-Grupo06`), nunca contra el repo
  original del que se forkeó.

## 7. Valor para el equipo

- Cada integrante (o la IA) ejecuta **un solo comando** y obtiene trabajo útil,
  ordenado y sin conflictos.
- La coordinación deja de depender de mensajes manuales: el propio repositorio es
  el tablero.
- El proceso es **trazable**: cada iteración tiene su rama, su PR y su registro de
  estado en el `BACKLOG.md`.
