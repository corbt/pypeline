===========
Pypeline DB
===========

Pypeline DB is designed to simplify the creation and management of datasets.
It has a friendly and easy-to-master API backed by the power of `LevelDB
<https://code.google.com/p/leveldb/>`_.  This allows it to manage datasets too
large to fit in RAM without sacrificing data access performance.

Pypeline is great for:
 * Exploring data without eating all your RAM
 * Transforming data with maps, filters and reductions
 * Stopping you from losing or overwriting your data (unless you explicitly ask it to)

It's also easy to export a dataset from Pypeline to Pandas for further
analysis.

Contents
========

.. toctree::
   :maxdepth: 2

   install
   intro
   API

Links
=====
* `Source <https://github.com/kcorbitt/pypeline>`_
* `PyPi Package <https://pypi.python.org/pypi/pypeline-db/>`_
* `Docs <http://pypeline.readthedocs.org/en/latest/>`_
* `Blog Post <http://corbt.com/blog/introducing-pypeline-db.html>`_