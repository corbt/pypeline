import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

with open(os.path.join(os.path.dirname(__file__), 'pypeline', '_version.py')) as f:
    exec(f.read(), globals(), locals())


long_description = ''
if os.path.exists('README.txt'):
    long_description = open('README.txt').read()

setup(
    name = "pypeline-db",
    version = __version__,
    author = "Kyle Corbitt",
    author_email = "kyle@corbt.com",
    description = "A data processesing and storing helper based on LevelDB",
    license = "MIT",
    keywords = "levelDB big data data science",
    url = "https://github.com/kcorbitt/pypeline",
    packages=['pypeline'],
    long_description=long_description,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Science/Research",
        "Operating System :: POSIX",
        "Topic :: Utilities",
        "Topic :: Database",
        "Topic :: Scientific/Engineering",
    ],
    install_requires=['plyvel']
)
