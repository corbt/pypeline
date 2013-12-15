import json
import copy
import random
from functools import reduce
import plyvel
from ._version import schema_version

class DB:
    """
    The pypeline LevelDB database.  This class contains collections and
    provides some system-level organization.

    All arguments beyond the database path are passed directly to the
    underlying plyvel DB constructor. More details can be found at
    https://plyvel.readthedocs.org/en/latest/api.html#DB 

    Arguments:
    `database_path` -- The path to the folder for database storage
    """

    def __init__(self, database_path, **kwargs):         
        self.db=plyvel.DB(database_path, **kwargs)

        self.collections_set=self.db.prefixed_db(b'collections/')
        self.collection_items_set=self.db.prefixed_db(b'collection-items/')
        self.collections_cache = {}

        try:
            self.schema_version = decode(self.db.get(b'pypeline-schema-version'))
        except:
            self.schema_version = schema_version
            self.db.put(b'pypeline-schema-version', encode(schema_version))

    def collection(self, collection_name, reset_collection=False, 
        create_if_missing=True, error_if_exists=False):
        """
        Returns the collection stored at `collection_name`, or creates it if it doesn't exist.

        | Arguments:
        | ``collection_name`` -- the name of the collection to return

        | Keyword arguments:
        | ``reset_collection`` -- when True any existant data in the collection is deleted before it is returned
        | ``create_if_missing`` -- when False a ValueError is raised if the collection doesn't exist
        | ``error_if_exists`` -- When True a ValueError is raised if the collection already exists 
        """

        if collection_name not in self.collections_cache:
            data = self.collections_set.get(collection_name.encode())
            if data == None:
                if create_if_missing == False:
                    raise ValueError("Collection '{0}' does not exist".format(collection_name))
                self.collections_set.put(collection_name.encode(), b'true')
            self.collections_cache[collection_name] = Collection(self, self.collection_items_set, collection_name)
        elif error_if_exists:
            raise ValueError("Collection '{0}' already exists".format(collection_name))

        if reset_collection:
            self.collections_cache[collection_name].delete_all()

        return self.collections_cache[collection_name]

    def collections(self):
        """
        Returns a list of keys of collections contained in the database.
        """
        
        return [name.decode() for name in self.collections_set.iterator(include_value=False)]

    def copy_collection(self, old_collection, new_collection, start=None, end=None, **kwargs):
        """
        Copies all instances in the old_collection into the new_collection

        | Arguments:
        | ``old_collection`` -- The string name of the old collection
        | ``new_collection`` -- The string name of the new collection

        | Keyword arguments:
        | ``start`` -- (Optional) The index to begin copying from old_collection
        | ``end`` -- (Optional) The index to end copying from old_collection
        | ``create_if_missing`` -- when False a ValueError is raised if the new collection doesn't exist (default: True)
        | ``error_if_exists`` -- When True a ValueError is raised if the collection already exists (default: False)
        """
        old = self.collection(old_collection, create_if_missing=False)
        new = self.collection(new_collection, reset_collection=True, **kwargs)
        new.append_all(old.iterator(start, end))

        return new

    def delete(self, collection_name):
        """
        Deletes a collection.

        | Arguments:
        | ``collection_name`` -- the name of the collection to delete
        """

        self.collection(collection_name).delete_all()
        self.collections_set.delete(collection_name.encode())
        del self.collections_cache[collection_name]

    def close(self):
        """Closes the database."""
        self.db.close()

    def open(self):
        """Opens the database."""
        self.db.open()

