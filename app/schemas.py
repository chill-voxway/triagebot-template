"""Esquemas de request de la API REST (`SPEC.md` §4).

Separan la validación de entrada del modelo ORM `Ticket`. Los límites de
longitud se aplican tras hacer `strip()` para rechazar entradas vacías o solo
con espacios (→ `422`).
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator

from app.models import Priority, Status

TITLE_MAX = 200
DESCRIPTION_MAX = 5000


class TicketCreate(BaseModel):
    """Payload de `POST /tickets`."""

    title: str
    description: str

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= TITLE_MAX:
            raise ValueError(f"`title` debe tener entre 1 y {TITLE_MAX} caracteres")
        return value

    @field_validator("description")
    @classmethod
    def _validate_description(cls, value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= DESCRIPTION_MAX:
            raise ValueError(
                f"`description` debe tener entre 1 y {DESCRIPTION_MAX} caracteres"
            )
        return value


class TicketPatch(BaseModel):
    """Payload de `PATCH /tickets/{id}`: solo `status` y/o `priority`.

    Los enums rechazan automáticamente valores fuera de lista (→ `422`).
    """

    status: Status | None = None
    priority: Priority | None = None
