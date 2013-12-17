===========
Quick Start
===========

The Basics
==========

You only have to understand two concepts to get started with Pypeline DB:
databases and collections.  A *Database* is just a simple wrapper for a
LevelDB database on disk, which is stored as a directory.  A *collection* is a
group of documents in a database that are grouped together and can be worked
with collectively. Ready? Let's get started.

    >>> import pypeline
    >>> db = pypeline.DB("test_database.pypeline", create_if_missing=True)
    >>> collection = db.collection('collection_1')
    >>> collection
    pypeline.DB.Collection('collection_1')

This is pretty straightforward stuff.  By calling pypeline.DB we create a new
database to store our collections in (if you're opening a preexisting database
the ``create_if_missing`` argument is unnecessary).  We then create a new
collection that we can refer to as 'collection_1'.

    >>> db.collection('collection_2')
    pypeline.DB.Collection('collection_2')
    >>> db.collections()
    [u'collection_1', u'collection_2']

The database keeps track of the collections within it.  If you forget what
your collection was called, it's easy to find it again just by calling
``DB.collections()``.

Dealing with Collections
========================

Of course, a collection is no good to us empty, so let's learn how to add something to it.

    >>> for x in range(5):
    ...     collection.append(x)
    ...
    >>> print [record for record in collection]
    [0, 1, 2, 3, 4]
    >>> collection.append_all([{'a': 'b'}, 'string', [1,2]])
    >>> print [record for record in collection]
    [0, 1, 2, 3, 4, {u'a': u'b'}, u'string', [1, 2]]


There are a couple of interesting things to see here.  First of all,
collections implement ``append``.  This works just like appending to a list,
and writes your data straight to the database.  And just like a list in
Python, you can append several types of data.  Dicts, lists, and primitives
like ints and strings all work fine -- anything that is JSON- serializable.
``append_all`` takes anything that is iterable, like a list, range, or even
another collection, and appends every instance within it.  (This is also a
good way of combining multiple collections into a single one).

Secondly, Pypeline collections are `iterable`.  That means all the familiar
syntax like ``for x in collection`` will work just like you would expect.

    >>> collection[0]
    0
    >>> collection.delete(0)
    >>> print collection[0:2]
    [1, 2]
    >>> collection[0] = 5
    >>> print collection[0]
    5

Collections allow for the same familiar slice and indexing format as other
python objects.  This is very memory efficient because only the record(s) you
request will be loaded into memory.  Objects in a collection can also be
deleted by index.

Collections can be copied:

    >>> c3 = db.copy_collection('collection_1', 'collection_3')
    >>> c3[:]
    [5, 2, 3, 4, {u'a': u'b'}, u'string', [1, 2]]
    >>> c3[0] = 1
    >>> print c3[0]
    1
    >>> print collection[0]
    5

Collection copies are "deep" copies, so changing a value in one collection
won't affect it in the one it came from.  There are two separate copies of the
data on disk.

Reloading from Disk
===================

One of the advantages of Pypeline is that you don't have to worry about data loss -- everything you write to it is immediately backed up to disk.  Let's reload our database just to test it out.

    >>> db.close()
    >>> del db, collection, c3
    >>> db = pypeline.DB("test_database.pypeline")
    >>> db.collections()
    [u'collection_1', u'collection_2', u'collection_3']
    >>> print [record for record in db.collection('collection_1')]
    [5, 2, 3, 4, {u'a': u'b'}, u'string', [1, 2]]

As you can see, the database maintains its state with no problems.

Manipulating Data (Higher-order Functions)
==========================================

Transforming data manually with operations such as ``collection[0] =
some_function(collection[0])`` works just fine, but Pypeline provides more
powerful and convenient ways of running operations on your collections.  These
are the operations ``map``, ``filter`` and ``reduce``, as well as the
convenience operation ``random_subset``.  These work the same way as the
built-in Python functions of the same name, except that they operate on a
collection and allow you to set the output either to the same collection or to
a new one.  As always, the memory footprint of these operations is minimal
because not all the data is loaded at once.

    >>> c4 = db.collection('collection_4')
    >>> c4.append_all(range(10))
    >>> def map_add_one(x):
    ...     return x+1
    ... 
    >>> c5 = c4.map(map_add_one, 'collection_5')
    >>> print c5[:]
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    >>> def filter_less_5(x):
    ...     return x < 5
    ... 
    >>> c5.filter(filter_less_5, None)
    pypeline.DB.Collection('collection_5')
    >>> print c5[:]
    [1, 2, 3, 4]
    >>> def reduce_sum(x, y):
    ...     return x+y
    ... 
    >>> c6 = c5.reduce(reduce_sum, 'collection_6')
    >>> c6[:]
    [10]
    >>> c7 = c4.random_subset(5, 'collection_7')
    >>> c7[:]
    [0, 1, 4, 5, 7]

All of these functions take as an argument the name of the function to apply
as well as the name of the collection to write the results to.  The
destination collection *will be overwritten* by these operations, so it's best
to choose a new name and then append it to an existing collection if that's
what you'd like to do.  If the collection given is ``None``(as in the Filter
example) the current collection will be overwritten.

With this introduction you're now ready to get started using Pypeline!  If you
have further questions, be sure to check the :doc:`API` docs or open an issue on the
project `Github <https://github.com/kcorbitt/pypeline>`_.

Importing into Pandas
=====================

`Pandas <http://pandas.pydata.org/>`_ is an invaluable tool for data analysis,
and exporting data from Pypeline to Pandas is easy.  Because Pypeline makes no
assumptions about the format of your data, this requires a bit of manual glue
to get right.  An easy approach that does not require loading all the data into RAM is creating a temporary CSV file to act as a go-between.

    >>> import pandas, os, tempfile, csv
    >>> c8 = db.collection('collection_8')
    >>> csv_file = tempfile.NamedTemporaryFile(delete=False)
    >>> for x in range(5):
    ...     c8.append([x, x+1])
    >>> writer = csv.DictWriter(csv_file, fieldnames=['first', 'second'])
    >>> writer.writeheader()
    >>> for record in c8:
    ...     writer.writerow({'first': record[0], 'second': record[1]})
    >>> csv_file.close()
    >>> csv_path = csv_file.name
    >>> dataframe = pandas.io.parsers.read_csv(csv_path)
    >>> print dataframe
       first  second
    0      0       1
    1      1       2
    2      2       3
    3      3       4
    4      4       5
    >>> os.remove(csv_path)

This snippet creates a temporary file that we'll use to store our data as CSV,
a format that pandas can import from.  We then create our "data," which is
just a silly example in this case, and insert it into the collection.  Using
Python's built-in CSV utilities we then open the file and save our collection
to the CSV file row by row.  Finally, we close the file, import it into
pandas, and delete it.

The dataframe now contains all the data from our collection and is ready for further analysis.

