import inspect
import pathlib
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any, Sequence, TypeAlias

from gyver.misc.functions import lazymethod

from .base import AutoDiscoveryHelper, PathConverter, StrOrPath, smart_import

Validator: TypeAlias = Callable[[Any], bool]


class RuntimeAutoDiscovery:
    """
    Facilitates runtime discovery and loading of modules based on a validation function.

    This class enables the discovery and loading of modules within a specified directory (`root`)
    or its subdirectories (`look_on`), leveraging runtime inspection techniques to identify and
    load modules that meet the criteria defined by the provided validator function.

    Attributes:
        _internal (AutoDiscoveryHelper): Helper instance for managing directory traversal and path conversion.
        _validator (Validator): Function to validate modules or objects based on runtime inspection.

    Methods:
        load() -> Iterator[tuple[str, Any]]:
            Lazily loads modules that pass the validation criteria defined by `_validator`.

        load_asdict() -> dict[str, Any]:
            Loads discovered modules into a dictionary format.

    Example Usage:
        validator = lambda obj: inspect.isclass(obj) and issubclass(obj, MyBaseClass)
        discovery = RuntimeAutoDiscovery(
            validator,
            root=pathlib.Path("/path/to/directory"),
            exclude=["excluded_module.py"],
            exts=["py"],
        )
        for name, obj in discovery.load():
            print(f"Loaded module: {name}")
    """

    __slots__ = ("_internal", "_validator", lazymethod.get_private("load"))

    def __init__(
        self,
        validator: Validator,
        root: pathlib.Path,
        look_on: Path | None = None,
        exclude: Sequence[StrOrPath] = (),
        exts: Sequence[str] = (),
        converter: PathConverter = Path.as_posix,
    ):
        """
        Iterates over the members of the module specified by the given path.

        Args:
            path (Path): The path to the module to be loaded.

        Yields:
            Iterable[tuple[str, Any]]: An iterable of tuples containing member names
            and their corresponding objects if they pass the validation.
        """
        self._validator = validator
        self._internal = AutoDiscoveryHelper(
            root,
            look_on,
            exclude,
            exts,
            converter,
        )

    def _itermod(self, path: Path) -> Iterable[tuple[str, Any]]:
        """
        Iterates over the members of the module specified by the given path.

        Args:
            path (Path): The path to the module to be loaded.

        Yields:
            Iterable[tuple[str, Any]]: An iterable of tuples containing member names
            and their corresponding objects if they pass the validation.
        """
        resolver = self._internal.get_resolver()
        mod = smart_import(resolver(path), resolver)

        for name, obj in inspect.getmembers(mod):
            if self._validator(obj):
                yield (name, obj)

    @lazymethod
    def load(self) -> Iterator[tuple[str, Any]]:
        """
        Lazily loads modules that pass the validation criteria.

        Returns:
            Iterator[tuple[str, Any]]: Iterator yielding tuples of module names and their corresponding objects.
        """
        for file in self._internal._iterdir(self._internal.target_path):
            for name, obj in self._itermod(file):
                if self._validator(obj):
                    yield name, obj

    def load_asdict(self) -> dict[str, Any]:
        """
        Loads discovered modules into a dictionary format.

        Returns:
            dict[str, Any]: Dictionary mapping module names to their corresponding objects.
        """
        return dict(self.load())
