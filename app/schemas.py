"""Esquemas de request de la API REST (`SPEC.md` §4).

Separan la validación de entrada del modelo ORM `Ticket`. Los límites de
longitud se aplican tras hacer `strip()` para rechazar entradas vacías o solo
con espacios (→ `422`).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, field_validator

from app.models import Priority, Status

TITLE_MAX = 200
DESCRIPTION_MAX = 5000

# Bytes de control no imprimibles (excluye \t \n \r que son legítimos en texto).
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _check_chars(value: str, field: str) -> str:
    """Rechaza caracteres de control y bytes no UTF-8."""
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"`{field}` contiene caracteres no UTF-8") from exc
    if _CTRL_RE.search(value):
        raise ValueError(f"`{field}` contiene bytes de control no permitidos")
    return value


class TicketCreate(BaseModel):
    """Payload de `POST /tickets`."""

    title: str
    description: str

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        value = _check_chars(value.strip(), "title")
        if not 1 <= len(value) <= TITLE_MAX:
            raise ValueError(f"`title` debe tener entre 1 y {TITLE_MAX} caracteres")
        return value

    @field_validator("description")
    @classmethod
    def _validate_description(cls, value: str) -> str:
        value = _check_chars(value.strip(), "description")
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
