from collections.abc import Sequence
from enum import Enum
from typing import Any

from gyver.misc import strings
from gyver.misc.functions import lazymethod
from gyver.misc.sequences import maybe_next


class StrEnum(str, Enum):
    @classmethod
    def _missing_(cls, value: object) -> Any:
        return maybe_next(item for item in cls if value in item.aliases())

    @lazymethod
    def aliases(self) -> Sequence[str]:
        return tuple(
            {
                self.value,
                self.name,
                self.name.upper(),
                self.name.lower(),
                strings.to_camel(self.name),
                strings.to_pascal(self.name),
                strings.to_kebab(self.name),
            }
        )


class ValueEnum(StrEnum):
    def __str__(self) -> str:
        return self.value


class NameEnum(StrEnum):
    def __str__(self) -> str:
        return self.name


class SnakeEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return strings.to_snake(name)


class CamelEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return strings.to_camel(name)


class PascalEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return strings.to_pascal(name)


class KebabEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return strings.to_kebab(name)
