Examples
========

The examples below demonstrate how to accomplish common tasks with the Python TeaFiles API. They are mostly also available 
using APIs for C++ and C# to which they might be compared. The package source code holds the python code in the file 
examples.py in the root directory.


createticks
^^^^^^^^^^^

Shows how to create a TeaFile and write items into it. Useful for test file creation. ::

    import random
    from teafiles import *

    def createticks(filename, n, contentdescription=None, namevalues=None):
        with TeaFile.create(filename, "Time Price Volume", "qdq", contentdescription, namevalues) as tf:
            for t in rangen(DateTime(2000, 1, 1), Duration(minutes=1), n):    # increments n times by 1 minute
                r = random.random()
                tf.write(t, r * 100, int(r * 1000))


This function accepts a filename, the number of random ticks to write into the file and optionally 
a content description and name-value collection. Details about the code

    ::

        with TeaFile.create(filename, "Time Price", "qdq", contentdescription, namevalues) as tf:

Beside the filename, we pass :meth:`teafiles.TeaFile.create` the structure of our items as a list of *field names*, here 
**Time**, **Price** and **Volume**.

We then specify the respective *field type*, by passing the format string **"qd"**, that holds one character for each field.
The characters correspond to those used by the `struct module`_, so for here we defined thefields to have types int64, double and int64.

Content **description** is a simple string wile the name-value dictionary can hold for more structured descriptions. We pass both 
to store in the file.

Finally the **with** clause: TeaFile implements the context manager methods __enter__ and __exit__, guaranteeing that any open 
file will be closed when the with block is left, even if an exception occurs. It is highly recommended to always use TeaFile 
instances that way. Manual calls to :meth:`TeaFile.close()` should only be required in interactive sessions.

    ::

        tf.write(t, r * 100)

writes an item into the file. Note that this write method is dynamically created in the call to create and receives argument names "Time" and 
"Price" which is in particular convenient when using this api from an interactive commandline.



sumprices
^^^^^^^^^

Shows how to open a file and access its items. ::

    def sumprices(filename):
        with TeaFile.openread(filename) as tf:
            return sum(item.Price for item in tf.items())


Again we use a factory method to open the file, this time we use :meth:`teafiles.TeaFile.openread` to open the file in read only mode. The 
with statement ensure that the file is closed at the end.

    ::

        return sum(item.Price for item in tf.items())

We iterate over the items using items() which returns a generator (`generatoriterator`_) over all items which are named tuples like:

    ::

        >>> from pprint import pprint
        >>> tf = TeaFile.openread("lab.tea")
        >>> pprint(list(tf.items()))
        [TPV(Time=1970-01-01 00:00:00:000, Price=61.195988356060546, Volume=611),
         TPV(Time=1970-01-01 00:01:00:000, Price=56.2617855404688, Volume=562),
         TPV(Time=1970-01-01 00:02:00:000, Price=0.3000058069409506, Volume=3)
         ...
         ]


scenario: data cleansing
^^^^^^^^^^^^^^^^^^^^^^^^

ACME company receives data from stock exchanges holding prices and volums of transactions. Each transaction is stored as a 
"Tick" (Time, Price, Volume), one file per financial instrument. Clara is responsible to monitor the quality of the data
stored in the files. It happens that ticks come in with wrong numbers, like a price of 0, or a price obviously out of 
reasonable range. It even happens that ticks are missing. Each day, Clara has to check 3000 files and make sure that
their data is reasonable. To quickly identify files with potentially erroneous data, she runs the following data check algorithm
on each file:

    * for each day count the number of ticks
    * compute the median of all daily tick-counts
    * mark all those days that have a tick-count < 1/2 * median as suspect

    * In addition these descriptive measures are reported for each file:
        
        * minimum and maximum price
        * minimum and maximum tick count per session
        * median of tick count

The python functions analyzeticks() implements the algorithm above. Before we can run it we need some test data, which we create 
by another function, called createsession().

createsessions
^^^^^^^^^^^^^^

