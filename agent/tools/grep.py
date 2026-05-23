"""Search tool scaffold for the default agent."""

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
