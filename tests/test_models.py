"""Tests unitarios del modelo `Ticket` y la capa de persistencia (IT-1)."""

import pytest
from pydantic import ValidationError
from sqlmodel import Session, select


def test_models_import_without_error():
    """El módulo de modelos se importa sin errores y expone lo esperado."""
    from app.models import Category, Priority, Status, Ticket

    assert {c.value for c in Category} == {"bug", "feature_request", "question", "urgent"}
    assert {p.value for p in Priority} == {"P1", "P2", "P3"}
    assert {s.value for s in Status} == {"open", "in_progress", "resuelto", "closed"}
    assert Ticket is not None


def test_valid_ticket_has_defaults():
    """Un ticket válido toma `status=open` y timestamps UTC por defecto."""
    from app.models import Status, Ticket

    ticket = Ticket(
        title="La app no carga",
        description="Pantalla en blanco",
        category="bug",
        priority="P1",
    )

    assert ticket.status == Status.open
    assert ticket.tags == []
    assert ticket.created_at is not None
    assert ticket.updated_at is not None


@pytest.mark.parametrize(
    "field, value",
    [
        ("category", "URGENT"),
        ("category", "no-existe"),
        ("priority", "P4"),
        ("status", "abierto"),
    ],
)
def test_enums_reject_values_outside_the_list(field, value):
    """Los enums rechazan valores fuera de la lista (son vinculantes)."""
    from app.models import Ticket

    payload = {"title": "t", "description": "d", "category": "bug", "priority": "P1"}
    payload[field] = value

    with pytest.raises(ValidationError):
        Ticket.model_validate(payload)


def test_tags_limits_are_enforced():
    """Máx. 5 tags y máx. 30 caracteres por tag (SPEC §3)."""
    from app.models import Ticket

    base = {"title": "t", "description": "d", "category": "bug", "priority": "P1"}

    with pytest.raises(ValidationError):
        Ticket.model_validate({**base, "tags": [f"tag{i}" for i in range(6)]})

    with pytest.raises(ValidationError):
        Ticket.model_validate({**base, "tags": ["x" * 31]})


def test_create_db_and_tables_persists_with_database_url(tmp_path, monkeypatch):
    """`create_db_and_tables` usa `DATABASE_URL` y permite persistir tickets."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'models.db'}")

    # Re-importar db para que tome el engine con la nueva URL aislada.
    import importlib

    from app import db as db_module

    db_module = importlib.reload(db_module)
    db_module.create_db_and_tables()

    from app.models import Ticket

    with Session(db_module.engine) as session:
        session.add(
            Ticket(title="Persistido", description="ok", category="question", priority="P3")
        )
        session.commit()

    with Session(db_module.engine) as session:
        rows = session.exec(select(Ticket)).all()
        assert len(rows) == 1
        assert rows[0].title == "Persistido"
        assert rows[0].id is not None
