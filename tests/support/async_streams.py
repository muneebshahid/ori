"""Helpers for adapting static test data into async streams."""

from collections.abc import AsyncIterator, Sequence
from typing import TypeVar

TItem = TypeVar("TItem")


def async_stream(items: Sequence[TItem]) -> AsyncIterator[TItem]:
    """Yield static test items through an async iterator."""

    async def _iterate() -> AsyncIterator[TItem]:
        """Yield each configured item."""

        for item in items:
            yield item

    return _iterate()
