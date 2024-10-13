import pytest

from gyver.misc import Namespace


@pytest.fixture
def namespace():
    """Fixture to provide a default Namespace instance."""
    return Namespace({'a': 1, 'b': 2, 'c': 3})


def test_namespace_getattr(namespace):
    """Test attribute access using dot notation."""
    assert namespace.a == 1
    assert namespace.b == 2
    assert namespace.c == 3


def test_namespace_getattr_key_error(namespace):
    """Test attribute access raises AttributeError for missing keys."""
    with pytest.raises(AttributeError):
        _ = namespace.nonexistent


def test_namespace_setattr(namespace):
    """Test setting attributes using dot notation."""
    namespace.d = 4
    assert namespace.d == 4
    assert namespace.__namespace_data__['d'] == 4


def test_namespace_setattr_reserved():
    """Test setting __namespace_data__."""
    ns = Namespace()
    ns.__namespace_data__ = {'key': 'value'}
    assert ns.__namespace_data__ == {'key': 'value'}


def test_namespace_setattr_overwrites_existing(namespace):
    """Test that setting an existing attribute overwrites the value."""
    namespace.a = 100
    assert namespace.a == 100
    assert namespace.__namespace_data__['a'] == 100


def test_namespace_getitem(namespace):
    """Test dictionary-style access."""
    assert namespace['a'] == 1
    assert namespace['b'] == 2


def test_namespace_getitem_key_error(namespace):
    """Test dictionary-style access raises KeyError for missing keys."""
    with pytest.raises(KeyError):
        _ = namespace['nonexistent']


def test_namespace_setitem(namespace):
    """Test setting values using dictionary-style access."""
    namespace['d'] = 4
    assert namespace['d'] == 4


def test_namespace_delitem(namespace):
    """Test deleting an item using dictionary-style access."""
    del namespace['a']
    assert 'a' not in namespace.__namespace_data__
    assert len(namespace) == 2


def test_namespace_delitem_key_error(namespace):
    """Test deleting a nonexistent item raises KeyError."""
    with pytest.raises(KeyError):
        del namespace['nonexistent']


def test_namespace_delattr(namespace):
    """Test deleting attributes using dot notation."""
    del namespace.a
    assert 'a' not in namespace.__namespace_data__


def test_namespace_delattr_key_error(namespace):
    """Test deleting a nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        del namespace.nonexistent


def test_namespace_len(namespace):
    """Test the length of the Namespace."""
    assert len(namespace) == 3
    namespace.d = 4
    assert len(namespace) == 4


def test_namespace_iter(namespace):
    """Test that the Namespace is iterable and returns keys."""
    keys = list(iter(namespace))
    assert keys == ['a', 'b', 'c']


def test_namespace_get_method(namespace):
    """Test the get method with default values."""
    assert namespace.get('a') == 1
    assert namespace.get('nonexistent', 'default') == 'default'
    assert namespace.get('nonexistent') is None


def test_namespace_repr(namespace):
    """Test the string representation of the Namespace."""
    assert repr(namespace) == repr({'a': 1, 'b': 2, 'c': 3})
