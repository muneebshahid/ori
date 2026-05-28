"""Directory listing tool for the default agent."""

import asyncio
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from ai.types.tools import ToolDefinition

from agent.tools.truncation import OUTPUT_BYTE_LIMIT_LABEL, truncate_to_byte_limit


class Results(BaseModel):
    """Structured directory listing results returned by the ls tool."""

    entries: list[str]
    truncated: bool


async def fn(path: str = ".", limit: int = 500) -> str:
    """List the contents of a directory."""

    output = await _execute(path)
    results = _parse_output(output, limit)
    return _format_results(results, limit)


async def _execute(path: str) -> list[str]:
    """List directory entries asynchronously."""

    return await asyncio.to_thread(_list_directory_entries, path)


def _parse_output(output: Sequence[str], limit: int) -> Results:
    """Apply the entry limit to raw directory entries."""

    return Results(entries=list(output[:limit]), truncated=len(output) > limit)


def _format_results(results: Results, limit: int) -> str:
    """Format directory listing results as compact plain text."""

    if not results.entries:
        return "(empty directory)"

    result = "\n".join(results.entries)
    result, byte_limit_reached = truncate_to_byte_limit(result)

    notices: list[str] = []
    if results.truncated:
        notices.append(f"{limit} entries limit reached. Use limit={limit * 2} for more")
    if byte_limit_reached:
        notices.append(f"{OUTPUT_BYTE_LIMIT_LABEL} limit reached")
    if notices:
        result += f"\n\n[{'. '.join(notices)}]"
    return result


def _list_directory_entries(path: str) -> list[str]:
    """Return directory entry names for a string path."""

    return sorted(
        (_format_directory_entry(entry) for entry in Path(path).iterdir()),
        key=str.lower,
    )


def _format_directory_entry(entry: Path) -> str:
    """Return a display name with directory entries marked by a slash."""

    if entry.is_dir():
        return f"{entry.name}/"
    return entry.name


tool = ToolDefinition(
    name="ls",
    description="List the contents of a directory.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path of the directory to list. Defaults to the current directory.",
            },
            "limit": {
                "type": "integer",
                "description": "The maximum number of entries to list. Defaults to 500.",
            },
        },
        "required": ["path"],
        "additionalProperties": False,
    },
    fn=fn,
)
