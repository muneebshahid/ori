"""Tests for the default search tool scaffold."""

import pytest

import agent.tools.grep as grep_tool
from agent.tools.grep import grep


def test_grep_schema_requires_only_pattern() -> None:
    """Require only the search pattern so callers can omit optional controls."""

    assert grep.input_schema["required"] == ["pattern"]


def test_build_ripgrep_args_uses_default_search_flags() -> None:
    """Build the default ripgrep argv for machine-readable search output."""

    assert grep_tool._build_ripgrep_args(
        pattern="needle",
        path=".",
        glob=None,
        ignore_case=False,
        literal=False,
        context=0,
        limit=100,
    ) == [
        "--json",
        "--line-number",
        "--color=never",
        "--hidden",
        "--",
        "needle",
        ".",
    ]


def test_build_ripgrep_args_adds_optional_search_flags() -> None:
    """Build ripgrep argv from optional search controls."""

    assert grep_tool._build_ripgrep_args(
        pattern="needle",
        path="src",
        glob="**/*.py",
        ignore_case=True,
        literal=True,
        context=2,
        limit=25,
    ) == [
        "--json",
        "--line-number",
        "--color=never",
        "--hidden",
        "--ignore-case",
        "--fixed-strings",
        "--glob",
        "**/*.py",
        "--context",
        "2",
        "--",
        "needle",
        "src",
    ]


def test_build_ripgrep_args_protects_flag_like_patterns() -> None:
    """Place -- before the pattern so flag-like patterns stay search text."""

    assert grep_tool._build_ripgrep_args(
        pattern="--pre=payload",
        path=".",
        glob=None,
        ignore_case=False,
        literal=True,
        context=0,
        limit=100,
    )[-3:] == ["--", "--pre=payload", "."]


@pytest.mark.asyncio
async def test_grep_fn_builds_ripgrep_args_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reach the current no-op execution path when rg exists."""

    monkeypatch.setattr(grep_tool.shutil, "which", _find_ripgrep_only)

    assert await grep_tool.fn(pattern="needle") is None


@pytest.mark.asyncio
async def test_grep_fn_raises_when_ripgrep_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise a clear exception when rg is unavailable."""

    monkeypatch.setattr(grep_tool.shutil, "which", _find_no_executables)

    with pytest.raises(RuntimeError, match="ripgrep"):
        await grep_tool.fn(pattern="needle")


def _find_ripgrep_only(command: str) -> str | None:
    """Return an rg path only for ripgrep availability checks."""

    if command == "rg":
        return "/usr/bin/rg"
    return None


def _find_no_executables(command: str) -> None:
    """Return no executable path for all availability checks."""

    _ = command
    return None
