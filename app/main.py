"""API REST de TriageBot (`SPEC.md` §4).

Cuatro endpoints JSON sobre la entidad `Ticket`:
`POST /tickets`, `GET /tickets`, `GET /tickets/{id}`, `PATCH /tickets/{id}`.
La clasificación se delega en `app.classifier.classify_ticket`; el endpoint
nunca devuelve `5xx` por un fallo del LLM (fallback seguro).
"""

from __future__ import annotations

import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlmodel import Session, select

from app import classifier
from app.classifier import FALLBACK_CLASSIFICATION
from app.db import create_db_and_tables, get_session
from app.models import (
    Category,
    Priority,
    Status,
    Ticket,
    calcular_fecha_limite,
    utcnow,
)
from app.schemas import TicketCreate, TicketPatch

# Lock que serializa las creaciones de tickets para evitar duplicados concurrentes.
_ticket_lock = threading.Lock()

# Ventana de tiempo para detectar envíos duplicados (segundos).
_DUPLICATE_WINDOW = 10


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


app = FastAPI(title="TriageBot", lifespan=lifespan)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

SessionDep = Annotated[Session, Depends(get_session)]


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _classify(title: str, description: str) -> dict:
    """Clasifica con blindaje total: un fallo del LLM nunca propaga un `5xx`."""
    try:
        return classifier.classify_ticket(title, description)
    except Exception:
        return dict(FALLBACK_CLASSIFICATION)


def _classify_html(title: str, description: str) -> tuple[dict, bool]:
    """Clasifica y señaliza si el LLM falló (para mostrar 'LLM ERROR' en UI)."""
    try:
        return classifier.classify_ticket(title, description), False
    except Exception:
        return dict(FALLBACK_CLASSIFICATION), True


def _es_duplicado(session: Session, title: str, description: str) -> bool:
    """True si existe un ticket idéntico creado en los últimos _DUPLICATE_WINDOW s."""
    cutoff = (datetime.now(UTC) - timedelta(seconds=_DUPLICATE_WINDOW)).replace(tzinfo=None)
    query = (
        select(Ticket)
        .where(Ticket.title == title)
        .where(Ticket.description == description)
        .where(Ticket.created_at >= cutoff)
    )
    return session.exec(query).first() is not None


def _filtered_tickets(
    session: Session,
    category: Category | None,
    priority: Priority | None,
    status_: Status | None,
    vencidos: bool = False,
) -> list[Ticket]:
    """Tickets más recientes primero, con filtros opcionales combinables."""
    query = select(Ticket)
    if category is not None:
        query = query.where(Ticket.category == category)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    if status_ is not None:
        query = query.where(Ticket.status == status_)
    query = query.order_by(Ticket.created_at.desc())
    tickets = list(session.exec(query).all())
    if vencidos:
        tickets = [t for t in tickets if t.esta_vencido]
    return tickets


# ---------------------------------------------------------------------------
# Endpoints JSON
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets", response_model=Ticket, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, session: SessionDep) -> Ticket:
    """Valida, clasifica y persiste un ticket. Nunca `5xx` por fallo del LLM."""
    with _ticket_lock:
        if _es_duplicado(session, payload.title, payload.description):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ticket duplicado: ya existe uno idéntico enviado recientemente.",
            )
        classification = _classify(payload.title, payload.description)
        priority = Priority(classification["priority"])
        now = utcnow()
        ticket = Ticket(
            title=payload.title,
            description=payload.description,
            category=classification["category"],
            priority=priority,
            tags=classification.get("tags", []),
            fecha_limite=calcular_fecha_limite(priority),
            fecha_cambio_estado=now,
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
    vencidos: bool = False,
) -> list[Ticket]:
    """Lista tickets (más recientes primero) con filtros opcionales combinables."""
    return _filtered_tickets(session, category, priority, status, vencidos)


# ---------------------------------------------------------------------------
# Capa HTML / HTMX
# ---------------------------------------------------------------------------

