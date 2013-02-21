Python API for TeaFiles
=======================

pre release information
-----------------------

More information about TeaFiles and the TeaTime product line to follow soon (epected February 2012)


time series simple & efficient
------------------------------

TeaFiles provide a **very simple**, yet **highly efficient** way to store **time series data** in a way that allows **data exchange** between 
programs written in **C++, C#** or in applications like **R, Octave, Matlab** or others, running on Linux, Unix, Mac OS X or Windows.

TeaFiles store **binary data** composed from elementary data types signed and unsigned **integers, double and float** in IEEE 754 format. 
Data can be directly accessed via **memory mapping**. Since their header stores a description of the item structure, they relieve the opaqueness
of normal binary files and remain always accessible. In other words: Knowing that a file is a TeaFile is enough to access its data.


the api
------- 

    .. toctree::
       :maxdepth: 1

        teafiles  (TeaFile) <teafiles>
        clockwise (DateTime & Duration)<clockwise>

examples
--------

    .. toctree::
       :maxdepth: 1

        programs <examples>
        an interactive session <interactive>
