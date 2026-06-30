"""API REST de TriageBot (`SPEC.md` §4).

Cuatro endpoints JSON sobre la entidad `Ticket`:
`POST /tickets`, `GET /tickets`, `GET /tickets/{id}`, `PATCH /tickets/{id}`.
La clasificación se delega en `app.classifier.classify_ticket`; el endpoint
nunca devuelve `5xx` por un fallo del LLM (fallback seguro).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlmodel import Session, select

from app import classifier
from app.classifier import FALLBACK_CLASSIFICATION
from app.db import create_db_and_tables, get_session
from app.models import Category, Priority, Status, Ticket, utcnow
from app.schemas import TicketCreate, TicketPatch


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


app = FastAPI(title="TriageBot", lifespan=lifespan)

# Alias de dependencia: evita llamar a `Depends` en defaults (ruff B008).
SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets", response_model=Ticket, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, session: SessionDep) -> Ticket:
    """Valida, clasifica y persiste un ticket. Nunca `5xx` por fallo del LLM."""
    try:
        classification = classifier.classify_ticket(payload.title, payload.description)
    except Exception:
        # Blindaje: el clasificador ya da fallback, pero envolvemos por seguridad
        # para garantizar que un fallo del LLM nunca propague un 5xx.
        classification = dict(FALLBACK_CLASSIFICATION)

    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        category=classification["category"],
        priority=classification["priority"],
        tags=classification.get("tags", []),
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


@app.get("/tickets", response_model=list[Ticket])
def list_tickets(
    session: SessionDep,
    category: Category | None = None,
    priority: Priority | None = None,
    status: Status | None = None,
) -> list[Ticket]:
    """Lista tickets (más recientes primero) con filtros opcionales combinables."""
    query = select(Ticket)
    if category is not None:
        query = query.where(Ticket.category == category)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    if status is not None:
        query = query.where(Ticket.status == status)
    query = query.order_by(Ticket.created_at.desc())
    return list(session.exec(query).all())


@app.get("/tickets/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: int, session: SessionDep) -> Ticket:
    """Devuelve el ticket por id (`404` si no existe)."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    return ticket


@app.patch("/tickets/{ticket_id}", response_model=Ticket)
def patch_ticket(
    ticket_id: int,
    payload: TicketPatch,
    session: SessionDep,
) -> Ticket:
    """Actualiza solo `status` y/o `priority` (`404` si no existe, `422` si inválido)."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")

    if payload.status is not None:
        ticket.status = payload.status
    if payload.priority is not None:
        ticket.priority = payload.priority
    ticket.updated_at = utcnow()

    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket
