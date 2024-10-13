from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Coroutine,
    Iterable,
    Sequence,
)
from typing import Any, ParamSpec, TypeVar

from gyver.misc.casting import as_async

T = TypeVar('T')
S = TypeVar('S')
U = TypeVar('U')
P = ParamSpec('P')


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


async def afilter(
    predicate: Callable[[T], bool | Coroutine[Any, Any, bool]],
    iterable: AsyncIterable[T],
) -> AsyncGenerator[T]:
    """Return an async iterator that yields only those items for which the predicate is true."""
    asyncpredicate = as_async(predicate)
    async for item in iterable:
        if await asyncpredicate(item):
            yield item


async def amap(
    predicate: Callable[[T], S | Coroutine[Any, Any, S]], iterable: AsyncIterable[T]
) -> AsyncIterable[S]:
    """Return an async iterator that yields the result of applying the predicate to each item."""
    asyncpredicate = as_async(predicate)
    async for item in iterable:
        yield await asyncpredicate(item)  # type: ignore


async def aany(
    iterable: AsyncIterable[T],
    predicate: Callable[[T], bool | Coroutine[Any, Any, bool]] = bool,
) -> bool:
    """Return True if any item in the async iterable satisfies the predicate."""
    return (await anext(afilter(predicate, iterable), None)) is not None


async def aall(
    iterable: AsyncIterable[T],
    predicate: Callable[[T], bool | Coroutine[Any, Any, bool]] = bool,
) -> bool:
    """Return True if all items in the async iterable satisfy the predicate."""

    async def _not_predicate(x: T) -> bool:
        return not await as_async(predicate)(x)

    return not await aany(iterable, _not_predicate)


async def agetn_and_exhaust(iterable: AsyncIterable[T], n: int) -> Sequence[T]:
    """Return the first n items of an async iterable and exhaust it."""
    gen = amoving_window(iterable, n)
    window = await anext(gen, [])
    async for _ in gen:
        pass
    return window


async def maybe_anext(iterable: AsyncIterable[T]) -> T | None:
    return await anext(aiter(iterable), None)
