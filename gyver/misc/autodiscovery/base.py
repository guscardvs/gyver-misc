import ast
import importlib
import os
import pathlib
import sys
import warnings
from collections import defaultdict
from collections.abc import Callable, Iterator, Sequence
from inspect import getsourcelines
from pathlib import Path
from types import ModuleType
from typing import TypeAlias, TypeVar

from gyver.misc.casting import filter_isinstance
from gyver.misc.functions import lazymethod

PathConverter: TypeAlias = Callable[[Path], str]
StrOrPath: TypeAlias = str | Path
T = TypeVar('T')


def make_modulename_converter(
    root: pathlib.Path, path_converter: PathConverter
) -> PathConverter:
    root_path = path_converter(root)

    def converter(path: Path) -> str:
        pathstr = path_converter(path)
        if root_path in pathstr:
            pathstr = pathstr.replace(root_path, root.name)
        return pathstr.removesuffix('.py').replace('/', '.')

    return converter


class AutoDiscoveryHelper:
    """
    Helper class for auto-discovery of modules or files within a directory.

    Attributes:
        root (pathlib.Path): Root directory to start discovery.
        look_on (Path | None): Optional specific directory to look on.
        exclude (Sequence[StrOrPath]): List of paths or filenames to exclude.
        exts (Sequence[str]): List of file extensions to consider.
        converter (PathConverter): Function to convert paths to strings.
    """

    __slots__ = (
        '_root',
        '_look_on',
        '_exclude',
        '_exts',
        '_converter',
        lazymethod.get_private('get_resolver'),
        lazymethod.get_private('_excludes'),
    )

    def __init__(
        self,
        root: pathlib.Path,
        look_on: Path | None = None,
        exclude: Sequence[StrOrPath] = (),
        exts: Sequence[str] = (),
        converter: PathConverter = Path.as_posix,
    ):
        self._root = root
        self._look_on = look_on
        self._exclude = ('__pycache__', *exclude)
        self._exts = ('.py', *exts)
        self._converter = converter

    @lazymethod
    def _excludes(self) -> tuple[tuple[str, ...], tuple[Path, ...]]:
        str_exclude = tuple(filter_isinstance(str, self._exclude))
        path_exclude = tuple(filter_isinstance(pathlib.Path, self._exclude))
        return str_exclude, path_exclude

    def _should_look(self, path: Path) -> bool:
        str_exclude, path_exclude = self._excludes()
        _, ext = os.path.splitext(path)

        should_look = (
            path.name not in str_exclude
            and path not in path_exclude
            and (not path.is_file() or ext in self._exts)
        )
        return should_look

    @property
    def target_path(self) -> Path:
        return self._look_on or self._root

    @lazymethod
    def get_resolver(self) -> PathConverter:
        return make_modulename_converter(self._root, self._converter)

    def _iterdir(self, path: Path) -> Iterator[Path]:
        stack = [path]
        while stack:
            path = stack.pop()
            if not path.is_dir():
                yield path
                continue
            for item in filter(self._should_look, path.iterdir()):
                if item.is_dir():
                    stack.append(item)
                else:
                    yield item


def sort_files_by_dependency(modnames: list[str], files: list[Path]) -> Iterator[Path]:
    """
    Sorts Python files by their dependencies using AST analysis.

    Args:
        modnames (List[str]): List of module names corresponding to `files`.
        files (List[Path]): List of Path objects representing Python files to sort.

    Returns:
        List[Path]: Sorted list of Python files by dependency, least dependent first.
    """
    # Step 1: Parse each file and extract dependencies
    dependencies = defaultdict(set)
    for modname, file in zip(modnames, files):
        try:
            with file.open('r', encoding='utf-8') as f:
                module_ast = ast.parse(f.read(), filename=str(file))
                for node in ast.walk(module_ast):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name != '__future__':
                                dependencies[modname].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            dependencies[modname].add(node.module)
        except SyntaxError:
            # Handle syntax errors in the files gracefully
            warnings.warn(f'SyntaxError: Unable to parse file {file}')
            continue

    # Step 2: Perform topological sorting based on dependencies
    sorted_files = []
    visited = set()

    def dfs(modname):
        if modname in visited:
            return
        visited.add(modname)
        for dep in dependencies[modname]:
            dfs(dep)
        sorted_files.append(modname)

    for modname in modnames:
        dfs(modname)

    # Map sorted module names back to files
    for modname in sorted_files:
        for file, mod in zip(files, modnames):
            if mod == modname:
                yield file


def smart_import(modfullname: str, resolver: PathConverter) -> ModuleType:
    """
    Smart import function that avoids duplicate imports by leveraging sys.modules.

    Args:
        modfullname (str): Full module name to import.
        resolver (Callable[[Path], str]): Function to resolve module paths to full names.

    Returns:
        ModuleType: Imported module.
    """
    *_, modname = modfullname.rsplit('.', 1)
    if modname in sys.modules:
        return sys.modules[modname]

    main = sys.modules.get('__main__')
    main_modname = ''
    if main and main.__file__:
        main_modname = resolver(Path(main.__file__))

    if main_modname == modname:
        return main  # type: ignore
    return importlib.import_module(modfullname)


def ordered_mod(module: ModuleType):
    """Return a list of (name, obj) pairs sorted by place in module source."""
    modlines, _ = getsourcelines(module)
    objects = []
    later = []

    for name, obj in module.__dict__.items():
        try:
            source_lines, _ = getsourcelines(obj)
            start_line = source_lines[0]
            if start_line in modlines:
                linepos = modlines.index(start_line)
                objects.append((name, obj, linepos))
            else:
                later.append((name, obj))
        except (OSError, TypeError):
            later.append((name, obj))
    objects.sort(key=lambda x: x[2])  # Sort by start line number
    return [(name, obj) for name, obj, _ in objects] + later
