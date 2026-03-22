from typing import TypeAlias

from pydantic import BaseModel, JsonValue

JsonObject: TypeAlias = dict[str, JsonValue]


class ToolDefinition(BaseModel):
    """A provider-agnostic function tool definition."""

    name: str
    description: str
    input_schema: JsonObject
    defer_loading: bool = False
