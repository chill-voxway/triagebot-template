"""Tests del clasificador LLM (`app/classifier.py`).

El LLM se mockea sustituyendo `app.classifier.OpenAI` por un cliente falso, de
modo que no se hace ninguna llamada de red. Se cubren: salida válida, salida
inválida → fallback, excepción → fallback, reintento y saneamiento de tags.
"""

import json
from types import SimpleNamespace

import pytest

from app import classifier
from app.classifier import (
    FALLBACK_CLASSIFICATION,
    build_system_prompt,
    build_user_prompt,
    classify_ticket,
)
from app.models import (
    ALLOWED_CATEGORIES,
    ALLOWED_PRIORITIES,
    MAX_TAG_LENGTH,
    MAX_TAGS,
    Category,
    Priority,
)


def _make_response(content):
    """Construye un objeto con la forma `response.choices[0].message.content`."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class _FakeClient:
    """Cliente OpenAI falso: reproduce una secuencia de comportamientos.

    Cada elemento de `behaviors` es o bien un string (contenido a devolver) o
    bien una excepción a lanzar en esa llamada.
    """

    def __init__(self, behaviors):
        self._behaviors = list(behaviors)
        self.calls = 0
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        behavior = self._behaviors[self.calls]
        self.calls += 1
        if isinstance(behavior, Exception):
            raise behavior
        return _make_response(behavior)


@pytest.fixture()
def fake_openai(monkeypatch):
    """Devuelve un setter que instala un `_FakeClient` con los comportamientos dados."""

    def _install(behaviors):
        client = _FakeClient(behaviors)
        monkeypatch.setattr(classifier, "OpenAI", lambda **kwargs: client)
        return client

    return _install


def test_valid_output_returns_contract_dict(fake_openai):
    fake_openai([json.dumps({"category": "bug", "priority": "P1", "tags": ["login"]})])

    result = classify_ticket("La app no carga", "Pantalla en blanco al entrar")

    assert set(result.keys()) == {"category", "priority", "tags"}
    assert result["category"] in ALLOWED_CATEGORIES
    assert result["priority"] in ALLOWED_PRIORITIES
    assert result["tags"] == ["login"]


def test_invalid_category_uses_fallback(fake_openai):
    # "URGENT" en mayúsculas no está en los enums → ambos intentos inválidos.
    payload = json.dumps({"category": "URGENT", "priority": "P1", "tags": []})
    fake_openai([payload, payload])

    result = classify_ticket("título", "descripción")

    assert result == FALLBACK_CLASSIFICATION


def test_non_json_output_uses_fallback(fake_openai):
    fake_openai(["esto no es JSON", "tampoco esto"])

    result = classify_ticket("título", "descripción")

    assert result == FALLBACK_CLASSIFICATION


def test_sdk_exception_uses_fallback(fake_openai):
    fake_openai([RuntimeError("OpenRouter caído"), RuntimeError("otra vez")])

    result = classify_ticket("título", "descripción")

    assert result == FALLBACK_CLASSIFICATION


def test_retries_once_then_succeeds(fake_openai):
    valid = json.dumps({"category": "question", "priority": "P3", "tags": []})
    client = fake_openai([RuntimeError("fallo transitorio"), valid])

    result = classify_ticket("título", "descripción")

    assert client.calls == 2
    assert result["category"] == "question"


def test_tags_are_sanitized(fake_openai):
    payload = json.dumps(
        {
            "category": "feature_request",
            "priority": "P2",
            "tags": ["a" * 50, "ok", 123, "  ", "x", "y", "z", "w"],
        }
    )
    fake_openai([payload])

    result = classify_ticket("título", "descripción")

    assert len(result["tags"]) <= 5
    assert all(isinstance(t, str) and len(t) <= 30 for t in result["tags"])
    assert result["tags"][0] == "a" * 30  # recortado a MAX_TAG_LENGTH


# --- Prompt parametrizado: guard anti-drift entre enums y prompt ---


def test_system_prompt_lists_every_category():
    prompt = build_system_prompt()
    for category in Category:
        assert category.value in prompt


def test_system_prompt_lists_every_priority():
    prompt = build_system_prompt()
    for priority in Priority:
        assert priority.value in prompt


def test_system_prompt_reflects_tag_limits():
    prompt = build_system_prompt()
    assert str(MAX_TAGS) in prompt
    assert str(MAX_TAG_LENGTH) in prompt


def test_build_user_prompt_includes_title_and_description():
    # Formato de entrada del ticket (campos de seed_tickets.json).
    message = build_user_prompt("La VPN rechaza al equipo", "Sale authentication failed")

    assert "La VPN rechaza al equipo" in message
    assert "Sale authentication failed" in message
