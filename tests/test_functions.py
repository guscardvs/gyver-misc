import functools

from gyver.misc import cache, lazymethod


def test_cache():
    if isinstance(functools._lru_cache_wrapper, type):

        @cache
        def add(a, b):
            return a + b

        assert isinstance(add, functools._lru_cache_wrapper)
    else:
        counter = 0

        @cache
        def add(a, b):
            nonlocal counter
            counter += 1
            return a + b

        assert add(1, 2) == 3
        assert add(1, 2) == 3
        assert add(1, 2) == 3
        assert counter == 1


def test_lazymethod():
    class Test:
        def __init__(self) -> None:
            self.counter = 0

        @lazymethod
        def calculate_name(self):
            self.counter += 1
            return 'test_' + str(self.counter)

        @lazymethod
        def calculate_custom_name(self, name: str | None):
            self.counter += 1
            return f'test_{name or ""}' + str(self.counter)

        @lazymethod
        def calculate_complex_naming(self, names: list[str]):
            self.counter += 1
            return ', '.join(f'test_{name}' + str(self.counter) for name in names)

    t = Test()
    t2 = Test()
    assert t.calculate_name() == 'test_1'
    assert t.calculate_name() == 'test_1'
    assert t.calculate_custom_name('1') == 'test_12'
    assert t.calculate_custom_name('1') == 'test_12'
    assert t.calculate_complex_naming(['1', '2']) == 'test_13, test_23'
    assert t.calculate_complex_naming(['1', '2']) == 'test_13, test_23'

    assert lazymethod.is_initialized(t, 'calculate_name')
    assert not lazymethod.is_initialized(t2, 'calculate_name')

    assert t2.calculate_name() == 'test_1'
