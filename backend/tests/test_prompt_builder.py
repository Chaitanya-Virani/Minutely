"""Unit tests for :mod:`app.report.prompt_builder`.

Focused on the injectable system-instructions behaviour of ``build_system``.
"""

from __future__ import annotations

from app.report.prompt_builder import SYSTEM_INSTRUCTIONS, build_system


def _system_texts(blocks: list[dict[str, object]]) -> list[str]:
    """Extract the ``text`` field from each system content block."""
    return [str(block["text"]) for block in blocks]


def test_build_system_default_uses_system_instructions() -> None:
    """With no override, the first block carries the default instructions."""
    blocks = build_system(my_context="MY CTX")
    texts = _system_texts(blocks)
    assert texts[0] == SYSTEM_INSTRUCTIONS
    assert "MY CTX" in texts[1]


def test_build_system_custom_instructions_replace_default() -> None:
    """A non-blank override appears in the system blocks; default does not."""
    blocks = build_system(my_context="MY CTX", system_instructions="CUSTOM XYZ")
    texts = _system_texts(blocks)
    assert "CUSTOM XYZ" in texts[0]
    assert SYSTEM_INSTRUCTIONS not in texts


def test_build_system_whitespace_falls_back_to_default() -> None:
    """Whitespace-only override falls back to the default instructions."""
    blocks = build_system(my_context="MY CTX", system_instructions="   ")
    texts = _system_texts(blocks)
    assert texts[0] == SYSTEM_INSTRUCTIONS


def test_build_system_none_falls_back_to_default() -> None:
    """Explicit None override falls back to the default instructions."""
    blocks = build_system(my_context="MY CTX", system_instructions=None)
    texts = _system_texts(blocks)
    assert texts[0] == SYSTEM_INSTRUCTIONS
