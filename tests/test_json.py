import io

from orjson import loads

from gyver.misc import json


def test_loads():
    assert json.loads is loads


def test_dumps():
    assert isinstance(json.dumps({}), str)


def test_load():
    io_buffer = io.StringIO('{"foo": "bar"}')

    assert json.load(io_buffer) == {"foo": "bar"}

    io_buffer = io.BytesIO(b'{"foo": "bar"}')

    assert json.load(io_buffer) == {"foo": "bar"}


def test_dump():
    io_buffer = io.BytesIO()

    json.dump({"foo": "bar"}, io_buffer)

    new_buffer = io.BytesIO()
    json.dump({"a": 1, "b": 2}, new_buffer, indent=True)

    assert io_buffer.getvalue() == b'{"foo":"bar"}'
    assert new_buffer.getvalue() == b'{\n  "a": 1,\n  "b": 2\n}'
