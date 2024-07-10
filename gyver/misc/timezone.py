import datetime
import sys
from collections.abc import Callable

from typing_extensions import deprecated

_DEFAULT_TZ = datetime.timezone.utc if sys.version_info < (3, 11) else datetime.UTC


class TimeZone:
    def __init__(self, tz: datetime.tzinfo) -> None:
        self._tz = tz
        self._retrieved = False

    def now(self) -> datetime.datetime:
        self._retrieved = True
        return datetime.datetime.now(self._tz)

    def today(self) -> datetime.date:
        return self.now().date()

    def set_tz(self, tz: datetime.tzinfo) -> None:
        if self._retrieved:
            raise ValueError('Timezone can only be set once')
        self._tz = tz


_default_instance = TimeZone(_DEFAULT_TZ)

now = _default_instance.now
today = _default_instance.today
set_tz = _default_instance.set_tz


# Compatibility
@deprecated('Use "TimeZone" instead')
def make_now_factory(tz: datetime.tzinfo) -> Callable[[], datetime.datetime]:
    return TimeZone(tz).now


__all__ = ['now', 'today', 'set_tz', 'TimeZone']
