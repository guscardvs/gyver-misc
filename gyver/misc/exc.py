from typing import TypeVar

from gyver.misc.strings import exclamation, question
from gyver.misc.strings import sentence as _sentence

ExceptionT = TypeVar('ExceptionT', bound=Exception)


def sentence(exc_type: type[ExceptionT], message: str, *args) -> ExceptionT:
    """Add a period to the end of the message."""
    return exc_type(_sentence(message), *args)


def scream(exc_type: type[ExceptionT], message: str, *args) -> ExceptionT:
    """Add an exclamation point to the end of the message."""
    return exc_type(exclamation(message), *args)


def question_message(exc_type: type[ExceptionT], message: str, *args) -> ExceptionT:
    """Add a question mark to the end of the message."""
    return exc_type(question(message), *args)
