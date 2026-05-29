"""Unit tests for :mod:`app.report.model_catalog`."""

from __future__ import annotations

import pytest

from app.report.model_catalog import (
    ALLOWED_MODEL_IDS,
    AVAILABLE_MODELS,
    DEFAULT_MODEL_ID,
    resolve_model,
)


def test_resolve_model_empty_returns_default() -> None:
    """An empty string resolves to the server default model."""
    assert resolve_model("") == DEFAULT_MODEL_ID


def test_resolve_model_none_returns_default() -> None:
    """None resolves to the server default model."""
    assert resolve_model(None) == DEFAULT_MODEL_ID


def test_resolve_model_whitespace_returns_default() -> None:
    """Whitespace-only input resolves to the server default model."""
    assert resolve_model("   ") == DEFAULT_MODEL_ID


def test_resolve_model_known_returns_itself() -> None:
    """A known allowed model ID is returned unchanged."""
    assert resolve_model("claude-opus-4-8") == "claude-opus-4-8"


def test_resolve_model_unknown_raises() -> None:
    """An unknown model ID raises ValueError listing the allowed IDs."""
    with pytest.raises(ValueError, match="Unsupported model"):
        resolve_model("bogus")


def test_allowed_model_ids_has_three_entries() -> None:
    """The allow-list contains exactly the three catalog models."""
    assert len(ALLOWED_MODEL_IDS) == 3
    assert len(AVAILABLE_MODELS) == 3
    assert ALLOWED_MODEL_IDS == frozenset(opt.id for opt in AVAILABLE_MODELS)


def test_default_model_is_allowed() -> None:
    """The default model must itself be in the allow-list."""
    assert DEFAULT_MODEL_ID in ALLOWED_MODEL_IDS
