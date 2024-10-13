from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


@contextmanager
def raise_insteadof(
    insteadof: type[Exception], exc: type[Exception] = Exception, *args: Any
) -> Generator[None, None, None]:
    try:
        yield
    except insteadof:
        raise exc(*args) from None


class Namespace:
    """
    A lightweight class that provides dictionary-like functionality but allows
    access to its keys as if they were attributes using dot notation.

    The `Namespace` is a thin wrapper around a dictionary, offering attribute-style
    access (`namespace.key`) in addition to the traditional item-style access
    (`namespace['key']`). It is designed for cases where dynamic attribute management
    is needed while maintaining the flexibility and mutability of a standard dictionary.

    Attributes:
        __namespace_data__ (dict): The underlying dictionary used for storage of keys
        and values.

    Methods:
        __getattr__(name): Returns the value associated with `name` if it exists.
        Raises an AttributeError if not found.

        __setattr__(name, value): Sets the value of `name` to `value`. Respects the
        `__slots__` definition for internal attributes.

        __getitem__(name): Retrieves the value associated with `name` using dictionary
        indexing.

        __setitem__(name, value): Sets the value associated with `name` using dictionary
        indexing.

        __delitem__(name): Deletes the item associated with `name` from the underlying
        dictionary.

        __delattr__(name): Deletes the attribute-style `name` from the underlying dictionary.

        __iter__(): Iterates over the keys of the namespace.

        __len__(): Returns the number of items in the namespace.

        get(name, default=None): Retrieves the value associated with `name`, or returns
        `default` if the key is not found.

        __repr__(): Returns a string representation of the underlying dictionary.
    """

    __slots__ = ('__namespace_data__',)

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self.__namespace_data__ = initial or {}

    def __getattr__(self, name: str) -> Any:
        with raise_insteadof(
            KeyError, AttributeError, f'Attribute {name} not found in namespace.'
        ):
            return self.__namespace_data__[name]

    def __setattr__(self, name: str, value: Any, /) -> None:
        if name in Namespace.__slots__:
            return super().__setattr__(name, value)
        self.__namespace_data__[name] = value

    def __getitem__(self, name: str) -> Any:
        return self.__namespace_data__[name]

    def __setitem__(self, name: str, value: Any, /) -> None:
        self.__namespace_data__[name] = value

    def __delitem__(self, name: str, /) -> None:
        del self.__namespace_data__[name]

    def __delattr__(self, name: str, /) -> None:
        if name in Namespace.__slots__:
            return super().__delattr__(name)

        with raise_insteadof(
            KeyError, AttributeError, f'Attribute {name} not found in namespace.'
        ):
            del self.__namespace_data__[name]

    def __iter__(self) -> Any:
        return iter(self.__namespace_data__)

    def __len__(self) -> int:
        return len(self.__namespace_data__)

    def get(self, name: str, default: Any = None, /) -> Any:
        try:
            return self.__namespace_data__[name]
        except KeyError:
            return default

    def __repr__(self) -> str:
        return repr(self.__namespace_data__)