For each day were trading is open at the exchange, we define a time interval from 09:00 to 17:30 were transactions occur and 
create randomized values and spaced ticks. The code is straight forard: ::

    def createsessions(filename, numberofsessions):
    
        def writedailyticks(teafile, day, isgoodday):
            ''' create a random series of ticks. if isgoodday is false, only 1% as much ticks will be written. '''
            t = day + Duration(hours=9)         # session begins at 09:00
            end = day + Duration(hours=17.5)    # session ends at 17:30
            while t < end:
                if isgoodday or random.randint(0, 99) < 1:
                    price = random.random() * 100
                    tf.write(t, price, 10)
                t += Duration(seconds = 15 + random.randint(0, 20))

        with TeaFile.create(filename, "Time Price Volume", "qdq") as tf:
            ''' write a file with random tick, similar to ticks as they occur on a stock exchange in reality:
                for <numberofsessions> days we create ticks between 9:00 and 17:30. 10% of the days will 
                create only 1% as much ticks than the other days. This simulates bad data '''
            for day in rangen(DateTime(2000, 1, 1), Duration(days=1), numberofsessions):
                isgoodday = random.randint(1, 100) <= 90
                writedailyticks(tf, day, isgoodday)
        print(tf)


analyzeticks
^^^^^^^^^^^^

To detect days with unexpected low tick count value, we count ticks for each day. To this purpose we define a class
TradingSession and create one for each day. Counting the ticks is straightfoward then: ::


    def analyzeticks(filename, displayvalues=True):
        
        class _TradingSession:        
            def __init__(self, begin):
                self.begin = begin
                self.end = self.begin + Duration(days=1)
                self.tickcount = 0

            def __repr__(self):
                return " ".join([str(self.begin), str(self.end), str(self.tickcount)])

        with TeaFile.openread(filename) as tf:

            if tf.itemcount == 0:
                print("This file holds no items")

            tick = tf.read()
            session = _TradingSession(tick.Time.date)
            minprice = maxprice = tick.Price
            sessions = [session]            
            for tick in tf.items():
                if tick.Time > session.end:
                    session = _TradingSession(tick.Time.date)
                    sessions.append(session)
                session.tickcount += 1
                minprice = min(minprice, tick.Price)
                maxprice = max(maxprice, tick.Price)

            mintransactions = maxtransactions = session.tickcount
            for s in sessions:
                mintransactions = min(mintransactions, s.tickcount)
                maxtransactions = max(maxtransactions, s.tickcount)

            print("min price = {}".format(minprice))
            print("max price = {}".format(maxprice))
            print("min ticks per session = {}".format(mintransactions))
            print("max ticks per session = {}".format(maxtransactions))

            tickcounts = sorted([s.tickcount for s in sessions])
            median = tickcounts[len(tickcounts) // 2]
            print("median = {}".format(median))

            if displayvalues:
                minimumexpectedtickspersession = median / 2.0
                print("First 10 sessions:")
                for s in sessions[:15]:
                    print("{} {}".format(s, "OK" if s.tickcount >= minimumexpectedtickspersession else "QUESTIONABLE"))

download data from Yahoo Finance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Python is particularly well suited to access data like available at Yahoo finance, as changes in such public api 
can be quickly adopted by modifications of the script.::

    from urllib import urlopen    
    def gethistoricalprices(symbol, filename, startyear, startmonth, startday, endyear, endmonth, endday):

        url = "http://ichart.yahoo.com/table.csv?s={0}&a={1:02}&b={2:02}&c={3:04}&d={4:02}&e={5:02}&f={6:04}&g=d&ignore=.csv" \
            .format(symbol, startmonth - 1, startday, startyear, endmonth - 1, endday, endyear)
        response = urlopen(url)        
        
        # values arrive in timely reversed order, so we store them in a list and add them reversed to the file
        values = []
        for line in response:
            line = line.decode("utf8")
            line = line.strip()
            parts = line.split(",")

            t = Time.parse(parts[0], "%Y-%m-%d")
            open_ = float(parts[1])
            high = float(parts[2])
            low = float(parts[3])
            close = float(parts[4])
            volume = int(parts[5])
            adjclose = float(parts[6])

            values.append((t, open_, high, low, close, adjclose, volume))

        # create the file to store the received values
        with TeaFile.create(filename, "Time Open High Low Close AdjClose Volume", "qdddddq", symbol, {"decimals:", 2}) as tf:
            for item in reversed(values):
                tf.write(*item)


.. _struct module:   http://docs.python.org/library/struct.html?highlight=struct#format-characters
.. _generatoriterator:  http://docs.python.org/reference/simple_stmts.html#the-yield-statement