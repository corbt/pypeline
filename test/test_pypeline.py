import os
import tempfile
import shutil

import pytest

from pypeline import DB

@pytest.fixture
def db_dir(request):
    path = tempfile.mkdtemp()

    def finalize():
        shutil.rmtree(path)

    request.addfinalizer(finalize)
    return path

@pytest.fixture
def db(request):
    path = tempfile.mkdtemp()
    db = DB(path, create_if_missing=True)

    def finalize():
        db.close()
        shutil.rmtree(path)

    request.addfinalizer(finalize)
    return db

@pytest.fixture
def collection(request):
    path = tempfile.mkdtemp()
    db = DB(path, create_if_missing=True)

    collection = db.collection('test')

    def finalize():
        db.close()
        shutil.rmtree(path)

    request.addfinalizer(finalize)
    return collection


def test_db_creation(db_dir):
    test_db = DB(db_dir, create_if_missing=True)
    assert os.path.isdir(db_dir) == True
    assert isinstance(test_db, DB) == True

def test_collection_creation(db):
    collection = db.collection(b'test')

    # Collection names cannot contain the reserved '!!' sequence
    with pytest.raises(ValueError):
        db.collection('a !! collection') 
    with pytest.raises(ValueError):
        db.collection('nonexistant-collection', create_if_missing=False)

def test_list_collections(db):
    collections = [b'test', b'test1', b'test2']
    for collection in collections:
        db.collection(collection)

    loaded_collections = db.collections()
    assert str(loaded_collections) == "[pypeline.DB.Collection('test'), pypeline.DB.Collection('test1'), pypeline.DB.Collection('test2')]"
    assert [collection.name for collection in loaded_collections] == collections

def test_collection_put(collection):
    collection.append([1,2])
    collection.append({'a': 'b'})

    assert collection[0] == [1,2]

    assert [c for c in collection] == [[1,2], {'a': 'b'}]


def test_collection_length(db):
    collection = db.collection(b'test')
    collection.append([1,2,3])
    collection.append([4,5,6])

    assert len(collection) == 2

def test_collection_random_access(collection):
    collection.append([1,2])
    collection.append({'a': 'b'})
    collection.append([3,4])

    assert collection[0] == [1,2]
    assert collection[1] == {'a': 'b'}
    assert collection[2] == [3,4]

    with pytest.raises(IndexError):
        assert collection[3] == [3,4]

def test_collection_slicing(collection):
    collection.append([1,2])
    collection.append({'a': 'b'})
    collection.append([3,4])

    assert collection[0:2] == [[1,2],{'a':'b'}]

def test_collection_random_access_assign(collection):
    collection.append([1,2])
    collection.append([3,4])
    collection[1] = [5,6]

    assert collection[1] == [5,6]

    with pytest.raises(IndexError):
        collection[3] = [3,4]

def test_collection_delete(collection):
    collection.append("a")
    collection.append("b")

    collection.delete(0)
    assert len(collection) == 1
    assert collection[0] == "b"

    collection.refresh()
    assert len(collection) == 1
    assert collection[0] == "b"


def test_collection_refresh(db):
    c1 = db.collection('test')
    c2 = db.collection('test')

    c1.append([1,2])

    assert len(c1) == 1
    assert len(c2) == 1
    assert c1[0] == [1,2]
    assert c2[0] == [1,2]

def test_collection_shallow_copying(db):
    c1 = db.collection('test')
    c2 = c1

    c1.append([1,2])

    assert len(c1) == 1
    assert len(c2) == 1
    assert c1[0] == [1,2]
    assert c2[0] == [1,2]

def test_collection_delete(db):
    c1 = db.collection('test')
    c1.append(1)

    db.delete('test')

    with pytest.raises(ValueError):
        c2 = db.collection('test', create_if_missing=False)

    c2 = db.collection('test')
    assert len(c2) == 0


# def test_collection_

def test_database_reloading(db_dir):
    test_db = DB(db_dir, create_if_missing=True)
    c1 = test_db.collection('test')
    c1.append(5)
    c1.append(6)

    c1.delete(0)

    test_db.close()

    test_db2 = DB(db_dir)
    assert test_db2.collection('test')[0] == 6
    assert len(test_db2.collection('test')) == 1