#  Copyright (c) 2011, DiscreteLogics (copyright@discretelogics.com)
#
#  license: GNU LGPL
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
# pylint: disable-msg=C0301
# C0301: Line too long (104/80) - maybe trim docstrings later for terminal users

'''
The examples below are commented in the package documentation. Here is the focus on the code only,
so docstrings are omitted or kept essential below.
'''


def teadir():
    ''' this utility function lists all tea files in the current directory '''
    import os
    print("{}:".format(os.getcwd()))
    for f in os.listdir('.'):
        if f.endswith(".tea"):
            print (f)


import random
from teafiles import *


def createticks(filename, n, contentdescription=None, namevalues=None):
    '''
    Create a TeaFile holding `n` items of random "Ticks" having fields Time, Price and Volume.
    '''
    with TeaFile.create(filename, "Time Price Volume", "qdq", contentdescription, namevalues) as tf:
        for t in rangen(DateTime(2000, 1, 1), Duration(minutes=1), n):    # increments n times by 1 minute
            r = random.random()
            tf.write(t, r * 100, int(r * 1000))
    print(tf)


def sumprices(filename):
    '''
    Sums all prices in a teafile holding ticks. This function is used forbenchmarking.
    '''
    with TeaFile.openread(filename) as tf:
        return sum(item.Price for item in tf.items())


def createsessions(filename, numberofsessions):

    def writedailyticks(teafile, day, isgoodday):
        '''
        create a random series of ticks. if isgoodday is false, only 1% as much ticks will be written.
        '''
        t = day + Duration(hours=9)         # session begins at 09:00
        end = day + Duration(hours=17.5)    # session ends at 17:30
        while t < end:
            if isgoodday or random.randint(0, 99) < 1:
                price = random.random() * 100
                tf.write(t, price, 10)
            t += Duration(seconds=15 + random.randint(0, 20))

    with TeaFile.create(filename, "Time Price Volume", "qdq") as tf:
        ''' write a file with random tick, similar to ticks as they occur on a stock exchange in reality:
            for <numberofsessions> days we create ticks between 9:00 and 17:30. 10% of the days will
            create only 1% as much ticks than the other days. This simulates bad data
        '''
        for day in rangen(DateTime(2000, 1, 1), Duration(days=1), numberofsessions):
            isgoodday = random.randint(1, 100) <= 90
            writedailyticks(tf, day, isgoodday)
    print(tf)


def analyzeticks(filename, displayvalues=True):
    ''' analyze a teafile holding ticks. print elementary descriptive numbers '''

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


def gethistoricalprices(symbol, filename, startyear, startmonth, startday, endyear, endmonth, endday):
    ''' fetch historical prices from Yahoo finance and store them in a file '''
    from urllib import urlopen

    url = "http://ichart.yahoo.com/table.csv?s={0}&a={1:02}&b={2:02}&c={3:04}&d={4:02}&e={5:02}&f={6:04}&g=d&ignore=.csv" \
        .format(symbol, startmonth - 1, startday, startyear, endmonth - 1, endday, endyear)
    response = urlopen(url)
    if response.code != 200:
        print(response.info())
        raise Exception("download failed. http response code = " + response.code)
    headerline = response.readline().decode("utf8")
    print(headerline)

    # create the file to store the received values
    tf = TeaFile.create(filename, "Time Open High Low Close AdjClose Volume", "qdddddq", symbol)

    # values arrive in timely reversed order, so we store them in a list and ad them reversed to the file
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

    for item in reversed(values):
        tf.write(*item)     # pylint:disable-msg=W0142

if __name__ == '__main__':
    # test zone
    createsessions("lab.tea", 5)
