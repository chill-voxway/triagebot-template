"""Modelo de dominio de TriageBot.

Define la entidad `Ticket` (SQLModel) y los enums vinculantes
de `category`, `priority` y `status` según `SPEC.md` §3.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum

from pydantic import field_validator
from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class Category(str, Enum):
    """Categorías permitidas para un ticket."""

    bug = "bug"
    feature_request = "feature_request"
    question = "question"
    urgent = "urgent"


class Priority(str, Enum):
    """Prioridades permitidas para un ticket."""

    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Status(str, Enum):
    """Estados permitidos para un ticket (IT-5: ciclo de vida ampliado)."""

    open = "open"
    in_progress = "in_progress"
    resuelto = "resuelto"
    closed = "closed"


# Estados que indican que el ticket ya está finalizado (no cuenta como vencido).
ESTADOS_FINALES = {Status.resuelto, Status.closed}

# Conjuntos derivados de los enums; útiles para validar la salida del
# clasificador (iteración 2) sin acoplarlo al modelo ORM.
ALLOWED_CATEGORIES = {c.value for c in Category}
ALLOWED_PRIORITIES = {p.value for p in Priority}
ALLOWED_STATUSES = {s.value for s in Status}

# Versión ordenada de los enums (según orden de definición); la usa el
# clasificador para construir el prompt de forma determinista y reproducible.
CATEGORY_VALUES = tuple(c.value for c in Category)
PRIORITY_VALUES = tuple(p.value for p in Priority)

# Límites de los tags (SPEC §3).
MAX_TAGS = 5
MAX_TAG_LENGTH = 30


def utcnow() -> datetime:
    """Timestamp UTC generado en servidor."""
    return datetime.now(UTC)


def _utcnow_naive() -> datetime:
    """UTC actual como datetime naive para comparar con valores de SQLite."""
    return datetime.now(UTC).replace(tzinfo=None)


def calcular_fecha_limite(priority: Priority) -> datetime:
    """Fecha límite (naive UTC) según prioridad.

    P1 -> EoD hoy · P2 -> EoD mañana · P3 -> EoD pasado mañana.
    Naive para compatibilidad con SQLite.
    """
    offsets = {Priority.P1: 0, Priority.P2: 1, Priority.P3: 2}
    target = (datetime.now(UTC) + timedelta(days=offsets[priority])).date()
    return datetime(target.year, target.month, target.day, 23, 59, 59)


class Ticket(SQLModel, table=True):
    """Incidencia de soporte clasificada por el LLM."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    category: Category
    priority: Priority
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: Status = Field(default=Status.open)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    # IT-5 TRABAJO 1: plazos y alertas
    fecha_limite: datetime | None = Field(default=None)
    # IT-5 TRABAJO 2: ciclo de vida
    fecha_cambio_estado: datetime | None = Field(default=None)

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: list[str]) -> list[str]:
        if len(value) > MAX_TAGS:
            raise ValueError(f"Como máximo {MAX_TAGS} tags por ticket")
        for tag in value:
            if not isinstance(tag, str):
                raise ValueError("Cada tag debe ser una cadena")
            if len(tag) > MAX_TAG_LENGTH:
                raise ValueError(f"Cada tag admite como máximo {MAX_TAG_LENGTH} caracteres")
        return value

    @property
    def esta_vencido(self) -> bool:
        """True si el ticket ha superado su fecha límite y no está finalizado."""
        if self.fecha_limite is None or self.status in ESTADOS_FINALES:
            return False
        fl = self.fecha_limite
        if fl.tzinfo:
            fl = fl.replace(tzinfo=None)
        return _utcnow_naive() > fl

    @property
    def tiempo_en_estado_actual(self) -> str:
        """Tiempo legible transcurrido desde el último cambio de estado."""
        ref = self.fecha_cambio_estado or self.created_at
        if ref is None:
            return "desconocido"
        ref_naive = ref.replace(tzinfo=None) if ref.tzinfo else ref
        secs = max(0, int((_utcnow_naive() - ref_naive).total_seconds()))
        if secs < 3600:
            mins = max(1, secs // 60)
            return f"{mins} min"
        elif secs < 86400:
            return f"{secs // 3600} h"
        else:
            days = secs // 86400
            return f"{days} {'día' if days == 1 else 'días'}"
