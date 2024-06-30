from gyver.misc import as_async, filter_isinstance, safe_cast


class CustomError(Exception):
    pass


def test_safe_cast():
    assert safe_cast(str, 1) == "1"
    assert safe_cast(int, "1") == 1
    assert safe_cast(str, 1.0) == "1.0"
    assert safe_cast(float, "1.0") == 1.0
    assert safe_cast(float, 1) == 1.0

    # test returns none on error
    assert safe_cast(int, "a") is None
    assert safe_cast(int, None) is None
    assert safe_cast(int, []) is None
    assert safe_cast(int, {}) is None
    assert safe_cast(int, (1, 2)) is None

    # custom function that intentionally raises CustomError
    def raise_error(val):
        raise CustomError

    assert safe_cast(raise_error, 1, default="", ignore_childof=(CustomError,)) == ""


async def test_as_async():
    @as_async
    def func():
        return 1

    assert await func() == 1


def test_filter_isinstance():
    assert list(filter_isinstance(int, [1, 2, 3])) == [1, 2, 3]
    assert list(filter_isinstance(float, (1, 2.0, 3))) == [2.0]
    mapping = {"a": 1, "b": 2, "c": 3}
    mockset = set(mapping.values())
    assert list(filter_isinstance((set, dict), [1, 2, [], mockset, mapping])) == [
        mockset,
        mapping,
    ]
