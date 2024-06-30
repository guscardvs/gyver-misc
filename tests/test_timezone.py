import pytest
from zoneinfo import ZoneInfo

from gyver.misc import timezone


def test_timezone():
    assert timezone.now().tzinfo is not None

    assert timezone.today() == timezone.now().date()

    with pytest.raises(ValueError):
        timezone.set_tz(ZoneInfo("UTC"))


def test_timezone_instance():
    new_tz = timezone.TimeZone(ZoneInfo("Europe/Paris"))

    assert new_tz.now().tzinfo == ZoneInfo("Europe/Paris")

    assert new_tz.today() == new_tz.now().date()

    with pytest.raises(ValueError):
        new_tz.set_tz(ZoneInfo("UTC"))
