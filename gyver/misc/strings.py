import re
import shlex
from collections.abc import Callable
from typing import Any, TypeVar

from typing_extensions import deprecated

__all__ = [
    'to_snake',
    'to_camel',
    'to_pascal',
    'to_kebab',
    'make_lex_separator',
    'comma_separator',
]

T = TypeVar('T')
OuterCastT = TypeVar('OuterCastT', list, tuple, set)

_to_camel_regexp = re.compile('(_|-)([a-zA-Z])')
_to_snake_regexp = re.compile('([a-z])([A-Z])')


def replace_all(string: str, replacements: dict[str, str]) -> str:
    for old, new in replacements.items():
        string = string.replace(old, new)
    return string


def to_snake(string: str) -> str:
    return replace_all(
        _to_snake_regexp.sub(r'\1_\2', string), {'-': '_', ' ': '_'}
    ).lower()


def to_camel(string: str) -> str:
    return _to_camel_regexp.sub(
        lambda match: match[2].upper(), to_snake(string)
    ).rstrip('_-')


def to_pascal(string: str) -> str:
    val = to_camel(string)
    return val[0].upper() + val[1:]


upper_camel = deprecated('Use "to_pascal" instead.')(to_pascal)


def to_kebab(string: str, remove_trailing_underscores: bool = False) -> str:
    result = to_snake(string).replace('_', '-')
    return result if not remove_trailing_underscores else result.rstrip('-')


def make_lex_separator(
    outer_cast: type[OuterCastT], cast: type = str
) -> Callable[[str], OuterCastT]:
    def wrapper(value: str) -> OuterCastT:
        lex = shlex.shlex(value, posix=True)
        lex.whitespace = ','
        lex.whitespace_split = True
        return outer_cast(cast(item.strip()) for item in lex)

    return wrapper


def quote(string: str, quote_char: str = '"') -> str:
    return f'{quote_char}{string}{quote_char}'


comma_separator = make_lex_separator(tuple, str)


def convert(obj: dict[str, Any], key_format: Callable[[str], str]) -> dict[str, Any]:
    return {key_format(key): value for key, value in obj.items()}


def sentence(string: str) -> str:
    return string.rstrip('.!?') + '.'


def exclamation(string: str) -> str:
    return string.rstrip('.!?') + '!'


def question(string: str) -> str:
    return string.rstrip('.!?') + '?'
