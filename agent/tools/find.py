"""File path search tool scaffold for the default agent."""

from ai.types.tools import ToolDefinition


async def fn(
    pattern: str,
    path: str = ".",
    limit: int = 1000,
) -> str:
    """Find file paths matching a glob pattern."""

    _ = (pattern, path, limit)
    raise NotImplementedError("find execution is not implemented yet.")


def _build_args(
    pattern: str,
    path: str,
    limit: int,
) -> list[str]:
    """Build command arguments for a file path search."""

    effective_limit = max(1, limit)
    args = [
        "--glob",
        "--color=never",
        "--hidden",
        "--no-require-git",
        "--max-results",
        str(effective_limit),
    ]

    effective_pattern = _build_effective_pattern(pattern)
    if _matches_full_path(pattern):
        args.append("--full-path")

    args.extend(["--", effective_pattern, path])
    return args


def _build_effective_pattern(pattern: str) -> str:
    """Return the pattern adjusted for fd full-path matching."""

    if not _matches_full_path(pattern) or pattern.startswith("**/"):
        return pattern

    if pattern.startswith("/"):
        return f"**{pattern}"

    return f"**/{pattern}"


def _matches_full_path(pattern: str) -> bool:
    """Return whether a glob pattern should match candidate paths."""

    return "/" in pattern


tool = ToolDefinition(
    name="find",
    description="Search for files by glob pattern.",
    input_schema={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "The glob pattern to match file paths, for example '*.py' or 'src/**/*.py'.",
            },
            "path": {
                "type": "string",
                "description": "The directory path to search. Defaults to the current directory.",
            },
            "limit": {
                "type": "integer",
                "description": "The maximum number of file paths to return. Defaults to 1000.",
            },
        },
        "required": ["pattern"],
        "additionalProperties": False,
    },
    fn=fn,
)
