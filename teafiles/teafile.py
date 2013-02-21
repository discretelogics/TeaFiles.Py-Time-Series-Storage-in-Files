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
    tbd
'''

# pylint: disable-msg=W0232, W0142, W0122, C0301
# W0142:655,15:TeaFile.read: Used * or ** magic
# W0122:730,8:TeaFile._attachwritemethod: Use of the exec statement
# C0301:172,0: Line too long (104/80) - maybe trim docstrings later for terminal users

import struct
import uuid
from io import BytesIO
from collections import namedtuple
from teafiles.clockwise import DateTime

# if set to true, time fields are returned as instances of clockwise.DateTime, otherwise
USE_TIME_DECORATION = True


class TeaFile:
    '''
    Create, write and read or just inspect a file in the TeaFile format.

    1. **create** and **write** a teafile holding Time/Price/Volume
    items.

    >>> tf = TeaFile.create("acme.tea", "Time Price Volume", "qdq", "prices of acme at NYSE", {"decimals": 2, "url": "www.acme.com" })
    >>> tf.write(DateTime(2011, 3, 4,  9, 0), 45.11, 4500)
    >>> tf.write(DateTime(2011, 3, 4, 10, 0), 46.33, 1100)
    >>> tf.close()

    Note: Arguments of tf.write show up in intellisense with their names "Time", "Price" and "Volume".

    2. **read** a teafile. TeaFiles are self describung  a filename is sufficient, - we might have no clue what is inside the file, due to
    TeaFiles

    >>> tf = TeaFile.openread("acme.tea")
    >>> tf.read()
    TPV(Time=2011-03-04 09:00:00:000, Price=45.11, Volume=4500)
    >>> tf.read()
    TPV(Time=2011-03-04 10:00:00:000, Price=46.33, Volume=1100)
    >>> tf.read()
    >>> tf.close()

    Since the item structure is described in the file, we can always open the data items in the file.
    We can even do so on many platforms and with many applications, like from R on Linux, Mac OS or Windows,
    or using proprietary C++ or C# code.

    3. **describe**: See the `description` property about accessing the values passed to create. As a teaser, lets access
    the content description and namevalues collection for the file above:

    >>> tf.description.contentdescription
    u'prices of acme at NYSE'

    >>> tf.description.namevalues
    {u'url': u'www.acme.com', u'decimals': 2}
    '''

    #pylint:disable-msg=R0902,W0212

    # the factory methods at the module level, `create`, `openread` and `openwrite` should be used to create instances of this class.
    def __init__(self, filename):
        self.decimals = -1

        self._filename = filename   # we need the filename for the call to getsize in itemareaend()
        self.file = None

        self._description = None

        self.itemareastart = None
        self._itemareaend = None
        self.itemsize = None

        self.itemstruct = None
        self.nameditemtuple = None

        self.write = None

    @staticmethod
    def create(filename, fieldnames, fieldformat=None, contentdescription=None, namevalues=None):
        '''
        creates a new file and writes its header based on the description passed.
        leaves the file open, such that items can be added immediately. the caller must close the
        file finally.

        args:
            * **filename**:   The filename, that will internally be passed to io.open, so the same rules apply.
            * **fieldnames**: The name of fields passed either as a string that seperates each
              fieldname by whitespace or as a list ot strings
            * **fieldformat**: Holds a composed by the format character for each field.
              the format characters are those used by the struct module.
              *example: "qdd" means that items stored in the file have 3 fields, the first is of
              type int64, the second and third are double values.*
              If omitted, all fields are considered to be of type int64.
            * **contentdescription**: A teafile can store one contentdescription, a string that describes what the
              contents in the file is about. examples: "Weather NYC", "Network load", "ACME stock".
              Applications can use this string as the "title" of the time series, for instance in a chart.
            * **namevalues**: A collection of name-value pairs used to store descriptions about the file.
              Often additional properties, like the "data provider", "feed", "feed id", "ticker".
              By convention, the name "decimals" is used to store an integer describing how many
              numbers of decimals to be used to format floating point values. This api for instance makes
              use of this convention. Besides formatting, an application might also treat this number
              as the accuracy of floating point values.

        >>> from teafiles import *
        >>> tf = TeaFile.create("lab.tea", "Time Temperature Humidity", "qdd") # create a file with 3 fields of types int64, double, double
        >>> tf.write(DateTime(2011, 3, 1), 44.2, 33.7)
        >>> tf.write(DateTime(2011, 3, 2), 45.1, 31.8)
        >>> tf.close()
        >>> tf.itemcount
        2L

        note that itemcount is still accessible, even after the file is closed.
        '''
        tf = TeaFile(filename)

        # setup description
        tf._description = d = TeaFileDescription()
        id_ = ItemDescription.create(None, fieldnames, fieldformat)
        tf.itemstruct = id_.itemstruct
        d.itemdescription = id_
        d.contentdescription = contentdescription
        d.namevalues = namevalues
        d.timescale = TimeScale.java()

        # open file and write header

        tf.file = open(filename, "wb")
        hm = _HeaderManager()
        fio = _FileIO(tf.file)
        fw = _FormattedWriter(fio)
        wc = hm.writeheader(fw, tf._description)
        tf.itemareastart = wc.itemareastart
        tf._itemareaend = wc.itemareaend
        tf.itemsize = id_.itemsize

        tf._attachwritemethod()     # pylint:disable-msg=W0212

        tf.flush()
        return tf

    @staticmethod
    def openread(filename):
        '''
        Open a TeaFile for read only.

        >>> from teafiles import *
        >>> with TeaFile.create("lab.tea", "Time Temperature Humidity", "qdd") as tf:
        ...     tf.write(DateTime(2011, 3, 1), 44.2, 33.7)
        ...     tf.write(DateTime(2011, 3, 2), 45.1, 31.8)
        ...
        >>> from pprint import pprint
        >>> with TeaFile.openread("lab.tea") as tf:
        ...         pprint(list(tf.items()))
        ...
        [TTH(Time=2011-03-01 00:00:00:000, Temperature=44.2, Humidity=33.7),
         TTH(Time=2011-03-02 00:00:00:000, Temperature=45.1, Humidity=31.8)]

        The instance demonstrates that is is not writable by not having a write method at all:

        >>> tf.write == None
        True
        '''
        tf = TeaFile._open(filename, "rb")
        return tf

    @staticmethod
    def openwrite(filename):
        '''
        Open a TeaFile for read and write.

        The file returned will have its *filepointer set to the end of the file*, as this function
        calls seekend() before returning the TeaFile instance.

        >>> with TeaFile.create('lab.tea', 'A B') as tf:
        ...     for i in range(3):
        ...         tf.write(i, 10*i)
        ...
        >>> TeaFile.printitems("lab.tea")
        [AB(A=0, B=0), AB(A=1, B=10), AB(A=2, B=20)]
        >>>
        >>> with TeaFile.openwrite('lab.tea') as tf:  # open the file to add more items
        ...     tf.write(7, 77)
        ...
        >>> TeaFile.printitems("lab.tea")
        [AB(A=0, B=0), AB(A=1, B=10), AB(A=2, B=20), AB(A=7, B=77)]

        '''
        tf = TeaFile._open(filename, "r+b")
        tf._attachwritemethod()     # pylint: disable-msg=W0212
        tf.seekend()                # this is what one would expect: writes append to the file
        return tf

    @staticmethod
    def _open(filename, mode):
        ''' internal open method, used by openread and openwrite '''
        tf = TeaFile(filename)
        tf.file = open(filename, mode)
        fio = _FileIO(tf.file)
        fr = _FormattedReader(fio)
        hm = _HeaderManager()
        rc = hm.readheader(fr)
        tf._description = rc.description
        id_ = tf._description.itemdescription
        if id_:
            tf.itemsize = id_.itemsize
            tf.itemstruct = id_.itemstruct
            tf.nameditemtuple = id_.itemtype
        tf.itemareastart = rc.itemareastart
        tf._itemareaend = rc.itemareaend

        nvs = tf._description.namevalues
        if nvs and nvs.get("decimals"):
            tf.decimals = nvs["decimals"]
        return tf

#pylint:enable-msg=W0212

    # read & write
    def read(self):
        '''
        Read then next item at the position of the file pointer. If no more items exist, None is returned.

        >>> with TeaFile.create('lab.tea', 'A B') as tf:
        ...     for i in range(3):
        ...         tf.write(i, 10*i)
        ...
        >>> tf = TeaFile.openread('lab.tea')
        >>> tf.read()
        AB(A=0, B=0)
        >>> tf.read()
        AB(A=1, B=10)
        >>> tf.read()
        AB(A=2, B=20)
        >>> tf.read()
        >>>
        '''
        itembytes = self.file.read(self.itemsize)
        if not itembytes:
            return None
        itemvalues = self.itemstruct.unpack(itembytes)
        adjusteditemvalues = [f.getvalue(itemvalues) for f in self._description.itemdescription.fields]
        tupelized = tuple(adjusteditemvalues)
        return self.nameditemtuple(*tupelized)

    def _write(self, *itemvalues):
        '''
        Internal item write method accepting a value for each field.

        A **typed write method** will be created inside the create and openwrite methods, available
        as **write(field1, field2, ....)**.

        >>> tf = TeaFile.create("acme.tea", "Time Price Volume", "qdq", "prices of acme at NYSE", {"decimals": 2, "url": "www.acme.com" })
        >>> tf.write(DateTime(2011, 3, 4,  9, 0), 45.11, 4500)
        >>> tf.write(DateTime(2011, 3, 4, 10, 0), 46.33, 1100)
        >>> tf.close()

        Note: Arguments of the tf.write show up in intellisense with their names "Time", "Price" and "Volume". This however works usually
        only in interactive shells, not in py-script editors, since they do not instantiate the class.
        '''
        if USE_TIME_DECORATION:
            itemvalues = tuple([f.decoratetime(itemvalues) for f in self.description.itemdescription.fields])
        bytes_ = self.itemstruct.pack(*itemvalues)
        self.file.write(bytes_)

    def flush(self):
        '''
        Flush buffered bytes to disk.

        When items are written via write, they do not land directly in the file, but are buffered in memory. flush
        persists them on disk. Since the number of items in a TeaFile is computed from the size of the file, the
        `itemcount` property is accuraty only after items have been flushed.

        >>> with TeaFile.create('lab.tea', 'A') as tf:
        ...     for i in range(3):
        ...         tf.write(i)
        ...
        >>> tf = TeaFile.openwrite('lab.tea')
        >>> tf.itemcount
        3L
        >>> tf.write(71)
        >>> tf.itemcount
        3L
        >>> tf.flush()
        >>> tf.itemcount
        4L
        >>> tf.close()
        '''
        self.file.flush()

    def seekitem(self, itemindex):
        '''
        Sets the file pointer to the item at index `temindex`.

        >>> with TeaFile.create("lab.tea", "A") as tf:
        ...     for i in range(20):
        ...         tf.write(i)
        ...
        >>> tf = TeaFile.openread('lab.tea')
        >>> tf.read()
        A(A=0)
        >>> tf.read()
        A(A=1)
        >>> tf.read()
        A(A=2)
        >>> tf.seekitem(7)
        >>> tf.read()
        A(A=7)
        >>> tf.seekitem(2)
        >>> tf.read()
        A(A=2)
        >>> tf.close()
        '''
        self.file.seek(self.itemareastart + itemindex * self.itemsize)

    def seekend(self):
        '''
        Sets the file pointer past the last item.

        >>> with TeaFile.create('lab.tea', 'A') as tf:
        ...     for i in range(10):
        ...         tf.write(i)
        ...
        >>> tf = TeaFile.openread('lab.tea')
        >>> tf.read()
        A(A=0)
        >>> tf.seekend()
        >>> tf.read()
        >>> # nothing returned, we are at the end of file
        >>> tf.close()
        '''
        self.file.seek(0, 2)    # SEEK_END

    def items(self, start=0, end=None):
        '''
        Returns an iterator over the items in the file allowing start and end to be passed as item index.
        Calling this method will modify the filepointer.

        Optional, the range of the iterator can be returned

        >>> with TeaFile.create('lab.tea', 'A') as tf:
        ...     for i in range(10):
        ...         tf.write(i)
        ...
        >>> tf = TeaFile.openread('lab.tea')
        >>> tf.items()
        <generator object items at 0x...>
        >>> list(tf.items())
        [A(A=0), A(A=1), A(A=2), A(A=3), A(A=4), A(A=5), A(A=6), A(A=7), A(A=8), A(A=9)]
        >>> list(tf.items(2, 4))
        [A(A=2), A(A=3)]
        >>> list(tf.items(1, 5))
        [A(A=1), A(A=2), A(A=3), A(A=4)]
        >>>
        '''
        self.seekitem(start)
        if not end:
            end = self.itemcount
        current = start
        while current < end:
            yield self.read()
            current += 1

    @property
    def itemcount(self):
        ''' The number of items in the file. '''
        return self._getitemareasize() / self.itemsize

    def _getitemareaend(self):
        ''' the end of the item area, as an integer '''
        import os
        if self._itemareaend:
            return self._itemareaend
        return os.path.getsize(self._filename)

    def _getitemareasize(self):
        ''' the item area size, as an integer '''
        return self._getitemareaend() - self.itemareastart

    def close(self):
        '''
        Closes the file.

        TeaFile implements the context manager protocol and using this protocol is prefered, so manually closing the file
        should be required primarily in interactive mode.
        '''
        self.file.close()

    # context manager protocol
    def __enter__(self):
        return self

    def __exit__(self, type_, value, tb):
        self.close()

    # information about the file and its contents
    @property
    def description(self):
        '''
        Returns the description of the file.

        TeaFile describe the structure of its items and annotations about its content in their header. This
        property returns this description which in turn (optionally) holds
        * the itemdescription describing field names, types and offsets
        * a contentdescription describing the content
        * a namevalue collection holding name-value pairs and
        * a timescale describing how time stored as numbers shall be interpreted as time.::

            tf = TeaFile.create('lab.tea', 'Time Price Volume', 'qdq', 'ACME stock', {'exchange': 'nyse', 'decimals': 2})
            tf.description
            # returns:

            ItemDescription
            Name:	TPV
            Size:	24
            Fields:
            [Time         Type:  Int64   Offset: 0   IsTime:0   IsEventTime:0,
             Price        Type: Double   Offset: 8   IsTime:0   IsEventTime:0,
             Volume       Type:  Int64   Offset:16   IsTime:0   IsEventTime:0]

            ContentDescription
            ACME stock

            NameValues
            {'feed': 'bluum', 'decimals': 2, 'exchange': 'nyse'}
            TimeScale
            Epoch:           719162
            Ticks per Day: 86400000
            Wellknown Scale:   Java

        Note that the description object remains valid even after the file is closed.

        '''
        return self._description

    def __repr__(self):
        return  "TeaFile('{}') {} items".format(self._filename, self.itemcount)

    def getvaluestring(self, field, item):
        '''
        Returns the string representation of an item, considerung the number of decimals if available.

        >>> tf = TeaFile.create('lab.tea', 'Time Price', 'qd', 'ACME stock', {'exchange': 'nyse', 'decimals': 2})
        >>> tf.write(DateTime(2010, 2, 3), 44.444444)
        >>> tf.write(DateTime(2010, 2, 3), 44.333333)
        >>> tf.close()
        >>> tf = TeaFile.openread('lab.tea')
        >>> item = tf.read()
        >>> item                                    # decimals=2 is not considered
        TP(Time=2010-02-03 00:00:00:000, Price=44.444444)
        >>> pricefield = tf.description.itemdescription.fields[1]
        >>> pricefield
        Price        Type: Double   Offset: 8   IsTime:0   IsEventTime:0
        >>> tf.getvaluestring(pricefield, item)     # decimals=2 is considered
        44.44
        '''
        value = field.getvalue(item)
        if(self.decimals != -1 and (field.fieldtype == 9 or field.fieldtype == 10)):
            value = round(value, self.decimals)
        elif(field.fieldtype == 1):
            value = round(value, self.decimals)
        return value

    #internals
    def _attachwritemethod(self):
        ''' generate specific write method with named arguments '''
        id_ = self._description.itemdescription
        commafields = ",".join(id_.fieldnames)
        methodcode = "def customWrite(self, " + commafields + "): self._write(" + commafields + ")"
        import types
        d = {}
        exec(methodcode, d)
        func = d["customWrite"]
        boundmethod = types.MethodType(func, self)
        self.write = boundmethod

    @staticmethod
    def printitems(filename, maxnumberofitems=10):
        '''
        Prints all items in the file. By default at most 10 items are printed.


        >>> with TeaFile.create("lab.tea", "A B") as tf:
        ...     for i in range(40):
        ...         tf.write(i, 10 * i)
        ...
        >>> TeaFile.printitems("lab.tea")
        [AB(A=0, B=0), AB(A=1, B=10), AB(A=2, B=20), AB(A=3, B=30), AB(A=4, B=40), AB(A=5, B=50), AB(A=6, B=60), AB(A=7, B=70), AB(A=8, B=80), AB(A=9, B=90)]
        10 of 40 items
        >>>
        >>> TeaFile.printitems("lab.tea", 5)
        [AB(A=0, B=0), AB(A=1, B=10), AB(A=2, B=20), AB(A=3, B=30), AB(A=4, B=40)]
        5 of 40 items
        >>>
        '''
        with TeaFile.openread(filename) as tf:
            from itertools import islice
            print(list(islice(tf.items(), maxnumberofitems)))
            if tf.itemcount > maxnumberofitems:
                print ("{} of {} items".format(maxnumberofitems, tf.itemcount))

    @staticmethod
    def printsnapshot(filename):
        '''
        Prints a snapshot of an existing file, that is its complete description and the first 5 items.

        Example output: ::

            >> TeaFile.printsnapshot('lab.tea')
            TeaFile('lab.tea') 40 items

            ItemDescription
            Name:	AB
            Size:	16
            Fields:
            [A            Type:  Int64   Offset: 0   IsTime:0   IsEventTime:0,
             B            Type:  Int64   Offset: 8   IsTime:0   IsEventTime:0]

            ContentDescription
            None

            NameValues
            None

            TimeScale
            Epoch:           719162
            Ticks per Day: 86400000
            Wellknown Scale:   Java

            Items
            AB(A=0, B=0)
            AB(A=1, B=10)
            AB(A=2, B=20)
            AB(A=3, B=30)
            AB(A=4, B=40)
        '''
        with TeaFile.openread(filename) as tf:
            print(tf)
            print("")
            print(tf.description)
            print("Items")
            for item in tf.items(0, 5):
                print(item)


class _ValueKind:   # pylint: disable-msg=R0903
    ''' enumeration type, describing the type of a value inside a name-value pair '''
    Invalid, Int32, Double, Text, Uuid = [0, 1, 2, 3, 4]


def _getnamevaluekind(value):
    ''' returns the `_ValueKind' based on the for the passed `value` '''
    if isinstance(value, int):
        return _ValueKind.Int32
    if isinstance(value, float):
        return _ValueKind.Double
    if isinstance(value, basestring):
        return _ValueKind.Text
    if isinstance(value, uuid):
        return _ValueKind.Uuid
    raise ValueError("Invalid type inside NameValue")


class TimeScale:
    '''
    The TeaFile format is time format agnostic. Times in such file can be integral or float values
    counting seconds, milliseconds from an epoch like 0001-01-01 or 1970-01-01. The epoch together
    with the tick size define the `time scale` modeled by this class. These values are stored in the file.

    In order to support many platforms, the epoch value of 1970-01-01 and a tick size of Milliseconds is recommended.
    Moreover, APIs for TeaFiles should primarily support this time scale before any other, to allow exchange
    between applications and operating systems. In this spirit, the clockwise module in this package uses this
    1970 / millisecond time scale.
    '''
    def __init__(self, epoch, ticksperday):
        self._epoch = epoch
        self._ticksperday = ticksperday

    @staticmethod
    def java():
        '''
        Returns a TimeScale instance with the epoch 1970-01-01 and millisecond resolution.
        This time scale is that used by Java, so we call this the Java TimeScale.
        '''
        return TimeScale(719162, 86400000)

    @property
    def wellknownname(self):
        ''' Returns 'Java' if epoch == 719162 (1970-01-01) and ticksperday == 86400 * 1000.
            Returns 'Net' if epoch == 0 (0001-01-01) and ticksperday == 86400 * 1000 * 1000 * 10.
            Returns None otherwise.
        '''
        if self._epoch == 719162 and self._ticksperday == 86400000:
            return "Java"
        if self._epoch == 0 and self._ticksperday == 864000000000:
            return "Net"
        return None

    def __repr__(self):
        s = "Epoch:         {:>8}\nTicks per Day: {:>8}\n" \
                .format(self._epoch, self._ticksperday)
        wnn = self.wellknownname
        if wnn:
            s += "Wellknown Scale:{:>7}\n".format(wnn)
        return s


class _FileIO:
    ''' FileIO provides the ability to read int32, int64, double and byte lists from a file '''

    def __init__(self, iofile):
        self.file = iofile

    # read
    def readint32(self):
        ''' read a 32bit signed integer from the file '''
        bytes_ = self.file.read(4)
        value = struct.unpack("i", bytes_)[0]
        return value

    def readint64(self):
        ''' read a 64bit signed integer from the file '''
        bytes_ = self.file.read(8)
        value = struct.unpack("q", bytes_)[0]
        return value

    def readdouble(self):
        ''' read a double from the file '''
        bytes_ = self.file.read(8)
        value = struct.unpack("d", bytes_)[0]
        return value

    def readbytes(self, n):
        ''' read `n` bytes from the file '''
        return self.file.read(n)

    # write
    def writeint32(self, value):
        ''' write a 32bit signed integer to the file '''
        bytes_ = struct.pack("i", value)
        assert len(bytes_) == 4
        self.file.write(bytes_)

    def writeint64(self, value):
        ''' write a 64bit signed integer to the file '''
        bytes_ = struct.pack("q", value)
        assert len(bytes_) == 8
        self.file.write(bytes_)

    def writedouble(self, value):
        ''' write a double to the file '''
        bytes_ = struct.pack("d", value)
        assert len(bytes_) == 8
        self.file.write(bytes_)

    def writebytes(self, bytes_):
        ''' write the list of byte to the file '''
        self.file.write(bytes_)

    # position
    def skipbytes(self, bytestoskip):
        ''' skip `bytestoskip` in the file. increments the file pointer '''
        self.file.read(bytestoskip)

    def position(self):
        ''' returns the file pointer '''
        return self.file.tell()


class _FormattedReader:
    ''' Provides formatted reading of a `_FileIO` instance.'''

    def __init__(self, fio):
        self.fio = fio

    def readint32(self):
        ''' read int32 '''
        return self.fio.readint32()

    def readint64(self):
        ''' read int64 '''
        return self.fio.readint64()

    def readdouble(self):
        ''' read double '''
        return self.fio.readdouble()

    def readbytes_lengthprefixed(self):
        ''' read bytes, length prefixed '''
        n = self.readint32()
        return self.fio.readbytes(n)

    def readtext(self):
        ''' read a unicode string in utf8 encoding '''
        return self.readbytes_lengthprefixed().decode("utf8")

    def readuuid(self):
        ''' read a uuid '''
        bytes16 = self.fio.readbytes(16)
        return uuid.UUID(bytes=bytes16)

    def skipbytes(self, bytestoskip):
        ''' skip `bytestoskip` bytes '''
        self.fio.skipbytes(bytestoskip)

    def position(self):
        ''' returns the position of the filepointer '''
        return self.fio.position()

    def readnamevalue(self):
        ''' returns a dictionary holding a single name : value pair '''
        name = self.readtext()
        kind = self.readint32()
        if kind == _ValueKind.Int32:
            value = self.readint32()
        elif kind == _ValueKind.Double:
            value = self.readdouble()
        elif kind == _ValueKind.Text:
            value = self.readtext()
        elif kind == _ValueKind.Uuid:
            value = self.readuuid()
        return {name: value}


class _FormattedWriter:

    def __init__(self, fio):
        self.fio = fio

    def writeint32(self, int32value):
        ''' write an int32 value '''
        self.fio.writeint32(int32value)

    def writeint64(self, int64value):
        ''' write an int64 value '''
        self.fio.writeint64(int64value)

    def writedouble(self, doublevalue):
        ''' write a double value '''
        self.fio.writedouble(doublevalue)

    def writebytes_lengthprefixed(self, bytes_):
        ''' writes the `bytes` prefixed with their length '''
        self.writeint32(len(bytes_))
        self.fio.writebytes(bytes_)

    def writeraw(self, bytes_):
        ''' write `bytes` without length prefixing them '''
        self.fio.writebytes(bytes_)

    def writetext(self, text):
        ''' write `text` in UTF8 encoding '''
        self.writebytes_lengthprefixed(text.encode("utf8"))   # todo: is this encoding right?

    def writeuuid(self, uuidvalue):
        ''' Not implemented yet. writes `uuidvalue` into the file. '''
        raise Exception("cannot write uuid, feature not yet implemented. uuid={}{}".format(self, uuidvalue))
        #bytes16 = self.fio.writebytes(16)
        #return uuid.UUID(bytes=bytes16)

    def skipbytes(self, bytestoskip):
        ''' skip `bytestoskip` '''
        self.fio.skipbytes(bytestoskip)

    def position(self):
        ''' return the position (the file pointer '''
        return self.fio.position()

    def writenamevalue(self, key, value):
        ''' write a name/value pair '''
        kind = _getnamevaluekind(value)
        self.writetext(key)
        self.writeint32(kind)
        if kind == _ValueKind.Int32:
            self.writeint32(value)
        elif kind == _ValueKind.Double:
            self.writedouble(value)
        elif kind == _ValueKind.Text:
            self.writetext(value)
        elif kind == _ValueKind.Uuid:
            self.writeuuid(value)


# descriptions
class TeaFileDescription:
    '''
    Holds the description of a time series. Its attributes are the
        itemdescription, describing the item's fields and layout
        contentdescription, a simple string describing what the time series is about
        namevalues, a collection of name-value pairs holding int32,double,text or uuid values and the
        timescale, describing the format of times inside the file
    '''
    #pylint: disable-msg=R0903

    def __init__(self):
        self.itemdescription = None
        self.contentdescription = None
        self.namevalues = None
        self.timescale = None

    def __repr__(self):
        return "ItemDescription\n{}" \
               "\n\nContentDescription\n{}" \
               "\n\nNameValues\n{}" \
               "\n\nTimeScale\n{}" \
                .format(self.itemdescription, \
                    self.contentdescription, \
                    self.namevalues, \
                    self.timescale)


class ItemDescription:
    '''
    The item description describes the item type.
    Each teafile is a homogenous collection of items and an instance of this class describes
    the fields of this item, that is

        the name of each field
        the field's offset inside the item
        its type.
    '''
    def __init__(self):
        self.itemsize = 0
        self.itemname = ""
        self.fields = []
        self.itemstruct = None  # the struct for marshalling to the file
        self.itemtype = None    # the named tuple class used for items
        self.fieldnames = None

    def __repr__(self):
        from pprint import pformat
        return "Name:\t{}\nSize:\t{}\nFields:\n{}" \
            .format(self.itemname, self.itemsize, pformat(self.fields))

    @staticmethod
    def create(itemname, fieldnames, fieldformat):
        '''
        Creates an ItemDescription instance to be used for the creation of a new TeaFile.

        itemname is the name for the items in the file (eg "Tick")
        fieldnames is a list of the names (eg ["Time", "Price", "Volume"]).
        Alternatively, fieldnames is a string that holds fieldnames separated
        by whitspace ("Time Price Volume")

        fieldformat specifies the layout of the item as used by
        struct.pack(fmt, ...). However the following restrictions apply:

            1. the repeat oerator is not allowed. So while "4h" means the same as
            "hhhh" for struct.pack/unpack, this method allows only the latter
            without repeat number.
            2. padding bytes (format character 'x') are not available.
            3. Only these formats are allowed:
            "b", "h", "i", "q", "B", "H", "I", "Q", "f", "d".
        '''

        id_ = ItemDescription()

        # prepare arguments
        if not isinstance(fieldnames, list):
            fieldnames = fieldnames.split()
        id_.fieldnames = fieldnames
        if not itemname:
            itemname = "".join([s[0] for s in fieldnames])

        if not fieldformat:
            fieldformat = "q" * len(fieldnames)

        id_.itemtype = namedtuple(itemname, fieldnames)
        id_.itemstruct = struct.Struct(fieldformat)
        id_.itemname = itemname

        # ensure fieldformat has no repeat numbers
        if not set(fieldformat).isdisjoint("0123456789"):
            raise ValueError("fieldformat contains digits. change format such that no digits occur")
        # remove byte order specifiers used by the struct module
        fieldformat = "".join([c for c in fieldformat if not c in "@<>=!"])
        if len(fieldformat) != len(fieldnames):
            raise Exception("fieldformat has different number of characters than fieldnames: " + \
                fieldformat + "(" + str(len(fieldformat)) + ") vs " + \
                ",".join(fieldnames) + "(" + str(len(fieldnames)) + ")")
        # create Fields
        i = 0
        for fname in fieldnames:
            f = Field()
            f.name = fname
            f.index = i
            f.formatchar = fieldformat[i]
            f.fieldtype = FieldType.getfromformatcharacter(f.formatchar)
            i += 1
            id_.fields.append(f)

        # analyze and assign offsets
        _analyzefieldoffsets(id_)
        id_._adjustitemstructforpadding(fieldformat)    # pylint: disable-msg=W0212
        return id_

    def _adjustitemstructforpadding(self, fieldformat):
        ''' we add trailing padding bytes after layout analysis, because it does not matter there '''
        itemalignment = max(FieldType.getsize(f.fieldtype) for f in self.fields)
        rawsize = self.itemstruct.size
        itempadding = itemalignment - (rawsize % itemalignment)
        if itempadding == itemalignment:
            itempadding = 0
        self.itemsize = rawsize + itempadding
        if itempadding:
            fieldformat += str(itempadding) + "x"
            self.itemstruct = struct.Struct(fieldformat)

    def getfieldbyoffset(self, offset):
        ''' Returns a field given its offset '''
        for f in self.fields:
            if f.offset == offset:
                return f
        print("field not found at offset{0}".format(offset))
        raise RuntimeError()

    def setupfromfields(self):
        ''' When a TeaFile is read from file, the fields are created and appended to this instance.
            This method sets up all remaining fields '''
        self.fieldnames = [self._getsafename(f.name) for f in self.fields]
        for f in self.fields:
            f.size = FieldType.getsize(f.fieldtype)
        self.itemtype = namedtuple(self._getsafename(self.itemname), self.fieldnames)
        fieldformat = "".join([FieldType.getformatcharacter(f.fieldtype) for f in self.fields])
        self.itemstruct = struct.Struct(fieldformat)
        self._adjustitemstructforpadding(fieldformat)

    @staticmethod
    def _getsafename(name):
        ''' convert item or field name to a name valid for namedtuple '''
        validchars = '_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return ''.join(c for c in name if c in validchars)


def _analyzefieldoffsets(itemdescription):
    ''' analyzes the itemdescription to find how it will be layouted '''
    id_ = itemdescription
    import array
    buffer_ = array.array('b', [0] * id_.itemstruct.size)
    for f in id_.fields:
        fts = FieldType.getsize(f.fieldtype)
        for pos in range(0, id_.itemstruct.size - fts + 1):
            magic = FieldType.getmagicvalue(f.fieldtype)
            struct.pack_into(f.formatchar, buffer_, pos, magic)
            testitem = id_.itemstruct.unpack(buffer_)
            struct.pack_into(f.formatchar, buffer_, pos, 0)  # reset buffer
            if testitem[f.index] == magic:
                f.offset = pos
                break
    return None


class FieldType:
    ''' An enumeration of field types and utility functions related to. '''

    Int8, Int16, Int32, Int64, UInt8, UInt16, UInt32, UInt64, Float, Double = \
        _formatNumbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    _typeNames = [None, "Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "Float", "Double"]
    _typesizes = [1, 2, 4, 8, 1, 2, 4, 8, 4, 8]
    _formatCharacters = ["b", "h", "i", "q", "B", "H", "I", "Q", "f", "d"]
    _magicValues = [0, 0x71, 0x7172, 0x71727374, 0x7172737475767778, 0xa1, 0xa1a2, 0xa1a2a3a4, 0xa1a2a3a4a5a6a7a8, 1.01, 3.07]

    @staticmethod
    def getsize(fieldtype):
        ''' get the size of a field type '''
        i = FieldType._formatNumbers.index(fieldtype)
        return FieldType._typesizes[i]

    @staticmethod
    def getfromformatcharacter(c):
        ''' get the field type given its formatting character as used by the `struct` module '''
        try:
            i = FieldType._formatCharacters.index(c)
            return FieldType._formatNumbers[i]
        except:
            raise ValueError("Invalid format character: " + c)

    @staticmethod
    def getformatcharacter(fieldtype):
        ''' get the formatting character of a field type, as used by the `struct` module '''
        try:
            i = FieldType._formatNumbers.index(fieldtype)
            return FieldType._formatCharacters[i]
        except:
            raise ValueError("Invalid fieldtype: " + fieldtype)

    @staticmethod
    def getmagicvalue(fieldtype):
        ''' given a fieldtype, get a magic value. This is used for analyzing the item layout. '''
        return FieldType._magicValues[fieldtype]

    @staticmethod
    def getname(fieldtype):
        ''' get the string representation of `fieldtype`` '''
        return FieldType._typeNames[fieldtype]


class Field:
    '''
    Describes a field inside an item.

    Attributes are:
        * name
        * offset
        * istime
        * iseventtime
        * index
        * formatchar
    '''
    #pylint:disable-msg=R0903
    def __init__(self):
        self.name = ""
        self.offset = None
        self.fieldtype = None
        self.istime = False
        self.iseventtime = False
        self.index = None
        self.formatchar = None

    def getvalue(self, item):
        ''' Given a field and an item, returns the value of this field.

        If the field is a time field, the value is packed into a `Time`, unless
        configured otherwise by setting `use_time_decoration` to False.
        '''
        value = item[self.index]
        if self.istime:
            value = DateTime(ticks=value)
        return value

    def decoratetime(self, item):
        value = item[self.index]
        if isinstance(value, DateTime):
            value = value.ticks     # unpack time into its ticks
        return value

    def __repr__(self):
        return "{:10}   Type:{:>7}   Offset:{:>2}   IsTime:{}   IsEventTime:{}".format(self.name, FieldType.getname(self.fieldtype), self.offset, int(self.istime), int(self.iseventtime))


# context, section formatters
class _ReadContext:
    ''' context used for header reading '''
    #pylint:disable-msg=R0903
    def __init__(self, formattedreader):
        self.reader = formattedreader
        self.description = TeaFileDescription()
        self.itemareastart = None
        self.itemareaend = None
        self.sectioncount = None


class _WriteContext:
    ''' context used for header writing '''
    #pylint:disable-msg=R0903
    def __init__(self, formattedwriter):
        self.writer = formattedwriter
        self.itemareastart = None
        self.itemareaend = None
        self.sectioncount = None
        self.description = None


# disable method could be function warnings for the formatters read/write methods. check back later if and how this could be done more pythonesk
#pylint:disable-msg=R0201

class _ItemSectionFormatter:
    ''' reads and writes the itemdescription into / from the file '''
    id = 10

    def read(self, rc):
        ''' read the section '''
        id_ = ItemDescription()
        r = rc.reader
        id_.itemsize = r.readint32()
        id_.itemname = r.readtext()
        fieldcount = r.readint32()
        i = 0
        for _ in range(fieldcount):
            f = Field()
            f.index = i
            f.fieldtype = r.readint32()
            f.offset = r.readint32()
            f.name = r.readtext()
            id_.fields.append(f)
            i += 1
        id_.setupfromfields()
        rc.description.itemdescription = id_

    def write(self, wc):
        ''' writes the section '''
        id_ = wc.description.itemdescription
        w = wc.writer
        w.writeint32(id_.itemsize)
        w.writetext(id_.itemname)
        w.writeint32(len(id_.fields))
        for f in id_.fields:
            w.writeint32(f.fieldtype)
            w.writeint32(f.offset)
            w.writetext(f.name)


class _ContentSectionFormatter:
    ''' reads and writes the contentdescription into / from the file '''
    id = 0x80

    def read(self, rc):
        ''' read the section '''
        r = rc.reader
        rc.description.contentdescription = r.readtext()

    def write(self, wc):
        ''' writes the section '''
        cd = wc.description.contentdescription
        if cd:
            wc.writer.writetext(cd)


class _NameValueSectionFormatter:
    ''' reads and writes the namevalue-description into / from the file '''
    id = 0x81

    def read(self, rc):
        ''' read the section '''
        r = rc.reader
        n = r.readint32()
        if n == 0:
            return
        nvc = {}
        while n > 0:
            nv = r.readnamevalue()
            nvc.update(nv)
            n = n - 1
        rc.description.namevalues = nvc

    def write(self, wc):
        ''' writes the section '''
        nvs = wc.description.namevalues
        if not nvs:
            return
        w = wc.writer
        w.writeint32(len(nvs))
        for key, value in nvs.items():
            w.writenamevalue(key, value)


class _TimeSectionFormatter:
    ''' reads and writes the timescale and description of time fields into / from the file '''
    id = 0x40

    def read(self, rc):
        ''' read the section '''
        r = rc.reader

        # time scale
        epoch = r.readint64()
        ticksperday = r.readint64()
        rc.description.timescale = TimeScale(epoch, ticksperday)

        # time fields
        timefieldcount = r.readint32()
        if timefieldcount == 0:
            return

        id_ = rc.description.itemdescription
        isfirsttimefield = True
        for _ in range(timefieldcount):
            o = r.readint32()
            f = id_.getfieldbyoffset(o)
            f.istime = True
            f.iseventtime = isfirsttimefield
            isfirsttimefield = False

    def write(self, wc):
        ''' writes the section '''
        w = wc.writer
        # this api restricts time formats to JavaTime
        # in addition, the first field named "time" is considered the EventTime
        w.writeint64(719162)        # days between 0001-01-01 and 1970-01-01
        w.writeint64(86400 * 1000)  # millisecond resolution
        id_ = wc.description.itemdescription
        timefields = [f for f in id_.fields if f.name.lower() == "time"]
        w.writeint32(len(timefields))   # will be 0 or 1
        for f in timefields:
            w.writeint32(f.offset)


class _HeaderManager:
    ''' reads and writes the file header, delegating the formatting of sections to the sectionformatters. '''
    def __init__(self):
        self.sectionformatters = ([
            _ItemSectionFormatter(),
            _ContentSectionFormatter(),
            _NameValueSectionFormatter(),
            _TimeSectionFormatter()])

    def getformatter(self, id_):
        ''' the a formatter given its id '''
        for f in self.sectionformatters:
            if f.id == id_:
                return f
        raise RuntimeError()

    def readheader(self, r):
        ''' read the file header '''
        rc = _ReadContext(r)
        bom = r.readint64()
        if bom != 0x0d0e0a0402080500:
            print("Byteordermark mismatch: ", bom)
            raise RuntimeError()
        rc.itemareastart = r.readint64()
        rc.itemareaend = r.readint64()
        rc.sectioncount = r.readint64()
        n = rc.sectioncount
        while n > 0:
            self.readsection(rc)
            n = n - 1
        bytestoskip = rc.itemareastart - r.position()   # padding bytes between header and item area
        r.skipbytes(bytestoskip)
        return rc

    def readsection(self, rc):
        ''' read a section '''
        r = rc.reader
        sectionid = r.readint32()
        nextsectionoffset = r.readint32()
        beforesection = r.position()
        f = self.getformatter(sectionid)
        f.read(rc)
        aftersection = r.position()
        if (aftersection - beforesection) > nextsectionoffset:
            print("section reads too many bytes")
            raise RuntimeError()

    def writeheader(self, fw, description):
        ''' write the file header '''
        wc = _WriteContext(fw)
        wc.itemareastart = 32
        wc.itemareaend = 0     # no preallocation
        wc.description = description
        wc.sectioncount = 0
        sectionbytes = self.createsections(wc)

        fw.writeint64(0x0d0e0a0402080500)
        fw.writeint64(wc.itemareastart)
        fw.writeint64(wc.itemareaend)
        fw.writeint64(wc.sectioncount)
        wc.writer.writeraw(sectionbytes)

        return wc

    def createsections(self, wc):
        ''' writing the sections into the file raises a small challange:
        before writing the first section, we need to know how many sections will follow, as the
        file format prefixes the section count before the actual sections.
        This implementation accomplishes this by writing the header first into memory, afterwards
        the sectioncount and the sections. Alternatives would be to move the file pointer or
        to enhance the sectionformatters such that they provide the section length without
        writing the section.
        '''
        saved = wc.writer
        sectionstream = BytesIO()
        sectionwriter = _FormattedWriter(_FileIO(sectionstream))
        pos = 32   # sections start at byte position 32
        for formatter in self.sectionformatters:
            payloadstream = BytesIO()
            wc.writer = _FormattedWriter(_FileIO(payloadstream))
            formatter.write(wc)
            payload = payloadstream.getvalue()
            size = len(payload)
            if size > 0:
                # section id
                sectionwriter.writeint32(formatter.id)
                pos += 4

                # nextSectionOffset
                sectionwriter.writeint32(size)
                pos += 4

                # payload
                sectionwriter.writeraw(payloadstream.getvalue())
                pos += size    # no padding or spacing done here

                wc.sectioncount += 1

        # padding
        paddingbytes = 8 - pos % 8
        if paddingbytes == 8:
            paddingbytes = 0
        if paddingbytes:
            padding = b"\0" * paddingbytes
            sectionwriter.writeraw(padding)
        wc.itemareastart = pos + paddingbytes  # first item starts padded on 8 byte boundary.

        wc.writer = saved
        return sectionstream.getvalue()

if __name__ == '__main__':
    import doctest, teafiles.teafile
    doctest.testmod(teafiles.teafile, optionflags = doctest.ELLIPSIS)
