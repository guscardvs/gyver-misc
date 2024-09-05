import asyncio

from gyver.misc import aenumerate, amoving_window, as_async_generator
from gyver.misc.asynciter import aall, aany, afilter, agetn_and_exhaust, amap


async def test_aenumerate():
    async for index, item in aenumerate(as_async_generator([1, 2, 3])):
        assert index == item - 1


async def test_amoving_window():
    windows = []
    async for window in amoving_window(as_async_generator([1, 2, 3, 4, 5]), 3):
        windows.append(window)

    assert windows == [[1, 2, 3], [4, 5]]


async def test_as_async_generator():
    sequence = (1, 2, 3, 4, 5)
    async for idx, item in aenumerate(as_async_generator(sequence)):
        assert item == sequence[idx]


async def test_amap():
    async def predicate(a: int):
        await asyncio.sleep(0)
        return a + 2

    items = [1, 2, 3, 4, 5]
    async for idx, item in aenumerate(amap(predicate, as_async_generator(items))):
        assert item == items[idx] + 2


async def test_afilter():
    async def predicate(a: int):
        await asyncio.sleep(0)
        return a % 2 == 0

    items = [1, 2, 3, 4, 5]
    max_idx = 0
    async for idx, item in aenumerate(afilter(predicate, as_async_generator(items))):
        assert item in (2, 4)
        max_idx = idx

    assert max_idx == 1


async def test_aany():
    async def predicate(a: int):
        await asyncio.sleep(0)
        return a % 2 == 0

    assert await aany(as_async_generator([1, 2, 3, 4, 5]), predicate)
    assert not await aany(as_async_generator([1, 3, 5, 7, 9]), predicate)


async def test_aall():
    async def predicate(a: int):
        await asyncio.sleep(0)
        return a % 2 == 0

    assert await aall(as_async_generator([2, 4, 6, 8, 10]), predicate)
    assert not await aall(as_async_generator([1, 3, 5, 7, 9]), predicate)


async def test_agetn_and_exhaust():
    counter = 0

    async def generator(max: int):
        nonlocal counter
        for _ in range(max):
            yield counter
            counter += 1

    window = await agetn_and_exhaust(generator(5), 3)
    assert counter == 5
    assert window == [0, 1, 2]
