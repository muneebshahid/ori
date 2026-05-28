"""Tests for external executable availability helpers."""

import sys

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


@pytest.mark.asyncio
async def test_execute_returns_process_stdout() -> None:
    """Return captured stdout from a successful process."""

    result = await executables.execute(sys.executable, ["-c", "print('out')"])

    assert result == "out\n"


@pytest.mark.asyncio
async def test_execute_raises_on_disallowed_exit_code() -> None:
    """Raise stderr output when a process exits with a disallowed code."""

    with pytest.raises(RuntimeError, match="boom"):
        await executables.execute(
            sys.executable,
            ["-c", "import sys; print('boom', file=sys.stderr); sys.exit(2)"],
        )


@pytest.mark.asyncio
async def test_execute_allows_configured_exit_code() -> None:
    """Return stdout when a process exits with an explicitly allowed code."""

    result = await executables.execute(
        sys.executable,
        ["-c", "import sys; print('empty'); sys.exit(1)"],
        allowed_exit_codes=(0, 1),
    )

    assert result == "empty\n"


def _find_command(command: str) -> str | None:
    """Return a path for the ripgrep command only."""

    if command == "rg":
        return "/usr/bin/rg"
    return None


def _find_no_commands(command: str) -> None:
    """Return no command path for all availability checks."""

    _ = command
    return None
