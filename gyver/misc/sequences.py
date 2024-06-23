import itertools
from collections import deque
from collections.abc import Iterable, Sequence
from typing import Literal, TypeVar

from gyver.misc.casting import safe_cast

T = TypeVar("T")


def moving_window(iterable: Iterable[T], window_size: int) -> Iterable[Sequence[T]]:
    """Return an iterator moving a window of size window_size over iterable."""
    iterator = iter(iterable)

    while True:
        window = tuple(itertools.islice(iterator, window_size))
        if not window:
            break
        yield window


def flatten(sequence: Sequence[Sequence[T]]) -> Sequence[T]:
    """Flatten an arbitrarily nested sequence."""
    flattened = []
    stack: list[tuple[Sequence, int]] = [(sequence, 0)]

    while stack:
        curseq, index = stack.pop()
        while index < len(curseq):
            item = curseq[index]
            if isinstance(item, Sequence) and not isinstance(item, str | bytes):
                stack.append((curseq, index))
                curseq, index = item, 0
            else:
                flattened.append(item)
            index += 1

    return safe_cast(
        type(sequence), flattened, default=flattened, ignore_childof=(Exception,)
    )  # type: ignore


def merge_dicts(
    left: dict,
    right: dict,
    on_conflict: Literal["strict", "left", "right"],
    merge_sequences: bool = True,
) -> dict:
    """
    Merge two dictionaries with customizable conflict resolution strategy.

    Args:
        left (dict): The left dictionary to merge.
        right (dict): The right dictionary to merge.
        on_conflict (Literal["strict", "left", "right"]): The conflict resolution strategy to use.

            - 'strict': Raise a MergeConflict exception if conflicts occur.
            - 'left': Prioritize the values from the left dictionary in case of conflicts.
            - 'right': Prioritize the values from the right dictionary in case of conflicts.
        merge_sequences (bool, optional): Indicates whether to merge sequences (lists, sets, tuples) or skip them.

            - If True, sequences will be merged based on the conflict resolution strategy.
            - If False, sequences will be skipped, and the value from the chosen (defaults to left on strict)
            dictionary will be used. Default is True.

    Returns:
        dict: The merged dictionary.

    Raises:
        MergeConflict: If conflicts occur and the conflict resolution strategy is set to 'strict'.
    """

    output = {key: value for key, value in left.items() if key not in right}

    stack = deque([(left, right, output)])

    while stack:
        left_curr, right_curr, output_curr = stack.pop()

        for key, value in right_curr.items():
            if key not in left_curr:
                output_curr[key] = value
            elif isinstance(value, (list, set, tuple)) and merge_sequences:
                left_val = left_curr[key]
                if isinstance(left_val, (list, set, tuple)):
                    type_ = type(value) if on_conflict == "right" else type(left_val)
                    output_curr[key] = type_(itertools.chain(left_val, value))
            elif isinstance(value, dict):
                if isinstance(left_curr[key], dict):
                    output_curr[key] = {
                        lkey: lvalue
                        for lkey, lvalue in left_curr[key].items()
                        if lkey not in value
                    }
                    stack.append((left_curr[key], value, output_curr[key]))
            elif on_conflict not in ("left", "right"):
                raise ValueError(
                    "Conflict found when trying to merge dicts",
                    key,
                    value,
                    left_curr[key],
                )
            elif on_conflict == "left":
                output_curr[key] = left_curr[key]
            else:
                output_curr[key] = value

    return output
