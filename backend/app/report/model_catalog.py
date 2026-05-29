"""Single source of truth for selectable Claude models and generation defaults.

The frontend reads :data:`AVAILABLE_MODELS`, :data:`DEFAULT_MODEL_ID`, and the
default system prompt through ``GET /api/v1/config`` (served as a
:class:`GenerationConfig`). The backend validates incoming ``model`` form values
against :data:`ALLOWED_MODEL_IDS` via :func:`resolve_model`.

Model IDs here are verified against the Anthropic docs and must not be changed
casually — the frozen settings contract (docs/superpowers/specs) depends on the
exact ``id`` / ``label`` / ``description`` shapes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = [
    "ModelOption",
    "AVAILABLE_MODELS",
    "ALLOWED_MODEL_IDS",
    "DEFAULT_MODEL_ID",
    "resolve_model",
    "GenerationConfig",
]


class ModelOption(BaseModel):
    """A single selectable model exposed to the frontend selector."""

    id: str = Field(..., description="Anthropic API model identifier.")
    label: str = Field(..., description="Human-friendly model name for the UI.")
    description: str = Field(
        ...,
        description="Short guidance on when to pick this model (speed/cost/quality).",
    )


# Ordered list — the frontend renders the selector in this exact order. IDs are
# verified against Anthropic docs; do not change them.
AVAILABLE_MODELS: list[ModelOption] = [
    ModelOption(
        id="claude-opus-4-8",
        label="Claude Opus 4.8",
        description=(
            "Most capable. Best for complex reasoning and nuanced reports. "
            "Slowest, highest cost. 1M context."
        ),
    ),
    ModelOption(
        id="claude-sonnet-4-6",
        label="Claude Sonnet 4.6",
        description="Balanced default. Strong quality with good speed. 1M context.",
    ),
    ModelOption(
        id="claude-haiku-4-5-20251001",
        label="Claude Haiku 4.5",
        description=(
            "Fastest and most economical. Great for quick drafts. 200k context."
        ),
    ),
]


# Derived from AVAILABLE_MODELS so the allow-list can never drift from the list
# the UI shows.
ALLOWED_MODEL_IDS: frozenset[str] = frozenset(option.id for option in AVAILABLE_MODELS)


# Server-side default when the caller omits a model (must be one of
# ALLOWED_MODEL_IDS).
DEFAULT_MODEL_ID: str = "claude-sonnet-4-6"


def resolve_model(model: str | None) -> str:
    """Resolve a caller-supplied model identifier to a validated model ID.

    - ``None``, the empty string, or whitespace-only input falls back to
      :data:`DEFAULT_MODEL_ID`.
    - A value present in :data:`ALLOWED_MODEL_IDS` is returned unchanged.
    - Any other value raises :class:`ValueError` listing the allowed IDs.
    """
    if model is None or not model.strip():
        return DEFAULT_MODEL_ID
    candidate = model.strip()
    if candidate in ALLOWED_MODEL_IDS:
        return candidate
    allowed = ", ".join(sorted(ALLOWED_MODEL_IDS))
    raise ValueError(
        f"Unsupported model '{candidate}'. Allowed models: {allowed}."
    )


class GenerationConfig(BaseModel):
    """Read-model served by ``GET /api/v1/config`` for the frontend UI."""

    models: list[ModelOption] = Field(
        ...,
        description="Selectable models, in display order.",
    )
    default_model: str = Field(
        ...,
        description="Model ID used when the caller does not choose one.",
    )
    default_system_prompt: str = Field(
        ...,
        description="The default system instructions, served verbatim for editing.",
    )
