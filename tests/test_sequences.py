import pytest

from gyver.misc import flatten, moving_window
from gyver.misc.sequences import carrymap, carrystarmap, exclude_none, maybe_next


def test_flatten():
    assert flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]
    assert flatten([1, 2, 3, 4]) == [1, 2, 3, 4]
    assert flatten([1, 2, [3, 4]]) == [1, 2, 3, 4]
    assert flatten([1, 2, [3, [4]]]) == [1, 2, 3, 4]
    assert flatten([1, 2, [3, [4, 5]]]) == [1, 2, 3, 4, 5]


def test_moving_window():
    assert list(moving_window([1, 2, 3, 4, 5], 1, list)) == [[1], [2], [3], [4], [5]]
    assert list(moving_window([1, 2, 3, 4, 5], 2, list)) == [[1, 2], [3, 4], [5]]
    assert list(moving_window([1, 2, 3, 4, 5], 3, list)) == [[1, 2, 3], [4, 5]]
    assert list(moving_window([1, 2, 3, 4, 5], 4, list)) == [[1, 2, 3, 4], [5]]
    assert list(moving_window([1, 2, 3, 4, 5], 5, list)) == [[1, 2, 3, 4, 5]]
    assert list(moving_window([1, 2, 3, 4, 5], 6, list)) == [[1, 2, 3, 4, 5]]


def test_exclude_none_dict():
    input_data = {'a': 1, 'b': None, 'c': {'d': 2, 'e': None}}
    expected_output = {'a': 1, 'c': {'d': 2}}
    assert exclude_none(input_data) == expected_output


def test_exclude_none_list():
    input_data = [1, None, 2, [3, None, 4], None]
    expected_output = [1, 2, [3, 4]]
    assert exclude_none(input_data) == expected_output


def test_exclude_none_tuple():
    input_data = (1, None, 2, (3, None, 4), None)
    expected_output = [1, 2, [3, 4]]  # tuple type is not preserved due to immutability
    assert exclude_none(input_data) == expected_output


def test_exclude_none_nested():
    input_data = {'a': [1, None, {'b': 2, 'c': None}], 'd': None}
    expected_output = {'a': [1, {'b': 2}]}
    assert exclude_none(input_data) == expected_output


def test_exclude_none_empty():
    assert exclude_none([]) == []
    assert exclude_none({}) == {}
    assert exclude_none(()) == []


def test_exclude_none_invalid_type():
    with pytest.raises(TypeError):
        exclude_none('invalid')


def test_maybe_next():
    sequence = [1, 2, 3, 4, 5]

    assert maybe_next(item for item in sequence if item == 1) == 1
    assert maybe_next(item for item in sequence if item < 1) is None
    assert maybe_next(reversed(sequence)) == 5


def test_carrymap():
    def predicate(a: int) -> int:
        return a * 2

    items = [1, 2, 3, 4, 5]
    results = list(carrymap(predicate, items))

    assert results == [(2, 1), (4, 2), (6, 3), (8, 4), (10, 5)]


def test_carrymap_empty():
    def predicate(a: int) -> int:
        return a * 2

    assert list(carrymap(predicate, [])) == []


def test_carrystarmap():
    def predicate(a: int, b: int) -> int:
        return a + b

    items = [(1, 2), (3, 4), (5, 6)]
    results = list(carrystarmap(predicate, items))

    assert results == [(3, (1, 2)), (7, (3, 4)), (11, (5, 6))]


def test_carrystarmap_empty():
    def predicate(a: int, b: int) -> int:
        return a + b

    assert list(carrystarmap(predicate, [])) == []
