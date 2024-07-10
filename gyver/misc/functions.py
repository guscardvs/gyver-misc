import functools
from collections.abc import Callable
from typing import Generic, ParamSpec, TypeVar, cast, overload

from typing_extensions import Self

T = TypeVar('T')
P = ParamSpec('P')
SelfT = TypeVar('SelfT')


def cache(f: Callable[P, T]) -> Callable[P, T]:
    return cast(Callable[P, T], functools.cache(f))


class lazymethod(Generic[SelfT, T]):
    __slots__ = ('_func', 'public_name', 'private_name')

    format_ = '_lazymethod_{method_name}_'

    def __init__(self, func: Callable[[SelfT], T]) -> None:
        self._func = func

    def __set_name__(self, owner: type[SelfT], name: str) -> None:
        self.public_name = name
        self.private_name = self.format_.format(method_name=name)

    @classmethod
    def get_private(cls, name: str) -> str:
        return cls.format_.format(method_name=name)

    @overload
    def __get__(self, instance: None, owner: type[SelfT]) -> Self: ...

    @overload
    def __get__(self, instance: SelfT, owner: type[SelfT]) -> Callable[[], T]: ...

    def __get__(
        self, instance: SelfT | None, owner: type[SelfT]
    ) -> Callable[[], T] | Self:
        if instance is None:
            return self
        return self._call(instance)

    def _call(self, instance: SelfT) -> Callable[[], T]:
        @functools.wraps(self._func)
        def _callable() -> T:
            if hasattr(instance, self.private_name):
                return getattr(instance, self.private_name)
            return self._set(instance)

        return _callable

    def _set(self, instance: SelfT) -> T:
        value = self._func(instance)
        setattr(instance, self.private_name, value)
        return value

    @classmethod
    def is_initialized(cls, instance: SelfT, name: str) -> bool:
        return hasattr(instance, cls.format_.format(method_name=name))
