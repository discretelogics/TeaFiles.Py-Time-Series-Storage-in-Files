TeaFiles.Py - Time Series Storage in Files
==========================================

Use TeaFiles.Py to create, read and write files holding time series data.


In Use
------

>>> tf = TeaFile.create("acme.tea", "Time Price Volume", "qdq", "ACME at NYSE", {"decimals": 2, "url": "acme.com" })
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


Exchange Time Series across  Applications / Operating Systems
-------------------------------------------------------------

TeaFiles have a simple file layout, they contain raw binary data after a header that optionally holds metadata.
APis abstract the header layout and make file creation as simple as

>>> tf = TeaFile.create("acme.tea", "Time Price Volume", "qdq", "ACME at NYSE", {"decimals": 2, "url": "acme.com" })

At the moment, APIs exist for 

- C++,
- C#,
- Python (this one)
- other APis are planned and in draft phase (R, Octave/Matlab)

TeaFiles can be access from any operating system, like

- Linux / Unix
- Mac OS
- Windows


Python API Examples
-------------------
- programs        http://www.discretelogics.com/doc/teafiles.py/examples.html
- interactive     http://www.discretelogics.com/doc/teafiles.py/interactive.html
- examples.py (in the package source)


TeaFiles
--------
Find more about TeaFiles at http://www.discretelogics.com/teafiles


Documentation
-------------
http://www.discretelogics.com/doc/teafiles.py/


Scope of the Python API
-----------------------
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

Data download from web services for instance is a good fit. See the examples.py file in the package source for a Yahoo finance download function in about 30 lines.


Limitations
-----------
When it comes to high performance processing of very large time series files, this API is currently not as fast as the C++ and C# APIs. 
There are numerous ways to improve this if necessary, but no current plans at discretelogics to do so. Use of other languages/APIs is recommended. 
If you intend to make this Python API faster contact us we should be able to identify points of potential speed enhancements.


Installation
------------

The package is hosted on PyPi, so installation goes by

**$ pip install teafiles**

package source with examples.py at https://github.com/discretelogics/TeaFiles.Py

Tests
-----
Run the unit tests from the package root by

$ python -m pytest .\test


Python 2.7 / 3.2
----------------
Package tested under CPython 2.7.
Python 3.2 planned

Author
------
This API brought to you by discretelogics, company specialicing in time series analysis and event processing.
http://www.discretelogics.com

Version 0.7
-----------
The current version is reasonably tested by doctests and some pytests. Better test coverage with unit tests (currently pytest is used) is desirable.

open points towards version 1.0
    - pytest coverage
    - cleaner test runs, cleanup test files
  optional
    - enhance performance after measuring it in python 3 (struct module could play a crucial role, so results might differ considerably)

License
-------
This package is released under the MIT LICENSE.


Feedback
--------
Welcome at: office@discretelogics.com
