import asyncio
from collections.abc import Callable, Coroutine, Iterable
from functools import wraps
from typing import (
    Any,
    Concatenate,
    ParamSpec,
    TypeAlias,
    TypeVar,
    overload,
)

T = TypeVar('T')
P = ParamSpec('P')


def safe_cast(
    target_type: Callable[[Any], T],
    value: Any,
    *,
    default: T | None = None,
    ignore_childof: tuple[type[Exception], ...] = (ValueError, TypeError),
) -> T | None:
    """Cast value to target_type if possible, otherwise return default."""
    try:
        return target_type(value)
    except ignore_childof:
        return default


AsyncFunc: TypeAlias = Callable[P, Coroutine[Any, Any, T]]


@overload
def as_async(
    func: None = None,
    /,
    *,
    cast: Callable[
        Concatenate[Callable[P, T], P], Coroutine[Any, Any, T]
    ] = asyncio.to_thread,
) -> Callable[[Callable[P, T]], AsyncFunc[P, T]]: ...


@overload
def as_async(
    func: Callable[P, T],
    /,
) -> AsyncFunc[P, T]: ...


@overload
def as_async(
    func: AsyncFunc[P, T],
    /,
) -> AsyncFunc[P, T]: ...


def as_async(
    func: Callable[P, T] | AsyncFunc[P, T] | None = None,
    /,
    *,
    cast: Callable[
        Concatenate[Callable[P, T], P], Coroutine[Any, Any, T]
    ] = asyncio.to_thread,
) -> AsyncFunc[P, T] | Callable[[Callable[P, T]], AsyncFunc[P, T]]:
    """Convert a synchronous function to an asynchronous one."""

    def outer(func: Callable[P, T]) -> AsyncFunc[P, T]:
        if asyncio.iscoroutinefunction(func):
            return func

        @wraps(func)
        async def _inner(*args: P.args, **kwargs: P.kwargs) -> T:
            return await cast(func, *args, **kwargs)

        return _inner

    if func is None:
        return outer
    return outer(func)


def filter_isinstance(
    bases: type[T] | tuple[type[T], ...], iterable: Iterable[Any]
) -> 'filter[T]':
    def _predicate(item: T) -> bool:
        return isinstance(item, bases)

    return filter(_predicate, iterable)


def filter_issubclass(
    bases: type[T] | tuple[type[T], ...], iterable: Iterable[Any]
) -> 'filter[T]':
    def _predicate(item: T) -> bool:
        return isinstance(item, type) and issubclass(item, bases)

    return filter(_predicate, iterable)
