import os
import tempfile
import shutil

import pytest

from pypeline import DB, Collection

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
    assert isinstance(collection, Collection) == True

    # Collection names cannot contain the reserved '!!' sequence
    with pytest.raises(ValueError):
        db.collection(b'a !! collection') 

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

    assert [c for c in collection] == [[1,2], {'a': 'b'}]
#     assert collection[0] == {'a': 'b'}

def test_collection_random_access(collection):
    pass

# def test_collection_reloading(db):
#     pass

# def test_collection_length(db):
#     collection = db.collection(b'test')
#     collection.append([1,2,3])
#     collection.append([4,5,6])

    # assert len(collection) == 2