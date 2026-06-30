"""API REST de TriageBot (`SPEC.md` §4).

Cuatro endpoints JSON sobre la entidad `Ticket`:
`POST /tickets`, `GET /tickets`, `GET /tickets/{id}`, `PATCH /tickets/{id}`.
La clasificación se delega en `app.classifier.classify_ticket`; el endpoint
nunca devuelve `5xx` por un fallo del LLM (fallback seguro).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
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
from app.models import Category, Priority, Status, Ticket, utcnow
from app.schemas import TicketCreate, TicketPatch


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


app = FastAPI(title="TriageBot", lifespan=lifespan)

# Plantillas Jinja2 (capa HTML/HTMX): el HTML vive en `templates/`, nunca como
# strings en este módulo (SPEC frontend §2).
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Alias de dependencia: evita llamar a `Depends` en defaults (ruff B008).
SessionDep = Annotated[Session, Depends(get_session)]


def _classify(title: str, description: str) -> dict:
    """Clasifica con blindaje: un fallo del LLM nunca propaga un `5xx`."""
    try:
        return classifier.classify_ticket(title, description)
    except Exception:
        return dict(FALLBACK_CLASSIFICATION)


def _filtered_tickets(
    session: Session,
    category: Category | None,
    priority: Priority | None,
    status_: Status | None,
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
    return list(session.exec(query).all())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets", response_model=Ticket, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, session: SessionDep) -> Ticket:
    """Valida, clasifica y persiste un ticket. Nunca `5xx` por fallo del LLM."""
    classification = _classify(payload.title, payload.description)
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
    return _filtered_tickets(session, category, priority, status)


# --------------------------------------------------------------------------- #
# Capa HTML / HTMX (SPEC frontend §5). Cada endpoint devuelve HTML, no JSON.   #
# Se declaran ANTES de `/tickets/{ticket_id}`: la ruta estática                #
# `/tickets/tablero` debe casar antes que la paramétrica (si no, FastAPI       #
# intenta parsear "tablero" como `int` y devuelve `422`).                      #
# HTMX reemplaza el contenido de `#tablero` (`hx-swap="innerHTML"`).           #
# --------------------------------------------------------------------------- #


def _render_tablero(
    request: Request,
    tickets: list[Ticket],
    error: str | None = None,
) -> HTMLResponse:
    """Renderiza el parcial reutilizable del tablero (filas o estado vacío)."""
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
) -> HTMLResponse:
    """Página única con filtros persistidos en la URL.

    Acepta query params opcionales (vacío = sin filtrar). Pasa `filtros` a la
    plantilla para marcar `selected` en los selects al recargar.
    """
    tickets = _filtered_tickets(
        session,
        _coerce_enum(Category, category),
        _coerce_enum(Priority, priority),
        _coerce_enum(Status, status),
    )
    filtros = {
        "category": category or None,
        "priority": priority or None,
        "status": status or None,
    }
    return templates.TemplateResponse(
        request, "index.html", {"tickets": tickets, "filtros": filtros}
    )


def _coerce_enum(enum_cls, value: str | None):
    """Convierte el valor de un filtro a su enum; vacío o inválido → `None`.

    Los `select` mandan `campo=` (string vacío) cuando se elige "Todos", así que
    no se puede tipar el query param como enum (daría `422`); se coacciona aquí.
    """
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
) -> HTMLResponse:
    """Fragmento del tablero filtrado por `category`/`priority`/`status` (vacío = todos)."""
    tickets = _filtered_tickets(
        session,
        _coerce_enum(Category, category),
        _coerce_enum(Priority, priority),
        _coerce_enum(Status, status),
    )
    return _render_tablero(request, tickets)


@app.post("/tickets/crear", response_class=HTMLResponse)
def crear_ticket_html(
    request: Request,
    session: SessionDep,
    title: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
) -> HTMLResponse:
    """Crea un ticket desde el formulario y devuelve el tablero refrescado.

    En error de validación devuelve el tablero con un mensaje, sin romper la
    página (nunca `5xx` ni pantalla en blanco).
    """
    try:
        payload = TicketCreate(title=title, description=description)
    except ValidationError:
        tickets = _filtered_tickets(session, None, None, None)
        return _render_tablero(
            request,
            tickets,
            error="Título y descripción son obligatorios.",
        )

    classification = _classify(payload.title, payload.description)
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
