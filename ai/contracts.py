from collections.abc import AsyncIterator
from typing import Literal, Protocol, TypedDict


class AsyncEventStream(Protocol):
    def __aiter__(self) -> AsyncIterator[object]: ...


class Reasoning(TypedDict, total=False):
    """App-level reasoning options passed to model providers."""

    effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"]
    summary: Literal["auto", "concise", "detailed"]
