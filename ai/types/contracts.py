from collections.abc import AsyncIterator
from typing import Literal, Protocol, TypedDict

from ai.types.stream import StreamEvent


class AsyncEventStream(Protocol):
    def __aiter__(self) -> AsyncIterator[StreamEvent]: ...


class Reasoning(TypedDict, total=False):
    """App-level reasoning options passed to model providers."""

    effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"]
    summary: Literal["auto", "concise", "detailed"]
