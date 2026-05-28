"""External executable availability helpers for built-in tools."""

import shutil


def require_executable(command: str, display_name: str) -> str:
    """Return an executable path or raise a clear tool availability error."""

    executable = shutil.which(command)
    if executable is None:
        raise RuntimeError(f"{display_name} is not available.")
    return executable
