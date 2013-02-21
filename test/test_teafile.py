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

import tempfile
import os
import sys
from teafiles import *

def setup_module(m):
    module = m
    module.testfiles = []

def gettempfilename():
    filename = tempfile.mktemp(".tea")
    module = sys.modules[__name__]
    module.testfiles.append(filename)
    return filename


def teardown_module(module):
    for filename in module.testfiles:
        os.remove(filename)


def gettempfilename():
    return tempfile.mktemp(".tea")


def test_create_and_read():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B C", "qqq") as tf:
        tf.write(1, 2, 3)
        tf.write(21, 22, 23)
    with TeaFile.openread(filename) as tf:
        assert tf.itemcount == 2
        item = tf.read()
        assert item
        assert item.A == 1
        assert item.B == 2
        assert item.C == 3
        item = tf.read()
        assert item
        assert item.A == 21
        assert item.B == 22
        assert item.C == 23
        assert not tf.read()


def test_itemarea_is_set_after_create():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B C", "qqq") as tf:
        assert tf.description.itemdescription.itemname == "ABC"
        assert tf.itemareastart > 32    # file holds item description, so item area starts after core header
        assert tf._getitemareaend() > 0
        assert tf._getitemareaend() == tf.itemareastart
        assert tf._getitemareasize() == 0
        assert tf.itemcount == 0


def test_itemarea_is_set_after_open():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B C") as tf:
        pass
    with TeaFile.openread(filename) as tf:
        assert tf.description.itemdescription.itemname == "ABC"
        assert tf.itemareastart > 0
        assert tf._getitemareaend() > 0
        assert tf._getitemareaend() == tf.itemareastart
        assert tf._getitemareasize() == 0
        assert tf.itemcount == 0


def test_itemcount():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B C", "qqq") as tf:
        assert tf.itemcount == 0
        for i in range(1, 11):
            tf.write(i, 22, 33)
            tf.flush()  # required, to update the filesize correctly
            assert tf.itemcount == i
    with TeaFile.openread(filename) as tf:
        assert tf.itemcount == 10


def test_seekitem():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B C", "qqq") as tf:
        for i in range(10):
            tf.write(i, 10 * i, 100 * i)
    with TeaFile.openread(filename) as tf:
        item = tf.read()
        assert len(item) == 3
        assert item[0] == 0
        assert item[1] == 0
        tf.seekitem(5)
        item = tf.read()
        assert item[0] == 5
        assert item[1] == 50
        tf.seekitem(2)
        item = tf.read()
        assert item[0] == 2
        assert item[1] == 20


def test_seekitem2():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B", "qq") as tf:
        tf.write(1, 1)
        tf.write(2, 2)
        tf.seekitem(0)
        tf.write(3, 3)
    with TeaFile.openread(filename) as tf:
        assert tf.read() == (3, 3)
        assert tf.read() == (2, 2)
    with TeaFile.openwrite(filename) as tf:
        tf.seekend()
        tf.write(4, 4)
        tf.write(5, 5)
    with TeaFile.openread(filename) as tf:
        assert tf.read() == (3, 3)
        assert tf.read() == (2, 2)
        assert tf.read() == (4, 4)
        assert tf.read() == (5, 5)


def test_openwrite():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B", "qq") as tf:
        for i in range(3):
            tf.write(i, i * 10)
    with TeaFile.openwrite(filename) as tf:
        tf.write(77, 770)
    with TeaFile.openread(filename) as tf:
        assert tf.read()[0] == 0
        assert tf.read()[0] == 1
        assert tf.read()[0] == 2
        assert tf.read()[0] == 77
    with TeaFile.openwrite(filename) as tf:
        tf.seekitem(0)
        tf.write(44, 440)
    with TeaFile.openread(filename) as tf:
        assert tf.read()[0] == 44
        assert tf.read()[0] == 1
        assert tf.read()[0] == 2
        assert tf.read()[0] == 77


def test_printsnapshot():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B C", "qqq", \
                        "here goes the content description!", \
                        {"data source": "Bluum", "decimals": 4}) as tf:
        tf.write(1, 2, 3)
        tf.write(2, 2, 3)
    TeaFile.printsnapshot(filename)


def test_namevalues():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B C", "qqq", "mycontent", {"a": 1, "bb": 22}) as tf:
        pass
    with TeaFile.openread(filename) as tf:
        nvs = tf.description.namevalues
        assert nvs["a"] == 1
        assert nvs["bb"] == 22
        assert len(nvs) == 2


def test_decimals():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B C", "qqq", "mycontent", {"decimals": 3, "bb": 22}) as tf:
        pass
    with TeaFile.openread(filename) as tf:
        nvs = tf.description.namevalues
        assert tf.decimals == 3


def test_items_iteration():
    filename = gettempfilename()
    with TeaFile.create(filename, "A B C", "qqq") as tf:
        tf.write(1, 2, 3)
        tf.write(21, 22, 23)
    with TeaFile.openread(filename) as tf:
        iter = tf.items()
        assert len([item for item in tf.items()]) == 2


if __name__ == '__main__':
    pass
    # to be run with pytest. for debugging purposes, tests may be executed here.

    #import sys
    #module = sys.modules[__name__]
    #setup_module(module)
    #
    #test_items_iteration()
    #
    #teardown_module(module)
