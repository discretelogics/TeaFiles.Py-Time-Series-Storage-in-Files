# Copyright (C) 2011 discretelogics
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''
TeaFiles should preferaby use an integer value for time representation storing
the number of milliseconds since 1.1.1970.

This module provides classes DateTime and Duration that aid in arithmetic,
parsing, printing and conversion to python's c-ish date and time tools.

The module name lends from the movie starring John Cleese, pretty pythonesk indeed.
'''


import time
import datetime
import calendar


class DateTime:
    ''' Holds a date and time value measured in milliseconds since the unix
        epoch 1970-01-01. This value, the number of "ticks", is the only state
        maintained by this class.

        1. Either **ticks** are passed, in which case all other arguments are ignored.
        2. Otherwise all other arguments are used to compute the ticks to be stored.

        * *year*:   beween 1 .. 9999
        * *month*:  between 1 .. 12
        * *day*:    between 1 .. 31
        * *hours*, *minutes*, *seconds* and *milliseconds* are not checked to be in any range, they
          are multiplied with their respective number of milliseconds and summed up to the
          value of _ticks.

        >>> DateTime()
        1970-01-01 00:00:00:000
        >>> DateTime().ticks
        0
        >>> DateTime(1970, 1, 1).ticks
        0
        >>> DateTime(1970, 1, 2).ticks
        86400000
        >>> DateTime(ticks=427).ticks
        427L
        >>> DateTime(2000, 1, 1, 77, 88, 99, 5240000).ticks
        946972619000L
        >>> DateTime(2000, 1, 1, 77, 88, 99, 5240000, 11).ticks
        11L
        '''

    ticksperday = 86400 * 1000  # millseconds per day

    def __init__(self, year=1970, month=1, day=1, hours=0, minutes=0, seconds=0, milliseconds=0, ticks=None):

        if ticks:
            self._ticks = long(ticks)
        else:
            if year > 9999:
                raise ValueError("Maximum value for year=9999")
            if year < 1:
                raise ValueError("Minimum value for year=0001")

            dt = DateTime._getticksfromdate(datetime.date(year, month, day)) + \
                hours * 60 * 60 * 1000 + \
                minutes * 60 * 1000 + \
                seconds * 1000 + \
                milliseconds
            self._ticks = dt

    @staticmethod
    def parse(timestring, format_):
        '''
        Creates an instance by parsing <timestring> using <format>.

        >>> DateTime.parse("2007-05-07 19:22:11", "%Y-%m-%d %H:%M:%S")
        2007-05-07 19:22:11:000
        >>> DateTime.parse("2007-04-09 09:22:11", "%Y-%m-%d %H:%M:%S")
        2007-04-09 09:22:11:000
        >>> DateTime.parse("2007-04-09", "%Y-%m-%d")
        2007-04-09 00:00:00:000
        '''
        ts = time.strptime(timestring, format_)
        cticks = calendar.timegm(ts)
        return DateTime(ticks=cticks * 1000)

    @property
    def ticks(self):
        '''
        Gets the internal representation of date and time, which are ticks, meaning the number of
        milliseconds since the epoch.

        >>> from datetime import date
        >>> DateTime().ticks
        0
        >>> DateTime(ticks=300).ticks
        300L
        >>> DateTime(2000, 1, 1).ticks
        946684800000L
        >>>
        '''
        return self._ticks

    @property
    def date(self):
        ''' Returns the date part, that is a DateTime with a time of 00:00:00:000.

        >>> t = DateTime(2000, 3, 4) + Duration(ticks=5000)
        >>> t
        2000-03-04 00:00:05:000
        >>> t.date
        2000-03-04 00:00:00:000
        >>>
        '''
        return DateTime(ticks=self._ticks - self._ticks % DateTime.ticksperday)

    def totimeandms(self):
        '''
        Gets the date and time parts as a tuple holding (time.time, milliseconds).
        Since this method uses `time.gmtime`, errors with negative tick values
        can arise when using CPython (not in IronPython).

        This method is used internally but can also serve as an interface to python's standard library time.

        >>> DateTime(2011, 4, 5, 22, 00, 14).totimeandms()
        (time.struct_time(tm_year=2011, tm_mon=4, tm_mday=5, tm_hour=22, tm_min=0, tm_sec=14, tm_wday=1, tm_yday=95, tm_isdst=0), 0L)
        >>> DateTime(2011, 4, 5, 22, 00, 14, 333).totimeandms()
        (time.struct_time(tm_year=2011, tm_mon=4, tm_mday=5, tm_hour=22, tm_min=0, tm_sec=14, tm_wday=1, tm_yday=95, tm_isdst=0), 333L)
        >>> DateTime().totimeandms()
        (time.struct_time(tm_year=1970, tm_mon=1, tm_mday=1, tm_hour=0, tm_min=0, tm_sec=0, tm_wday=3, tm_yday=1, tm_isdst=0), 0)
        '''
        sec, millisec = divmod(self._ticks, 1000)
        return time.gmtime(sec), millisec

    @staticmethod
    def _getticksfromdate(date):
        ''' Gets the ticks from a datetime.date value '''
        return (date.toordinal() - 719163) * DateTime.ticksperday

    def __repr__(self):
        ts, milliseconds = self.totimeandms()
        return '{:04}-{:02}-{:02} {:02}:{:02}:{:02}:{:03}' \
            .format(ts[0], ts[1], ts[2], ts[3], ts[4], ts[5], milliseconds)

# pylint: disable-msg=W0212

    # equality
    def __eq__(self, other):
        '''
        >>> DateTime() == DateTime()
        True
        >>> DateTime(2011, 1, 2, 3, 4, 5) == DateTime(2011, 1, 2, 3, 4, 5)
        True
        >>> DateTime(2011, 1, 2, 3, 4, 999) == DateTime(2011, 1, 2, 3, 4, 5)
        False
        >>>
        '''
        if isinstance(other, DateTime):
            return self._ticks == other._ticks
        if isinstance(other, long) or isinstance(other, int):
            return self._ticks == other
        raise ValueError('comparison of date with invalid type')

    def __ne__(self, other):
        '''
        >>> DateTime() != DateTime()
        False
        >>> DateTime(2011, 1, 2, 3, 4, 5) != DateTime(2011, 1, 2, 3, 4, 5)
        False
        >>> DateTime(2011, 1, 2, 3, 4, 999) != DateTime(2011, 1, 2, 3, 4, 5)
        True
        '''
        return self._ticks != other._ticks

    # comparison
    def __lt__(self, other):
        '''
        >>> DateTime(100) < DateTime(110)
        True
        >>> DateTime(100) < DateTime(101)
        True
        >>> DateTime(100) < DateTime(100)
        False
        >>> DateTime(100) < DateTime(99)
        False
        '''
        return self._ticks < other._ticks

    def __le__(self, other):
        '''
        >>> DateTime(100) <= DateTime(110)
        True
        >>> DateTime(100) <= DateTime(101)
        True
        >>> DateTime(100) <= DateTime(100)
        True
        >>> DateTime(100) <= DateTime(99)
        False
        '''
        return self._ticks <= other._ticks

    def __gt__(self, other):
        '''
        >>> DateTime(100) > DateTime(110)
        False
        >>> DateTime(100) > DateTime(101)
        False
        >>> DateTime(100) > DateTime(100)
        False
        >>> DateTime(100) > DateTime(99)
        True
        '''
        return self._ticks > other._ticks

    def __ge__(self, other):
        '''
        >>> DateTime(100) >= DateTime(110)
        False
        >>> DateTime(100) >= DateTime(101)
        False
        >>> DateTime(100) >= DateTime(100)
        True
        >>> DateTime(100) >= DateTime(99)
        True
        '''
        return self._ticks >= other._ticks

    # add
    def __add__(self, rhs):
        '''
        >>> DateTime() + Duration()
        1970-01-01 00:00:00:000
        >>> DateTime(ticks=10) + Duration()
        1970-01-01 00:00:00:010
        >>> DateTime(ticks=10) + Duration(ticks=3)
        1970-01-01 00:00:00:013
        >>> DateTime(ticks=10) + Duration(ticks=-17)
        1969-12-31 23:59:59:993
        >>> t = DateTime()
        >>> t
        1970-01-01 00:00:00:000
        >>> t += Duration(ticks=77)
        >>> t
        1970-01-01 00:00:00:077
        '''
        if isinstance(rhs, Duration):
            return DateTime(ticks=self._ticks + rhs._ticks)
        raise ValueError('only a Duration can be added to a time')

    # integral type
    def __trunc__(self):
        return self

    def __int__(self):
        return self._ticks


class Duration:
    '''
    Stores a duration as number of milliseconds. In combination with `DateTime`
    provides time arithmetic.

    >>> Duration(ticks=7000)      # 7000 milliseconds
    0 days 00:00:07:000
    >>> Duration(days=3)          # factory functions
    3 days 00:00:00:000
    >>> Duration(days=14) + Duration(hours=3) + 144
    14 days 03:00:00:144

    Initialize a duration from a number holding its milliseconds.

    >>> from teafiles.clockwise import *
    >>> Duration()
    0 days 00:00:00:000
    >>> Duration(ticks=3)
    0 days 00:00:00:003
    >>> Duration(ticks=1003)
    0 days 00:00:01:003
    >>> Duration(ticks=86400 + 1050)
    0 days 00:01:27:450
    >>> Duration(ticks=86400000 + 1050)
    1 days 00:00:01:050
    '''

    MILLISECOND = 1
    SECOND = 1000 * MILLISECOND
    MINUTE = 60 * SECOND
    HOUR = 60 * MINUTE
    DAY = 24 * HOUR

    def __init__(self, weeks=0, days=0, hours=0, minutes=0, seconds=0, milliseconds=0, ticks=None):

        if not ticks:
            ticks = milliseconds
            ticks += Duration.SECOND * seconds
            ticks += Duration.MINUTE * minutes
            ticks += Duration.HOUR * hours
            ticks += Duration.DAY * days
            ticks += 7 * Duration.DAY * weeks

        self._ticks = long(ticks)   # ticks shall always be integers

    @property
    def ticks(self):
        '''
        Returns the underlying number of ticks, that is the number of milliseconds.

        >>> Duration(ticks=1033).ticks
        1033L
        '''
        return self._ticks

    def totimedelta(self):
        '''
        Converts the duration to a `datetime.timedelta` instance.

        >>> Duration(ticks=33).totimedelta()
        datetime.timedelta(0, 0, 33000)
        >>> Duration(seconds=33).totimedelta()
        datetime.timedelta(0, 33)
        >>> Duration(minutes=33).totimedelta()
        datetime.timedelta(0, 1980)
        >>> Duration(hours=33).totimedelta()
        datetime.timedelta(1, 32400)
        >>> Duration(days=33).totimedelta()
        datetime.timedelta(33)
        '''
        return datetime.timedelta(milliseconds=self._ticks)

# pylint: disable-msg=W0212

    def __add__(self, other):
        '''
        Adds another duration or integer (interpreted as milliseconds).

        >>> Duration(days=4) + Duration(hours=7)
        4 days 07:00:00:000

        >>> Duration(days=4) + 3000
        4 days 00:00:03:000
        '''
        if isinstance(other, Duration):
            return Duration(ticks=self._ticks + other._ticks)
        elif isinstance(other, int) or isinstance(other, long):
            return Duration(ticks=self._ticks + other)
        raise ValueError("Invalid operand: Can add only int, long or instances of Duration to Duration")

    def __eq__(self, other):
        '''
        >>> Duration() == Duration()
        True
        >>> Duration() == Duration(ticks=3)
        False
        >>> Duration(ticks=3) == Duration(ticks=3)
        True
        '''
        return self._ticks == other.ticks

    def __ne__(self, other):
        '''
        >>> Duration() != Duration()
        False
        >>> Duration() != Duration(ticks=3)
        True
        >>> Duration(ticks=3) != Duration(ticks=3)
        False
        '''
        return self._ticks != other.ticks

    def __gt__(self, other):
        '''
        >>> Duration() > Duration()
        False
        >>> Duration() > Duration(ticks=3)
        False
        >>> Duration(ticks=3) > Duration(ticks=3)
        False
        >>> Duration(ticks=400) > Duration(ticks=3)
        True
        '''
        return self._ticks > other.ticks

    def __ge__(self, other):
        '''
        >>> Duration() >= Duration()
        True
        >>> Duration() >= Duration(ticks=3)
        False
        >>> Duration(ticks=3) >= Duration(ticks=3)
        True
        >>> Duration(ticks=400) >= Duration(ticks=3)
        True
        '''
        return self._ticks >= other.ticks

    def __lt__(self, other):
        '''
        >>> Duration() < Duration()
        False
        >>> Duration() < Duration(ticks=3)
        True
        >>> Duration(ticks=3) < Duration(ticks=3)
        False
        >>> Duration(ticks=400) < Duration(ticks=3)
        False
        '''
        return self._ticks < other.ticks

    def __le__(self, other):
        '''
        >>> Duration() <= Duration()
        True
        >>> Duration() <= Duration(ticks=3)
        True
        >>> Duration(ticks=3) <= Duration(ticks=3)
        True
        >>> Duration(ticks=400) <= Duration(ticks=3)
        False
        '''
        return self._ticks <= other.ticks

    def __repr__(self):
        '''
        Returns a string representation using the format "{} days {:02}:{:02}:{:02}:{:03}".
        '''
        days, remainder = divmod(self._ticks, Duration.DAY)
        hours, remainder = divmod(remainder, Duration.HOUR)
        minutes, remainder = divmod(remainder, Duration.MINUTE)
        seconds, remainder = divmod(remainder, Duration.SECOND)
        milliseconds = remainder
        return "{} days {:02}:{:02}:{:02}:{:03}".format(days, hours, minutes, seconds, milliseconds)

    def __trunc__(self):
        return self

    def __int__(self):
        return self._ticks

# pylint: enable-msg=W0212


#utils
def isdatetime(value):
    '''
    Returns true if `value` is an instance of DateTime.
    '''
    return isinstance(value, DateTime)


def isduration(value):
    '''
    Returns true if `value` is an instance of Duration.
    '''
    return isinstance(value, Duration)


# pimp range function
from __builtin__ import range as _range


def range(*args):   # pylint:disable-msg=W0622
    '''
    Overrides the range method, allowing DateTime ranges. Requires exactly 3 arguments to have effect (otherwise normal range method
    is called): start (DateTime), end (DateTime) and step (Duration)

    >>> for t in range(DateTime(2000, 9, 1), DateTime(2001, 1, 1), Duration(weeks=2)):
    ...     print t
    ...
    2000-09-01 00:00:00:000
    2000-09-15 00:00:00:000
    2000-09-29 00:00:00:000
    2000-10-13 00:00:00:000
    2000-10-27 00:00:00:000
    2000-11-10 00:00:00:000
    2000-11-24 00:00:00:000
    2000-12-08 00:00:00:000
    2000-12-22 00:00:00:000
    '''
    if len(args) == 3 and \
        isdatetime(args[0]) and isdatetime(args[1]) and isduration(args[2]):
        return _rangedate(*args)
    else:
        return _range(*args)


def _rangedate(start, stop, step):
    '''
    Returns an iterator (generator) of DateTime values. starting at `start` stopping before `stop`
    and a duration of `step` between.
    '''
    t = start.ticks
    stop = stop.ticks
    step = step.ticks
    while t < stop:
        yield DateTime(ticks=t)
        t += step


def rangen(startdate, stepduration, count):
    '''
    Simple creation of DateTime sequences. Generate <count> DateTimes starting
    with <startdate> incremented by <stepduration>.

    >>> for t in rangen(DateTime(2000, 9, 1), Duration(days=1), 10):
    ...     print t
    ...
    2000-09-01 00:00:00:000
    2000-09-02 00:00:00:000
    2000-09-03 00:00:00:000
    2000-09-04 00:00:00:000
    2000-09-05 00:00:00:000
    2000-09-06 00:00:00:000
    2000-09-07 00:00:00:000
    2000-09-08 00:00:00:000
    2000-09-09 00:00:00:000
    2000-09-10 00:00:00:000
    '''
    t = startdate.ticks
    step = stepduration.ticks
    while count:
        yield DateTime(ticks=t)
        t += step
        count -= 1


if __name__ == '__main__':
    import doctest
    import teafiles.clockwise
    doctest.testmod(teafiles.clockwise)
