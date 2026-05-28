"""Tests for external executable availability helpers."""

import pytest

import agent.tools.executables as executables


def test_require_executable_returns_resolved_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the executable path when the command is available."""

    monkeypatch.setattr(executables.shutil, "which", _find_command)

    assert executables.require_executable("rg", "ripgrep (rg)") == "/usr/bin/rg"


def test_require_executable_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise a clear error when the command is unavailable."""

    monkeypatch.setattr(executables.shutil, "which", _find_no_commands)

    with pytest.raises(RuntimeError, match="ripgrep"):
        executables.require_executable("rg", "ripgrep (rg)")


def _find_command(command: str) -> str | None:
    """Return a path for the ripgrep command only."""

    if command == "rg":
        return "/usr/bin/rg"
    return None


def _find_no_commands(command: str) -> None:
    """Return no command path for all availability checks."""

    _ = command
    return None
