from typing import TypeVar

ExceptionT = TypeVar("ExceptionT", bound=Exception)


def sentence(exc_type: type[ExceptionT], message: str, *args) -> ExceptionT:
    """Add a period to the end of the message."""
    return exc_type(message.rstrip(".!?") + ".", *args)


def scream(exc_type: type[ExceptionT], message: str, *args) -> ExceptionT:
    """Add an exclamation point to the end of the message."""
    return exc_type(message.rstrip(".!?") + "!", *args)
