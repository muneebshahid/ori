"""Tests for the default search tool scaffold."""

import pytest

import agent.tools.grep as grep_tool
from agent.tools.grep import grep


class RipgrepSelected(Exception):
    """Marker exception raised when the ripgrep stub is selected."""


class GrepSelected(Exception):
    """Marker exception raised when the grep stub is selected."""


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
async def test_grep_fn_prefers_ripgrep_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Call the ripgrep stub when rg exists."""

    monkeypatch.setattr(grep_tool.shutil, "which", _find_ripgrep_only)
    monkeypatch.setattr(grep_tool, "_run_ripgrep", _raise_ripgrep_selected)
    monkeypatch.setattr(grep_tool, "_run_grep", _raise_grep_selected)

    with pytest.raises(RipgrepSelected):
        await grep_tool.fn(pattern="needle")


@pytest.mark.asyncio
async def test_grep_fn_falls_back_to_grep_when_ripgrep_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Call the grep stub when rg is missing and grep exists."""

    monkeypatch.setattr(grep_tool.shutil, "which", _find_grep_only)
    monkeypatch.setattr(grep_tool, "_run_ripgrep", _raise_ripgrep_selected)
    monkeypatch.setattr(grep_tool, "_run_grep", _raise_grep_selected)

    with pytest.raises(GrepSelected):
        await grep_tool.fn(pattern="needle")


@pytest.mark.asyncio
async def test_grep_fn_raises_when_no_search_executable_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise a clear exception when neither rg nor grep exists."""

    monkeypatch.setattr(grep_tool.shutil, "which", _find_no_executables)

    with pytest.raises(RuntimeError, match="Neither ripgrep"):
        await grep_tool.fn(pattern="needle")


def _find_ripgrep_only(command: str) -> str | None:
    """Return an rg path only for ripgrep availability checks."""

    if command == "rg":
        return "/usr/bin/rg"
    return None


def _find_grep_only(command: str) -> str | None:
    """Return a grep path only for grep availability checks."""

    if command == "grep":
        return "/usr/bin/grep"
    return None


def _find_no_executables(command: str) -> None:
    """Return no executable path for all availability checks."""

    _ = command
    return None


async def _raise_ripgrep_selected(
    pattern: str,
    path: str,
    glob: str | None,
    ignore_case: bool,
    literal: bool,
    context: int,
    limit: int,
) -> None:
    """Raise the ripgrep selection marker."""

    _ = (pattern, path, glob, ignore_case, literal, context, limit)
    raise RipgrepSelected


async def _raise_grep_selected(
    pattern: str,
    path: str,
    glob: str | None,
    ignore_case: bool,
    literal: bool,
    context: int,
    limit: int,
) -> None:
    """Raise the grep selection marker."""

    _ = (pattern, path, glob, ignore_case, literal, context, limit)
    raise GrepSelected
