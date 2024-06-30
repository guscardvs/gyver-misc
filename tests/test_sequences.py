from gyver.misc import flatten, moving_window


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
