"""Search tool scaffold for the default agent."""

import shutil

from ai.types.tools import ToolDefinition


async def fn(
    pattern: str,
    path: str = ".",
    glob: str | None = None,
    ignore_case: bool = False,
    literal: bool = False,
    context: int = 0,
    limit: int = 100,
) -> None:
    """Search file contents for a pattern."""

    if shutil.which("rg") is not None:
        await _run_ripgrep(pattern, path, glob, ignore_case, literal, context, limit)
        return

    if shutil.which("grep") is not None:
        await _run_grep(pattern, path, glob, ignore_case, literal, context, limit)
        return

    raise RuntimeError("Neither ripgrep (rg) nor grep is available.")


async def _run_ripgrep(
    pattern: str,
    path: str,
    glob: str | None,
    ignore_case: bool,
    literal: bool,
    context: int,
    limit: int,
) -> None:
    """Run the future ripgrep-backed search implementation."""

    _ = (pattern, path, glob, ignore_case, literal, context, limit)
    pass


async def _run_grep(
    pattern: str,
    path: str,
    glob: str | None,
    ignore_case: bool,
    literal: bool,
    context: int,
    limit: int,
) -> None:
    """Run the future grep-backed search implementation."""

    _ = (pattern, path, glob, ignore_case, literal, context, limit)
    pass


grep = ToolDefinition(
    name="grep",
    description="Search file contents for a pattern.",
    input_schema={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "The search pattern to find. Treated as a regular expression unless literal is true.",
            },
            "path": {
                "type": "string",
                "description": "The file or directory path to search. Defaults to the current directory.",
            },
            "glob": {
                "type": "string",
                "description": "Filter searched files by glob pattern, for example '*.py' or '**/*_test.py'.",
            },
            "ignore_case": {
                "type": "boolean",
                "description": "Whether to search case-insensitively. Defaults to false.",
            },
            "literal": {
                "type": "boolean",
                "description": "Whether to treat the pattern as a literal string instead of a regular expression. Defaults to false.",
            },
            "context": {
                "type": "integer",
                "description": "The number of lines to include before and after each match. Defaults to 0.",
            },
            "limit": {
                "type": "integer",
                "description": "The maximum number of matches to return. Defaults to 100.",
            },
        },
        "required": ["pattern"],
        "additionalProperties": False,
    },
    fn=fn,
)
