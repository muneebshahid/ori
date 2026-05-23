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

    if shutil.which("rg") is None:
        raise RuntimeError("ripgrep (rg) is not available.")

    _ = _build_ripgrep_args(pattern, path, glob, ignore_case, literal, context, limit)
    pass


def _build_ripgrep_args(
    pattern: str,
    path: str,
    glob: str | None,
    ignore_case: bool,
    literal: bool,
    context: int,
    limit: int,
) -> list[str]:
    """Build command arguments for a ripgrep search."""

    args = ["--json", "--line-number", "--color=never", "--hidden"]

    if ignore_case:
        args.append("--ignore-case")
    if literal:
        args.append("--fixed-strings")
    if glob:
        args.extend(["--glob", glob])
    if context > 0:
        args.extend(["--context", str(context)])

    _ = limit
    args.extend(["--", pattern, path])
    return args


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
