============
Installation
============

Installing LevelDB
==================

Pypeline DB relies on LevelDB and the Plyvel driver.  Before installing
Pypeline, you should make sure you have LevelDB installed and that the shared
library is available.  On Debian-based Linux distributions like Ubuntu this is
as simple as ``sudo apt-get install libleveldb1 libleveldb-dev``.

Additionally, make sure that your system is capable of installing Python
modules with C extensions.  On Ubuntu this can be accomplished with ``sudo
apt-get install python-dev``.

Further instructions can be found in the `Plyvel docs 
<https://plyvel.readthedocs.org/en/0.7/installation.html>`_.

Installing Pypeline
===================

The simplest way of installing this package is with pip.  Simply run ``pip
install pypeline-db``.

Alternatively, you can download the source and run ``python setup.py install``

Check to make sure the package was properly installed by running ``python -c
'import pypeline'``.  If no output is generated you're good to go.
