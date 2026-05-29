"""Tool contracts shared by agents and AI providers."""

from collections.abc import Awaitable, Callable
from typing import Literal, TypeAlias

from pydantic import BaseModel, JsonValue

JsonObject: TypeAlias = dict[str, JsonValue]
ImageMimeType: TypeAlias = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]


class ToolTextContent(BaseModel):
    """Text content returned by a tool."""

    type: Literal["text"] = "text"
    text: str


class ToolImageContent(BaseModel):
    """Base64-encoded image content returned by a tool."""

    type: Literal["image"] = "image"
    data: str
    mime_type: ImageMimeType


ToolResultContent: TypeAlias = ToolTextContent | ToolImageContent


class ToolResult(BaseModel):
    """Provider-neutral tool execution result."""

    content: list[ToolResultContent]

    @classmethod
    def text(cls, text: str) -> "ToolResult":
        """Create a text-only tool result."""

        return cls(content=[ToolTextContent(text=text)])

    @classmethod
    def image(cls, text: str, image: ToolImageContent) -> "ToolResult":
        """Create an image tool result with an explanatory text block."""

        return cls(content=[ToolTextContent(text=text), image])


ToolFunctionResult: TypeAlias = ToolResult
ToolFunction: TypeAlias = Callable[..., Awaitable[ToolFunctionResult]]


class ToolDefinition(BaseModel):
    """A provider-agnostic function tool definition."""

    name: str
    description: str
    input_schema: JsonObject
    defer_loading: bool = False
    fn: ToolFunction
