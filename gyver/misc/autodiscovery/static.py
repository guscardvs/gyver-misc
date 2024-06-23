import os
from collections.abc import Callable, Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any, TypeAlias

from gyver.misc.autodiscovery.base import (
    AutoDiscoveryHelper,
    PathConverter,
    StrOrPath,
    smart_import,
    sort_files_by_dependency,
)
from gyver.misc.functions import lazymethod

CacheMap: TypeAlias = dict[str, Any]
ModName: TypeAlias = str
ObjectName: TypeAlias = str
Contents: TypeAlias = str
Validator: TypeAlias = Callable[[CacheMap, Contents, ModName], Iterator[ObjectName]]


class StaticAutoDiscovery:
    """
    Performs static analysis to discover and load modules based on predefined criteria.

    This class facilitates the discovery of modules within a specified directory (`root`) or its
    subdirectories (`look_on`), applying static analysis techniques to identify and load modules
    that meet the criteria defined by the provided validator function.

    Attributes:
        _internal (AutoDiscoveryHelper): Helper instance for managing directory traversal and path conversion.
        _validator (Validator): Function to validate modules based on cached information and contents.
        _rounds (int): Number of rounds for discovery, limiting the depth of exploration in the directory structure.
        _cache (CacheMap): Dictionary to store discovered module objects for reuse and reference.

    Methods:
        load() -> Iterable[tuple[str, Any]]:
            Lazily loads modules that pass the validation criteria defined by `_validator`.

        load_asdict() -> dict[str, Any]:
            Loads discovered modules into a dictionary format.

    Example Usage:
        validator = static.instance_of(MyBaseClass)
        discovery = StaticAutoDiscovery(
            validator,
            root=Path("/path/to/directory"),
            exclude=["excluded_module.py"],
            exts=["py"],
            rounds=2
        )
        for name, obj in discovery.load():
            print(f"Loaded module: {name}")
    """

    __slots__ = (
        "_internal",
        "_validator",
        "_rounds",
        "_cache",
        lazymethod.get_private("load"),
    )

    def __init__(
        self,
        validator: Validator,
        root: Path,
        look_on: Path | None = None,
        exclude: Sequence[StrOrPath] = (),
        exts: Sequence[str] = (),
        converter: PathConverter = Path.as_posix,
        rounds: int = 1,
    ):
        self._validator = validator
        self._rounds = rounds
        self._internal = AutoDiscoveryHelper(
            root,
            look_on,
            exclude,
            exts,
            converter,
        )
        self._cache: CacheMap = {}

    @lazymethod
    def load(self) -> Iterable[tuple[str, Any]]:
        """
        Lazily loads modules from the target directory based on validation criteria.

        Returns:
            Iterable[tuple[str, Any]]: Generator yielding tuples of module names and their corresponding objects.
        """
        for round_num in range(self._rounds):
            files = list(self._internal._iterdir(self._internal.target_path))
            for path in sort_files_by_dependency(
                [os.path.splitext(item)[0] for item in files], files
            ):
                module = self._parse_module(path)
                resolver = self._internal.get_resolver()
                modname = resolver(path)
                for name in self._validator(self._cache, module, modname):
                    yield from self._import_module([name], path)

    def load_asdict(self) -> dict[str, Any]:
        return dict(self.load())

    def _parse_module(self, path: Path) -> str:
        """
        Parses the contents of a module file.

        Args:
            path (Path): Path to the module file.

        Returns:
            str: Contents of the module as a string.
        """
        with path.open("r", encoding="utf-8") as stream:
            return stream.read()

    def _import_module(
        self, names: Sequence[str], path: Path
    ) -> Iterable[tuple[str, Any]]:
        """
        Imports specific modules identified by `names` from a given `path`.

        Args:
            names (Sequence[str]): Names of modules to import.
            path (Path): Path to the module file.

        Yields:
            Iterable[tuple[str, Any]]: Generator yielding tuples of imported module names and their corresponding objects.
        """
        names = [item for item in names if item not in self._cache]
        resolver = self._internal.get_resolver()
        modname = resolver(path)
        mod = smart_import(modname, resolver)
        for vname, obj in mod.__dict__.items():
            if vname in names:
                self._cache[vname] = obj
                yield vname, obj


class NOT_FOUND:
    """
    Placeholder class to indicate that a requested module or object was not found.
    """

    pass
