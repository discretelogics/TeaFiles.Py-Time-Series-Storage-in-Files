

Time Series Peristence
======================
This Python package provides Time Series storage in flat files according to the **TeaFile** file format.


In Use
======

>>> tf = TeaFile.create("acme.tea", "Time Price Volume", "qdq", "ACME at NYSE", {"decimals": 2, "url": "www.acme.com" })
>>> tf.write(DateTime(2011, 3, 4,  9, 0), 45.11, 4500)
>>> tf.write(DateTime(2011, 3, 4, 10, 0), 46.33, 1100)
>>> tf.close()

>>> tf = TeaFile.openread("acme.tea")
>>> tf.read()
TPV(Time=2011-03-04 09:00:00:000, Price=45.11, Volume=4500)
>>> tf.read()
TPV(Time=2011-03-04 10:00:00:000, Price=46.33, Volume=1100)
>>> tf.read()
>>> tf.close()


Exchange Time Series between Apps / OS
======================================
You can create, read and write TeaFiles with

- R,
- C++,
- C# or
- other applications

on

- Linux, Unix,
- Mac OS
- Windows


Python API Examples
===================
- programs        http://discretelogics.com/PythonAPI/examples.html
- interactive     http://discretelogics.com/PythonAPI/interactive.html
- examples.py (available in the package source)


TeaFiles
========
TeaFiles are a very **simple**, yet highly **efficient**, way to store time series data 
providing data exchange between programs written in C++, C# or applications like R, Octave, 
Matlab, running on Linux, Unix, Mac OS X or Windows.

- **Binary** data composed from elementary data types **signed and unsigned integers, double and float** in IEEE 754 format is prefixed by a **header** holding a description of the item structure and the content.
- Data can be directly accessed via **memory mapping**. 
- TeaFiles are **self describing**: Containing a description of the item structure they relieve opaqueness of straight binary files. Knowing that a file is a TeaFile is enough to access its data.

link to spec http://tbd


Scope of the Python API
=======================
The Python API makes TeaFiles accessible everywhere. It just needs a python installation on any OS to inspect the description and data 
of a TeaFile:


>>> # Show the decimals and displayname for all files in a folder:
...
>>> def showdecimals():
    ...     for filename in os.listdir('.'):
    ...         with TeaFile.openread(filename) as tf:
    ...             nvs = tf.description.namevalues
    ...             print('{} {} {}'.format(filename, nvs.get('Decimals'), nvs.get('DisplayName')))
    ... 
    >>> showdecimals()
    AA.day.tea 2 Alcoa, Inc.
    AA.tick.tea 2 Alcoa, Inc.
    AXP.day.tea 2 American Express Co.
    ...

Data download from web services is also a good fit. See the examples.py file in the package source for a Yahoo finance download function in about 30 lines.


Limitations
===========
When it comes to high performance processing of very large time series files, this API is currently not as fast as the C++ and C# APIs (Numbers coming soon on http://tbd). There are numerous ways to improve this if necessary, but no current plans at discretelogics to do so. Using the other languages/APIs is recommended. If you wish the Python API to be faster or want to work on that contact us.


Installation
============

**$ pip install teafiles**

package source with examples.py at http://bitbucket.org/discretelogics/teafiles.py

Tests
=====
Run the unit tests from the package root by

$ python -m pytest .\test


Python 2.7 / 3.2
================
Package tested under CPython 2.7.
Python 3.2 planned


Author
======
This API brought to you by discretelogics, company specialicing in time series analysis and event processing.
http://tbd


Version 0.7
===========
The current version is reasonably tested by doctests and some pytests. Better test coverage with unit tests (currently pytest is used) 
is desirable.

tbd towards version 1.0
    - enhance pytest coverage
    - consider api feedack
    - cleaner test runs, cleanup test files

optional
    - enhance performance after measuring it in python 3 (maybe struct module plays a minor role there)


License
=======
This package is released under the MIT LICENSE.


Feedback
========
Welcome at: pythonapi@discretelogics.com
