"""Capa de persistencia: engine SQLite y sesiones.

La URL de la base de datos se lee de `DATABASE_URL` (los tests la usan para
aislar la BD); por defecto un archivo local `triagebot.db` (SPEC §2).
"""

from __future__ import annotations

import os
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

# Importa los modelos para que queden registrados en `SQLModel.metadata`
# antes de crear las tablas.
from app import models  # noqa: F401

DEFAULT_DATABASE_URL = "sqlite:///triagebot.db"


def _database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def _make_engine():
    url = _database_url()
    # `check_same_thread=False` es necesario para usar SQLite con el
    # TestClient de FastAPI (varios hilos comparten la conexión).
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = _make_engine()


def create_db_and_tables() -> None:
    """Crea todas las tablas declaradas en los modelos SQLModel."""

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """Provee una sesión de base de datos (dependencia de FastAPI)."""

    with Session(engine) as session:
        yield session
