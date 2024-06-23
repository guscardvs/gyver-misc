import ast
import re
from collections.abc import Iterator
from io import BytesIO
from token import COMMENT
from tokenize import TokenError, tokenize
from typing import Any, Callable, Literal

from gyver.misc.casting import filter_isinstance

from .static import CacheMap, Validator


class runtime:
    """
    Implements runtime validation functions for checking object properties dynamically.

    Attributes:
        None

    Methods:
        child_of(parent_class: type) -> Callable[[Any], bool]:
            Returns a function to check if an object is a subclass or instance of `parent_class`.

        instance_of(*bases: type) -> Callable[[CacheMap, str, str], Iterator[str]]:
            Returns a function to validate instances of specified types in runtime.

        contains_attr(attr_name: str) -> Callable[[Any], bool]:
            Returns a function to check if an object contains a specified attribute.

        attr_with_value(attr_name: str, attr_value: Any) -> Callable[[Any], bool]:
            Returns a function to check if an object has a specified attribute with a specific value.
    """

    @staticmethod
    def child_of(parent_class: type) -> Callable[[Any], bool]:
        """
        Returns a function that checks if an object is a subclass (or instance) of `parent_class`.

        Args:
            parent_class (type): The class or type to check against.

        Returns:
            Callable[[Any], bool]: Function that checks if an object is a subclass or instance of `parent_class`.
        """

        def check(obj: Any) -> bool:
            return isinstance(obj, type) and issubclass(obj, parent_class)

        return check

    @staticmethod
    def instance_of(*bases: type) -> Callable[[CacheMap, str, str], Iterator[str]]:
        """
        Returns a function that validates instances of specified types in runtime.

        Args:
            *bases (type): Variable-length argument list of types to validate against.

        Returns:
            Callable[[CacheMap, str, str], Iterator[str]]: Function that yields names of instances
            that match the specified types.
        """

        def check(
            cachemap: CacheMap, module_contents: str, modname: str
        ) -> Iterator[str]:
            try:
                module_ast = ast.parse(module_contents, filename=modname)
            except SyntaxError:
                return None

            for node in filter_isinstance(ast.Assign, ast.walk(module_ast)):
                possible_bases = set(base.__name__ for base in bases) | {
                    name for name, item in cachemap.items() if isinstance(item, type)
                }
                walked = list(ast.walk(node.value))
                tuple_assign = next(
                    filter_isinstance(ast.Tuple, walked),
                    None,
                )
                if tuple_assign is not None:
                    for idx, item in enumerate(tuple_assign.elts):
                        if isinstance(item, ast.Call):
                            name = next(
                                filter_isinstance(ast.Name, ast.walk(item)), None
                            )
                            if name and name.id in possible_bases:
                                tuple_target = next(
                                    filter_isinstance(ast.Tuple, node.targets), None
                                )
                                if tuple_target is None:
                                    return

                                if len(tuple_target.elts) == 1 and isinstance(
                                    item_name := node.targets[0], ast.Name
                                ):
                                    yield (item_name.id)
                                elif idx < len(tuple_target.elts) and isinstance(
                                    item_name := tuple_target.elts[idx], ast.Name
                                ):
                                    yield (item_name.id)

                else:
                    next_call = next(
                        filter_isinstance(ast.Call, walked),
                        None,
                    )
                    if next_call is None:
                        continue
                    name = next(
                        filter_isinstance(ast.Name, ast.walk(next_call.func)), None
                    )
                    if not name:
                        continue
                    if name.id in possible_bases:
                        target = next(
                            filter_isinstance(
                                ast.Name,
                                (
                                    node
                                    for target in node.targets
                                    for node in ast.walk(target)
                                ),
                            ),
                            None,
                        )
                        if target is not None:
                            yield (target.id)

        return check

    @staticmethod
    def contains_attr(attr_name: str) -> Callable[[Any], bool]:
        """
        Returns a function that checks if an object contains an attribute `attr_name`.

        Args:
            attr_name (str): The attribute name to check for.

        Returns:
            Callable[[Any], bool]: Function that checks if an object contains the specified attribute.
        """

        def check(obj: Any) -> bool:
            return hasattr(obj, attr_name)

        return check

    @staticmethod
    def attr_with_value(attr_name: str, attr_value: Any) -> Callable[[Any], bool]:
        """
        Returns a function that checks if an object has an attribute `attr_name` with a specific `attr_value`.

        Args:
            attr_name (str): The attribute name to check for.
            attr_value (Any): The expected value of the attribute.

        Returns:
            Callable[[Any], bool]: Function that checks if the object has the specified attribute with the specified value.
        """

        def check(obj: Any) -> bool:
            return hasattr(obj, attr_name) and getattr(obj, attr_name) == attr_value

        return check