class Collection:
    """
    A collection of records stored in a database

    This class should never be instantiated directly.  Use the ``DB.collection()`` method instead
    """
    def __init__(self, database, items_set, name):
        if '!!' in name:
            raise ValueError("Disallowed character sequence '!!' in collection name")

        self.name = name
        self.db = items_set.prefixed_db(name.encode()+b'!!')
        self.parent_db = database

        self.refresh()

    def append(self, record):
        """
        Appends a single record.

        | Arguments:
        | ``record`` -- Any JSON-serializable python object (dicts, lists, ints, strings, etc.)
        """
        self.last_index += 1
        key = str(self.last_index).encode()
        self.db.put(key, encode(record))
        self.keys.append(key)

    def refresh(self):
        """
        Reloads the collection from the database.
        """
        self.keys = []
        for key in self.db.iterator(include_value=False):
            self.keys.append(key)

        if len(self.keys) > 0:
            self.last_index = int(self.keys[-1])
        else:
            self.last_index = 0

    def delete(self, index):
        """
        Deletes an item from the collection.

        | Arguments:
        | ``index`` -- Index of the item to be deleted.
        """
        self.db.delete(self.keys[index])
        self.keys.pop(index)

    def delete_all(self):
        """Deletes all items in the collection"""

        for key in self.keys:
            self.db.delete(key)
        self.keys = []
        self.last_index = 0

    def append_all(self, iterable):
        """Appends every item in the iterable to the collection"""

        for instance in iterable:
            self.append(instance)

    def map(self, function, new_collection, **kwargs):
        """
        Maps a collection to a new collection with a provided function.

        | Arguments:
        | ``function`` -- The function used for mapping.
        | ``new_collection`` -- The name of the collection to insert the new values into.  
            Any existing values will be deleted.
            If ``None``, values are mapped to the same collection.

        | Keyword arguments:
        | ``create_if_missing`` -- when False a ValueError is raised if the new collection doesn't exist
        | ``error_if_exists`` -- When True a ValueError is raised if the new collection already exists 
        """
        collection = None
        if new_collection in [None, self.name]:
            collection = self
            for key in self.keys:
                new_value = function(decode(self.db.get(key)))
                self.db.put(key, encode(new_value))
        else:
            collection = self.parent_db.collection(new_collection, reset_collection=True, **kwargs)
            for instance in self:
                collection.append(function(instance))

        return collection

    def filter(self, function, new_collection, **kwargs):
        """
        Filters a collection into a new collection with a given function.

        | Arguments:
        | ``function`` -- The function used for filtering.
        | ``new_collection`` -- The name of the collection to insert the new values into.  
            Any existing values will be deleted.
            If ``None``, values are filtered in the same collection.

        | Keyword arguments:
        | ``create_if_missing`` -- when False a ValueError is raised if the new collection doesn't exist
        | ``error_if_exists`` -- When True a ValueError is raised if the new collection already exists 
        """
        collection = None
        if new_collection in [None, self.name]:
            collection = self
            new_keys = []
            for key in self.keys:
                if function(decode(self.db.get(key))):
                    new_keys.append(key)
                else:
                    self.db.delete(key)
            self.keys = new_keys

        else:
            collection = self.parent_db.collection(new_collection, reset_collection=True, **kwargs)
            for instance in self:
                if function(instance):
                    collection.append(instance)

        return collection

    def reduce(self, function, new_collection, initializer=None, **kwargs):
        """
        Reduces a collection into a new collection with a given function.

        | Arguments:
        | ``function`` -- The function used for reducing.
        | ``new_collection`` -- The name of the collection to insert the new value into.  
            Any existing values will be deleted.
            If ``None``, the current collection is replaced with the reduction output.

        | Keyword arguments:
        | ``create_if_missing`` -- when False a ValueError is raised if the new collection doesn't exist
        | ``error_if_exists`` -- When True a ValueError is raised if the new collection already exists 
        """
        reduced = None
        if initializer != None:
            reduced = reduce(function, self.iterator(), initializer)
        else:
            reduced = reduce(function, self.iterator())

        collection = None
        if new_collection in [None, self.name]:
            collection = self
        else:
            collection = self.parent_db.collection(new_collection, reset_collection=True, **kwargs)
        
        collection.append(reduced)
        return collection

    def random_subset(self, number, new_collection, **kwargs):
        """
        Produces a random subset of a given collection and inserts it into a new collection.

        | Arguments:
        | ``new_collection`` -- The name of the collection to insert the new values into.  
            Any existing values will be deleted.
            If `None`, the subset is stored to the current collection.

        | Keyword arguments:
        | ``create_if_missing`` -- when False a ValueError is raised if the new collection doesn't exist
        | ``error_if_exists`` -- When True a ValueError is raised if the new collection already exists 
        """
        collection = None
        if new_collection in [None, self.name]:
            collection = self
            random.shuffle(self.keys)
            for key in self.keys[number:]:
                self.db.delete(key)
            self.keys = self.keys[:number]
            list.sort(self.keys)

        else:
            new_keys = copy.copy(self.keys)
            random.shuffle(new_keys)
            new_keys = new_keys[:number]
            list.sort(new_keys)
            collection = self.parent_db.collection(new_collection, **kwargs)
            collection.delete_all()
            for key in new_keys:
                collection.append(decode(self.db.get(key)))

        return collection


    def iterator(self, start=None, end=None):
        """Returns a collection iterator"""

        return Iterator(self, start, end)

    def __iter__(self):
        return self.iterator()

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [decode(self.db.get(key)) for key in self.keys[key]]
        else:
            return decode(self.db.get(self.keys[key]))

    def __setitem__(self, key, value):
        self.db.put(self.keys[key], encode(value))

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.name)

    def __len__(self):
        return len(self.keys)

class Iterator:
    def __init__(self, collection, start=None, end=None):
        self.key_iterator = iter(collection.keys[start:end])
        self.collection = collection

    def __iter__(self):
        return self

    def next(self):
        return decode(self.collection.db.get(self.key_iterator.next()))

    def __next__(self):
        return decode(self.collection.db.get(self.key_iterator.__next__()))

def encode(obj):
    return json.dumps(obj).encode()

def decode(string):
    return json.loads(string.decode())