def _render_tablero(
    request: Request,
    tickets: list[Ticket],
    error: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "_tickets_table.html",
        {"tickets": tickets, "error": error},
    )


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    session: SessionDep,
    category: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    vencidos: str | None = None,
) -> HTMLResponse:
    """Página única con filtros persistidos en la URL."""
    vencidos_bool = vencidos == "true"
    tickets = _filtered_tickets(
        session,
        _coerce_enum(Category, category),
        _coerce_enum(Priority, priority),
        _coerce_enum(Status, status),
        vencidos_bool,
    )
    filtros = {
        "category": category or None,
        "priority": priority or None,
        "status": status or None,
        "vencidos": "true" if vencidos_bool else None,
    }
    return templates.TemplateResponse(
        request, "index.html", {"tickets": tickets, "filtros": filtros}
    )


def _coerce_enum(enum_cls, value: str | None):
    """Convierte el valor de un filtro a su enum; vacío o inválido -> `None`."""
    if not value:
        return None
    try:
        return enum_cls(value)
    except ValueError:
        return None


@app.get("/tickets/tablero", response_class=HTMLResponse)
def tablero(
    request: Request,
    session: SessionDep,
    category: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    vencidos: str | None = None,
) -> HTMLResponse:
    tickets = _filtered_tickets(
        session,
        _coerce_enum(Category, category),
        _coerce_enum(Priority, priority),
        _coerce_enum(Status, status),
        vencidos == "true",
    )
    return _render_tablero(request, tickets)


@app.post("/tickets/crear", response_class=HTMLResponse)
def crear_ticket_html(
    request: Request,
    session: SessionDep,
    title: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
) -> HTMLResponse:
    """Crea un ticket desde el formulario y devuelve el tablero refrescado."""
    try:
        payload = TicketCreate(title=title, description=description)
    except ValidationError:
        tickets = _filtered_tickets(session, None, None, None)
        return _render_tablero(
            request, tickets, error="Título y descripción son obligatorios."
        )

    with _ticket_lock:
        if _es_duplicado(session, payload.title, payload.description):
            tickets = _filtered_tickets(session, None, None, None)
            return _render_tablero(
                request,
                tickets,
                error="Ticket duplicado: ya enviaste uno idéntico hace menos de 10 segundos.",
            )

        classification, llm_error = _classify_html(payload.title, payload.description)
        priority = Priority(classification["priority"])
        now = utcnow()
        ticket = Ticket(
            title=payload.title,
            description=payload.description,
            category=classification["category"],
            priority=priority,
            tags=classification.get("tags", []),
            fecha_limite=calcular_fecha_limite(priority),
            fecha_cambio_estado=now,
        )
        session.add(ticket)
        session.commit()
        session.refresh(ticket)

    tickets = _filtered_tickets(session, None, None, None)
    return _render_tablero(
        request,
        tickets,
        error="LLM ERROR" if llm_error else None,
    )


@app.post("/tickets/{ticket_id}/transicion", response_class=HTMLResponse)
def transicion_ticket(
    ticket_id: int,
    request: Request,
    session: SessionDep,
    nuevo_estado: Annotated[str, Form()],
) -> HTMLResponse:
    """Cambia el estado del ticket vía botón HTMX y devuelve el tablero."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is not None:
        nuevo_status = _coerce_enum(Status, nuevo_estado)
        if nuevo_status is not None:
            ticket.status = nuevo_status
            ticket.fecha_cambio_estado = utcnow()
            ticket.updated_at = utcnow()
            session.add(ticket)
            session.commit()
    tickets = _filtered_tickets(session, None, None, None)
    return _render_tablero(request, tickets)


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
    """Actualiza `status` y/o `priority` (`404` si no existe, `422` si inválido)."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")

    if payload.status is not None:
        ticket.status = payload.status
        ticket.fecha_cambio_estado = utcnow()
    if payload.priority is not None:
        ticket.priority = payload.priority
    ticket.updated_at = utcnow()

    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket
