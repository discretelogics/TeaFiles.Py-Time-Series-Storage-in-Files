teafiles.TeaFile in interactive use
===================================

A sample interactive session using TeaFiles api for Python. ::

    >>> from teafiles import *
    >>> with TeaFile.create('acme.tea', 'Time Price Volume', 'qdq', 'acme prices', {'exchange': 'nyse', 'decimals': 2}) as tf:
    ...     for t in range(DateTime(2000), DateTime(2001), Duration(weeks=1)):
    ...         import random
    ...         tf.write(t, random.random() * 100, random.randint(1, 10000))
    ... 
    >>> TeaFile.printsnapshot('acme.tea')
    TeaFile('acme.tea') 53 items

    ItemDescription
    Name:	TPV
    Size:	24
    Fields:
    [Time         Type:  Int64   Offset: 0   IsTime:1   IsEventTime:1,
     Price        Type: Double   Offset: 8   IsTime:0   IsEventTime:0,
     Volume       Type:  Int64   Offset:16   IsTime:0   IsEventTime:0]

    ContentDescription
    acme prices

    NameValues
    {u'decimals': 2, u'exchange': u'nyse'}

    TimeScale
    Epoch:           719162
    Ticks per Day: 86400000
    Wellknown Scale:   Java

    Items
    TPV(Time=2000-01-01 00:00:00:000, Price=37.579128977028674, Volume=8047)
    TPV(Time=2000-01-08 00:00:00:000, Price=10.618929589509186, Volume=232)
    TPV(Time=2000-01-15 00:00:00:000, Price=73.08506970525428, Volume=1711)
    TPV(Time=2000-01-22 00:00:00:000, Price=73.7749103916519, Volume=4397)
    TPV(Time=2000-01-29 00:00:00:000, Price=10.323610234110403, Volume=3376)
    >>> tf = TeaFile.openread('acme.tea')    
    >>> from pprint import pprint
    >>> pprint(list(tf.items(50)))
    [TPV(Time=2000-12-16 00:00:00:000, Price=62.654885677497305, Volume=8097),
     TPV(Time=2000-12-23 00:00:00:000, Price=28.267048873450907, Volume=9226),
     TPV(Time=2000-12-30 00:00:00:000, Price=34.48653142780683, Volume=7790)]
    >>> pprint(list(tf.items(0, 10)))
    [TPV(Time=2000-01-01 00:00:00:000, Price=37.579128977028674, Volume=8047),
     TPV(Time=2000-01-08 00:00:00:000, Price=10.618929589509186, Volume=232),
     TPV(Time=2000-01-15 00:00:00:000, Price=73.08506970525428, Volume=1711),
     TPV(Time=2000-01-22 00:00:00:000, Price=73.7749103916519, Volume=4397),
     TPV(Time=2000-01-29 00:00:00:000, Price=10.323610234110403, Volume=3376),
     TPV(Time=2000-02-05 00:00:00:000, Price=5.253065316994842, Volume=3213),
     TPV(Time=2000-02-12 00:00:00:000, Price=77.30547456663894, Volume=1740),
     TPV(Time=2000-02-19 00:00:00:000, Price=70.41257838854919, Volume=3450),
     TPV(Time=2000-02-26 00:00:00:000, Price=26.454005280919326, Volume=8699),
     TPV(Time=2000-03-04 00:00:00:000, Price=18.6317489603937, Volume=8166)]

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
    BA.day.tea 2 Boeing Co. (The)
    BAC.day.tea 2 Bank of America Corp.
    CAT.day.tea 2 Caterpillar Inc.
    CSCO.day.tea 2 Cisco Systems, Inc.
    CVX.day.tea 2 Chevron Corporation
    DD.day.tea 2 Du Pont (E.I.) de Nemours & Co
    DIS.day.tea 2 WALT DISNEY-DISNEY C
    GE.day.tea 2 General Electric Co
    HD.day.tea 2 HOME DEPOT INC
    HPQ.day.tea 2 Hewlett-Packard Co
    IBM.day.tea 2 International Business Machines Corp.
    INTC.day.tea 2 Intel Corporation
    JNJ.day.tea 2 Johnson & Johnson
    JPM.day.tea 2 JPMorgan Chase & Co.
    KFT.day.tea 2 Kraft Foods, Inc.
    KO.day.tea 2 Coca-Cola Co (The)
    MCD.day.tea 2 McDonald's Corp
    MMM.day.tea 2 3M Co
    MRK.day.tea 2 Merck & Co., Inc
    MSFT.day.tea 2 Microsoft Corporation
    PFE.day.tea 2 PFIZER INC
    PG.day.tea 2 Procter & Gamble Co.
    T.day.tea 2 AT&T Inc
    TRV.day.tea 2 Travelers Companies Inc (The)
    UTX.day.tea 2 United Technologies Corp.
    VZ.day.tea 2 Verizon Communications Inc
    WMT.day.tea 2 Wal-Mart Stores, Inc.
    XOM.day.tea 2 Exxon Mobil Corp.
    >>> 