class static:
    """
    Implements static analysis functions for validating code structures based on AST parsing.

    Attributes:
        None

    Methods:
        autoload_validator(comment: str = "# static: autoload") -> Callable[[CacheMap, str, str], Iterator[str]]:
            Returns a function to validate modules containing a specific autoload comment.

        child_of(*bases: type) -> Callable[[CacheMap, str, str], Iterator[str]]:
            Returns a function to check if a class is a child of specified base classes using AST analysis.

        instance_of(*bases: type) -> Callable[[CacheMap, str, str], Iterator[str]]:
            Returns a function to validate instances of specified types using AST analysis.

        chain_validate(mode: Literal['any', 'all'], *validators: Validator) -> Validator:
            Chains multiple validators into a single function with specified validation mode.
    """

    @staticmethod
    def autoload_validator(comment: str = "# static: autoload"):
        """
        Returns a function to validate modules containing a specific autoload comment.

        Args:
            comment (str, optional): The comment string to search for in module contents. Defaults to "# static: autoload".

        Returns:
            Callable[[CacheMap, str, str], Iterator[str]]: Function that yields module names containing the specified comment.
        """

        def check(
            cachemap: CacheMap, module_contents: str, modname: str
        ) -> Iterator[str]:
            contents = BytesIO(module_contents.encode("utf-8"))
            try:
                return next(
                    (
                        iter((modname,))
                        for item in tokenize(contents.readline)
                        if item.type == COMMENT and comment in item.string
                    ),
                    iter(()),
                )
            except TokenError:
                return iter(())

        return check

    @staticmethod
    def child_of(*bases: type) -> Callable[[CacheMap, str, str], Iterator[str]]:
        """
        Returns a function to check if a class is a child of specified base classes using AST analysis.

        Args:
            *bases (type): Variable-length argument list of base class types to check against.

        Returns:
            Callable[[CacheMap, str, str], Iterator[str]]: Function that yields class names that are children of specified base classes.
        """

        def check(
            cachemap: CacheMap, module_contents: str, modname: str
        ) -> Iterator[str]:
            try:
                module_ast = ast.parse(module_contents, filename=modname)
            except SyntaxError:
                return None

            for node in ast.walk(module_ast):
                possible_bases = set(base.__name__ for base in bases) | set(
                    cachemap.keys()
                )
                if isinstance(node, ast.ClassDef):
                    class_name = node.name

                    # Skip if the class matches any of the base classes themselves
                    if any(
                        modname == base.__module__ and class_name == base.__name__
                        for base in bases
                    ):
                        continue

                    curbases = [
                        base.id for base in node.bases if isinstance(base, ast.Name)
                    ]

                    # Check if any base class in the class definition matches the criteria
                    if any(item in curbases for item in possible_bases):
                        yield class_name

        return check

    @staticmethod
    def instance_of(
        *bases: type,
    ) -> Callable[[CacheMap, str, str], Iterator[str]]:
        """
        Returns a function to validate instances of specified types using AST analysis.

        Args:
            *bases (type): Variable-length argument list of types to validate against.

        Returns:
            Callable[[CacheMap, str, str], Iterator[str]]: Function that yields names of instances
            that match the specified types.
        """

        def check(
            cachemap: CacheMap, module_contents: str, modname: str
        ) -> Iterator[str]:
            try:
                module_ast = ast.parse(module_contents, filename=modname)
            except SyntaxError:
                return None

            for node in filter_isinstance(ast.Assign, ast.walk(module_ast)):
                possible_bases = set(base.__name__ for base in bases) | {
                    name for name, item in cachemap.items() if isinstance(item, type)
                }
                walked = list(ast.walk(node.value))
                tuple_assign = next(
                    filter_isinstance(ast.Tuple, walked),
                    None,
                )
                if tuple_assign is not None:
                    for idx, item in enumerate(tuple_assign.elts):
                        if isinstance(item, ast.Call):
                            name = next(
                                filter_isinstance(ast.Name, ast.walk(item)), None
                            )
                            if name and name.id in possible_bases:
                                tuple_target = next(
                                    filter_isinstance(ast.Tuple, node.targets), None
                                )
                                if tuple_target is None:
                                    return

                                if len(tuple_target.elts) == 1 and isinstance(
                                    item_name := node.targets[0], ast.Name
                                ):
                                    yield (item_name.id)
                                elif idx < len(tuple_target.elts) and isinstance(
                                    item_name := tuple_target.elts[idx], ast.Name
                                ):
                                    yield (item_name.id)

                else:
                    next_call = next(
                        filter_isinstance(ast.Call, walked),
                        None,
                    )
                    if next_call is None:
                        continue
                    name = next(
                        filter_isinstance(ast.Name, ast.walk(next_call.func)), None
                    )
                    if not name:
                        continue
                    if name.id in possible_bases:
                        target = next(
                            filter_isinstance(
                                ast.Name,
                                (
                                    node
                                    for target in node.targets
                                    for node in ast.walk(target)
                                ),
                            ),
                            None,
                        )
                        if target is not None:
                            yield (target.id)

        return check

    @staticmethod
    def chain_validate(
        mode: Literal["any", "all"], *validators: Validator
    ) -> Validator:
        """
        Chains multiple validators into a single function with specified validation mode.

        Args:
            mode (Literal['any', 'all']): Mode specifying whether 'any' or 'all' validators must pass.
            *validators (Validator): Variable-length argument list of validator functions.

        Returns:
            Validator: Composite validator function that applies validators based on the mode.
        """

        def composite_validator(*args, **kwargs) -> Iterator[str]:
            if mode == "any":
                for validator in validators:
                    result = validator(*args, **kwargs)
                    if result is not None:
                        yield from result
                        return
                return None
            elif mode == "all":
                for validator in validators:
                    result = validator(*args, **kwargs)
                    if result is not None:
                        yield from result
            else:
                raise ValueError(f"Invalid mode '{mode}'. Expected 'any' or 'all'.")

        return composite_validator

    @staticmethod
    def noop_validator(module_name_filter: str | re.Pattern) -> Validator:
        """
        Returns a validator function that acts as a no-operation (noop) validator
        for modules matching the specified name filter.

        Args:
            module_name_filter (str): Filter to match module names (e.g., 'models.py' or 'models/').

        Returns:
            Validator: Validator function that returns an empty iterator for modules matching the filter.
        """

        def validate_module(
            cachemap: CacheMap, module_contents: str, modname: str
        ) -> Iterator[str]:
            # Check if the module name matches the filter
            if re.search(module_name_filter, modname):
                return iter(
                    [modname]
                )  # Return an empty iterator if module matches filter
            else:
                # Return None if module doesn't match the filter (no validation performed)
                return iter([])

        return validate_module
