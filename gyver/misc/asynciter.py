from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Iterable,
    Sequence,
)
from typing import TypeVar

T = TypeVar("T")


async def aenumerate(
    iterable: AsyncIterable[T], start: int = 0
) -> AsyncIterator[tuple[int, T]]:
    """Return an async iterator that yields tuples of (index, value)."""
    index = start
    async for item in iterable:
        yield index, item
        index += 1


async def amoving_window(
    iterable: AsyncIterable[T], max_length: int
) -> AsyncIterator[Sequence[T]]:
    """Return an async iterator moving a window of size max_length over iterable."""
    window = []

    async for item in iterable:
        window.append(item)
        if len(window) >= max_length:
            yield window
            window = []
    if window:
        yield window


async def as_async_generator(iterable: Iterable[T]) -> AsyncGenerator[T, None]:
    """Return an async generator from an iterable."""
    for item in iterable:
        yield item
