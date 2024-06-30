from gyver.misc import aenumerate, amoving_window, as_async_generator


async def _generate(sequence):
    for item in sequence:
        yield item


async def test_aenumerate():
    async for index, item in aenumerate(_generate([1, 2, 3])):
        assert index == item - 1


async def test_amoving_window():
    windows = []
    async for window in amoving_window(_generate([1, 2, 3, 4, 5]), 3):
        windows.append(window)

    assert windows == [[1, 2, 3], [4, 5]]


async def test_as_async_generator():
    sequence = (1, 2, 3, 4, 5)
    async for idx, item in aenumerate(as_async_generator(sequence)):
        assert item == sequence[idx]
