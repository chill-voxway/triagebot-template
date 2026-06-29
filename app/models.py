"""Modelo de dominio de TriageBot.

Define la entidad `Ticket` (SQLModel, tabla SQLite) y los enums vinculantes
de `category`, `priority` y `status` según `SPEC.md` §3.
"""

from __future__ import annotations

from datetime import UTC, datetime
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
    """Estados permitidos para un ticket."""

    open = "open"
    in_progress = "in_progress"
    closed = "closed"


# Conjuntos derivados de los enums; útiles para validar la salida del
# clasificador (iteración 2) sin acoplarlo al modelo ORM.
ALLOWED_CATEGORIES = {c.value for c in Category}
ALLOWED_PRIORITIES = {p.value for p in Priority}
ALLOWED_STATUSES = {s.value for s in Status}

# Límites de los tags (SPEC §3).
MAX_TAGS = 5
MAX_TAG_LENGTH = 30


def utcnow() -> datetime:
    """Timestamp UTC generado en servidor."""

    return datetime.now(UTC)


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
