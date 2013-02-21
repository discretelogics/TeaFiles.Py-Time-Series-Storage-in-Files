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

import unittest
import os
import tempfile

import examples
from teafiles import *


def gettempfilename():
    return tempfile.mktemp(".tea")


def test_createticks():
    filename = gettempfilename()
    examples.createticks(filename, 10)
    assert os.path.exists(filename)
    assert os.path.getsize(filename) > 10 * 24
    with TeaFile.openread(filename) as tf:
        assert tf.itemcount == 10


def test_analyzeticks():
    filename = gettempfilename()
    examples.createticks(filename, 10)
    examples.analyzeticks(filename)


def test_sumprices():
    filename = gettempfilename()
    examples.createticks(filename, 10)
    examples.sumprices(filename)


def test_printsnapshot():
    filename = gettempfilename()
    examples.createticks(filename, 10)
    TeaFile.printsnapshot(filename)


if __name__ == '__main__':
    pass
    #test_createticks()
    #test_createticks()
    #test_analyzeticks()
    #test_sumprices()
    #test_printsnapshot()
