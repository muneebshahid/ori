from collections.abc import AsyncIterator
from typing import Protocol


class AsyncEventStream(Protocol):
    def __aiter__(self) -> AsyncIterator[object]: ...
