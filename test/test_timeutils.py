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

''' pytest tests '''

import datetime

from teafiles.clockwise import *


def test_fromticks():
    dt = DateTime(ticks=500)
    assert dt.ticks == 500

    dt = DateTime(ticks=500.4)
    assert dt.ticks == 500


def test_equality():
    assert DateTime(1970, 1, 3) == DateTime(1970, 1, 3)
    assert DateTime(2001, 4, 5) == DateTime(2001, 4, 5)


def test_duration_ctor():
    d = Duration(hours=1)
    assert d.ticks == 60 * 60 * 1000

    d = Duration(hours=1.5)
    assert d.ticks == 60 * 60 * 1000 * 1.5


def test_duration_repr():
    d = Duration(hours=1)
    assert d.__repr__() == "0 days 01:00:00:000"
    d = Duration(hours=1.5)
    assert d.__repr__() == "0 days 01:30:00:000"


if __name__ == '__main__':
    test_duration_repr()
    test_duration_ctor()
    test_fromticks()
    test_equality()
